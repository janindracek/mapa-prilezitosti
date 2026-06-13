"""
Unified Bars Service - Consolidates all bar chart data queries

This service replaces duplicate logic from /products and /bars_v2 endpoints
with a single, clean interface for all bar chart types.

Supported modes:
- products: Top HS6 products by export value
- partners: Top countries by export/import value for specific HS6  
- peer_compare: Partner bars filtered by peer group methodology
"""

import pandas as pd
import pycountry
from typing import List, Dict, Any, Optional, Set

from api.data_access import query_core, core_max_year, metrics_mtime_key, top_products
from api.data.loaders import load_hs6_names, resolve_peers
from api.normalizers import normalize_iso, norm_hs2
from api.formatting import fmt_value, to_json_safe


class BarsService:
    """Unified service for all bar chart data"""
    
    def __init__(self):
        self._hs6_names_cache = None
    
    def _get_hs6_names(self) -> Dict[str, str]:
        """Get HS6 names with caching"""
        if self._hs6_names_cache is None:
            self._hs6_names_cache = load_hs6_names()
        return self._hs6_names_cache
    
    def _enrich_country_names(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add country names using pycountry lookup"""
        for record in records:
            if 'id' in record and len(str(record['id'])) == 3:
                try:
                    country = pycountry.countries.get(alpha_3=str(record['id']))
                    if country:
                        record['name'] = country.name
                    else:
                        record['name'] = str(record['id'])
                except Exception:
                    record['name'] = str(record['id'])
        return records
    
    def _format_values(self, records: List[Dict[str, Any]], value_type: str = "export") -> List[Dict[str, Any]]:
        """Add value formatting to records"""
        for record in records:
            if 'value' in record:
                record['value_fmt'], record['unit'] = fmt_value(record['value'], value_type)
                record['value'] = to_json_safe(record['value'])
        return records
    
    def get_product_bars(
        self,
        year: Optional[int] = None,
        top: int = 10,
        country: Optional[str] = None,
        hs2: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get top HS6 products by export value.
        
        Args:
            year: Target year (defaults to latest)
            top: Number of top products to return
            country: Filter to specific country
            hs2: Filter to specific HS2 chapter
            
        Returns:
            List of {id: hs6, name, value, value_fmt, unit}
        """
        # Default to latest year. The groupby/top-N runs inside DuckDB so the
        # request never materializes a year slice (~894k rows) into pandas —
        # concurrent slices were what OOMed the 512 MB tier.
        year = year or core_max_year(metrics_mtime_key())
        if year is None:
            return []
        iso3 = None
        if country:
            iso3 = normalize_iso(country)
            if not iso3:
                return []
        hs2_normalized = norm_hs2(hs2) if hs2 else None
        product_totals = top_products(
            year=int(year), partner_iso3=iso3, hs2=hs2_normalized, top=top
        )
        if product_totals.empty:
            return []

        product_totals["id"] = product_totals["hs6"].astype(str)
        product_totals = product_totals[["id", "value"]]
        
        # Add product names
        hs6_names = self._get_hs6_names()
        product_totals["name"] = product_totals["id"].map(lambda x: hs6_names.get(x, x))
        
        records = product_totals.to_dict(orient="records")
        return self._format_values(records, "export")
    
    def get_partner_bars(
        self,
        hs6: str,
        year: int,
        mode: str = "peer_compare",
        country: Optional[str] = None,
        peer_group: Optional[str] = None,
        top: int = 10,
        value_type: str = "export"
    ) -> List[Dict[str, Any]]:
        """
        Get top partner countries for specific HS6.
        
        Args:
            hs6: Product code
            year: Target year
            mode: Display mode (peer_compare, yoy_growth, import_change)
            country: Ensure this country is included in results
            peer_group: Filter to specific peer group
            top: Number of top partners to return
            value_type: export or import values
            
        Returns:
            List of {id: iso3, name, value, value_fmt, unit}
        """
        # Normalize HS6 and read only this product's rows (all years) from the
        # parquet — small slice, keeps the existing year-filter + fallback logic.
        # podil_cz_na_importu rides along so every partner bar can expose the CZ
        # market share for that (hs6, year, partner).
        hs6_padded = str(hs6).zfill(6)
        df = query_core(
            ["year", "partner_iso3", "hs6", "export_cz_to_partner", "podil_cz_na_importu"],
            hs6=hs6_padded,
        )
        if df.empty:
            return []

        # Filter data
        filtered_data = df[
            (df["hs6"].astype(str).str.zfill(6) == hs6_padded) &
            (df["year"] == year)
        ].copy()
        
        if filtered_data.empty:
            # Fallback to latest available year for this HS6
            hs6_data = df[df["hs6"].astype(str).str.zfill(6) == hs6_padded].copy()
            if hs6_data.empty:
                return []
            fallback_year = int(hs6_data["year"].max())
            filtered_data = hs6_data[hs6_data["year"] == fallback_year].copy()
        
        # Determine value column
        if value_type == "export" or mode == "peer_compare":
            value_columns = ["export_cz_to_partner", "cz_curr", "cz_exports_usd", "exports_usd"]
        else:
            value_columns = ["imp_total", "import_total", "partner_import_total", "imports_usd", "import_usd"]
            # Fallback to export columns if import not available
            value_columns.extend(["export_cz_to_partner", "cz_curr", "cz_exports_usd", "exports_usd"])
        
        value_col = None
        for col in value_columns:
            if col in filtered_data.columns:
                value_col = col
                break
        
        if value_col is None:
            return []
        
        # Keep the pre-peer-filter frame: the selected country is not part of
        # its own peer group, so its REAL row must come from here (it used to be
        # re-appended with a hardcoded 0.0 — wrong whenever CZ actually exports
        # there, e.g. DEU/930400/2023 is 19.6M USD, not 0).
        base_data = filtered_data

        # Apply peer group filtering
        if mode == "peer_compare" and country and peer_group:
            iso3 = normalize_iso(country)
            if iso3:
                peer_countries = resolve_peers(iso3, year, peer_group)
                if peer_countries:
                    filtered_data = filtered_data[
                        filtered_data["partner_iso3"].isin(peer_countries)
                    ]

        # Aggregate by partner. One core_trade row exists per (year, hs6,
        # partner), so "max" just carries the stored share alongside the value.
        agg_spec = {value_col: "sum"}
        has_share = "podil_cz_na_importu" in filtered_data.columns
        if has_share:
            agg_spec["podil_cz_na_importu"] = "max"
        partner_totals = (
            filtered_data.groupby("partner_iso3", as_index=False)
            .agg(agg_spec)
            .rename(columns={value_col: "value", "podil_cz_na_importu": "share"})
        )

        # Ensure selected country is included — with its REAL value/share from
        # the pre-filter frame (0 only if it genuinely has no row).
        if country:
            iso3 = normalize_iso(country)
            if iso3 and partner_totals[partner_totals["partner_iso3"] == iso3].empty:
                own = base_data[base_data["partner_iso3"] == iso3]
                own_value = float(own[value_col].sum()) if not own.empty else 0.0
                own_share = None
                if has_share and not own.empty:
                    own_share = own["podil_cz_na_importu"].max()
                extra = {"partner_iso3": [iso3], "value": [own_value]}
                if has_share:
                    extra["share"] = [own_share]
                partner_totals = pd.concat([
                    partner_totals,
                    pd.DataFrame(extra)
                ], ignore_index=True)
        
        # Sort and limit
        partner_totals = partner_totals.sort_values(["value", "partner_iso3"], ascending=[False, True])
        
        if top > 0:
            top_partners = partner_totals.head(top)
            
            # Ensure selected country is in top results
            if country:
                iso3 = normalize_iso(country)
                if iso3 and top_partners[top_partners["partner_iso3"] == iso3].empty:
                    selected_country = partner_totals[partner_totals["partner_iso3"] == iso3]
                    if not selected_country.empty:
                        top_partners = pd.concat([top_partners, selected_country], ignore_index=True)
                        top_partners = top_partners.drop_duplicates(subset=["partner_iso3"])
                        top_partners = top_partners.sort_values(["value", "partner_iso3"], ascending=[False, True])
            
            partner_totals = top_partners
        
        # Format results
        partner_totals["id"] = partner_totals["partner_iso3"]
        out_cols = ["id", "value"] + (["share"] if has_share else [])
        records = partner_totals[out_cols].to_dict(orient="records")
        for record in records:
            # CZ share of the partner's imports for this (hs6, year) — float or null.
            record["share"] = to_json_safe(record.get("share"))

        # Add country names and format values
        records = self._enrich_country_names(records)
        return self._format_values(records, "USD")
    
    def get_bars(
        self,
        mode: str = "products",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Unified bar data endpoint.
        
        Args:
            mode: Type of bars (products, partners, peer_compare)
            **kwargs: Mode-specific parameters
            
        Returns:
            List of bar data records
        """
        if mode == "products":
            return self.get_product_bars(
                year=kwargs.get('year'),
                top=kwargs.get('top', 10),
                country=kwargs.get('country'),
                hs2=kwargs.get('hs2')
            )
        
        elif mode in ("partners", "peer_compare"):
            return self.get_partner_bars(
                hs6=kwargs.get('hs6'),
                year=kwargs.get('year'),
                mode=mode,
                country=kwargs.get('country'),
                peer_group=kwargs.get('peer_group'),
                top=kwargs.get('top', 10),
                value_type=kwargs.get('value_type', 'export')
            )
        
        else:
            raise ValueError(f"Unsupported bar mode: {mode}")