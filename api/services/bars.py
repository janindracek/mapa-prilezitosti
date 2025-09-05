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

from api.data_access import get_metrics_cached, metrics_mtime_key
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
        df = get_metrics_cached(metrics_mtime_key())
        if df.empty:
            return []
        
        # Default to latest year
        year = year or int(df["year"].max())
        current_data = df[df["year"] == year].copy()
        
        # Apply country filter
        if country:
            iso3 = normalize_iso(country)
            if not iso3:
                return []
            current_data = current_data[current_data["partner_iso3"] == iso3]
        
        # Apply HS2 filter
        if hs2:
            hs2_normalized = norm_hs2(hs2)
            if hs2_normalized:
                current_data = current_data[
                    current_data["hs6"].astype(str).str.zfill(6).str[:2] == hs2_normalized
                ]
        
        if current_data.empty:
            return []
        
        # Aggregate by HS6 and get top products
        product_totals = (
            current_data.groupby("hs6")["export_cz_to_partner"]
            .sum()
            .nlargest(max(int(top), 1))
            .reset_index()
        )
        
        # Format results
        product_totals["id"] = product_totals["hs6"].astype(str).str.zfill(6)
        product_totals = product_totals.rename(columns={"export_cz_to_partner": "value"})[["id", "value"]]
        
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
        df = get_metrics_cached(metrics_mtime_key())
        if df.empty:
            return []
        
        # Normalize HS6
        hs6_padded = str(hs6).zfill(6)
        
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
        
        # Apply peer group filtering
        if mode == "peer_compare" and country and peer_group:
            iso3 = normalize_iso(country)
            if iso3:
                peer_countries = resolve_peers(iso3, year, peer_group)
                if peer_countries:
                    filtered_data = filtered_data[
                        filtered_data["partner_iso3"].isin(peer_countries)
                    ]
        
        # Aggregate by partner
        partner_totals = (
            filtered_data.groupby("partner_iso3", as_index=False)
            .agg({value_col: "sum"})
            .rename(columns={value_col: "value"})
        )
        
        # Ensure selected country is included
        if country:
            iso3 = normalize_iso(country)
            if iso3 and partner_totals[partner_totals["partner_iso3"] == iso3].empty:
                partner_totals = pd.concat([
                    partner_totals, 
                    pd.DataFrame({"partner_iso3": [iso3], "value": [0.0]})
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
        records = partner_totals[["id", "value"]].to_dict(orient="records")
        
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