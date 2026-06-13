"""
Unified Signals Service - ETL-First Architecture

This service replaces the complex signal computation logic with simple data serving
from comprehensive pre-computed signals. All signal generation happens in ETL.

Architecture Benefits:
- Consistent results across all users
- Excellent performance (pure data filtering)
- Simple, maintainable code
- Complete peer group methodology support
"""

import os
import json
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path

from api.settings import settings
from api.normalizers import normalize_iso
from api.formatting import to_json_safe, fmt_value
from api.peer_group_registry import PeerGroupRegistry, get_peer_explanation_for_signal


class UnifiedSignalsService:
    """Unified service for serving pre-computed signals from comprehensive ETL"""
    
    def __init__(self):
        # M4b: read the single serving layer.
        self.comprehensive_signals_path = settings.SIGNALS_PATH
        self.comprehensive_metrics_path = settings.METRICS_PARQUET_PATH
        
        # Cache for loaded data
        self._signals_cache = None
        self._metrics_cache = None
    
    def _load_signals(self) -> pd.DataFrame:
        """Load comprehensive signals - NO FALLBACKS PERMITTED"""
        if self._signals_cache is not None:
            return self._signals_cache
        
        if not os.path.isfile(self.comprehensive_signals_path):
            raise FileNotFoundError(f"Required file missing: {self.comprehensive_signals_path}. Run ETL pipeline: python etl/06b_generate_comprehensive_signals.py")
        
        self._signals_cache = pd.read_parquet(self.comprehensive_signals_path)
        print(f"Loaded comprehensive signals: {len(self._signals_cache)} signals")
        return self._signals_cache
    
    def _load_metrics(self) -> pd.DataFrame:
        """Load comprehensive metrics - NO FALLBACKS PERMITTED"""
        if self._metrics_cache is not None:
            return self._metrics_cache
        
        if not os.path.isfile(self.comprehensive_metrics_path):
            raise FileNotFoundError(f"Required file missing: {self.comprehensive_metrics_path}. Run ETL pipeline: python etl/04b_enrich_metrics_with_all_peers.py")
        
        self._metrics_cache = pd.read_parquet(self.comprehensive_metrics_path)
        print(f"Loaded comprehensive metrics: {len(self._metrics_cache)} rows")
        return self._metrics_cache
    
    def get_signals_by_methodology(
        self, 
        country: str = "CZE", 
        method: str = "geographic", 
        hs6: Optional[str] = None,
        signal_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get signals for a specific peer group methodology.
        
        Args:
            country: Target country (ISO3)
            method: Peer group methodology
            hs6: Filter by specific product
            signal_type: Filter by signal type
            limit: Maximum number of signals
        
        Returns:
            List of signal dictionaries with complete information
        """
        iso3 = normalize_iso(country)
        if not iso3:
            return []
        
        signals_df = self._load_signals()
        if signals_df.empty:
            return []
        
        # M3/M4b: signals.parquet carries method ids verbatim. Keep legacy alias.
        method_mapping = {
            'trade_structure': 'trade_structure',
            'kmeans_cosine_hs2_shares': 'trade_structure',  # legacy alias
            'human': 'human',
            'yoy_export': 'yoy_export',
            'yoy_share': 'yoy_share',
        }
        
        # Also map for peer group registry lookup (use UI method name)
        ui_method = method  # Keep original method name for peer group registry
        
        # Use mapped method name for data filtering
        data_method = method_mapping.get(method, method)
        
        # Filter signals
        filtered = signals_df.copy()
        
        # CRITICAL: Filter by country logic
        # If country='CZE', return signals for ALL partners (Czech export opportunities)  
        # If country is a specific partner, filter for that partner only
        if 'partner_iso3' in filtered.columns and iso3 != 'CZE':
            filtered = filtered[filtered['partner_iso3'] == iso3]
        
        # Filter by methodology
        if 'method' in filtered.columns:
            filtered = filtered[filtered['method'] == data_method]
        
        # Filter by product
        if hs6:
            hs6_padded = str(hs6).zfill(6)
            filtered = filtered[filtered['hs6'] == hs6_padded]
        
        # Filter by signal type
        if signal_type:
            filtered = filtered[filtered['type'] == signal_type]
        
        # Sort by intensity and limit
        if 'intensity' in filtered.columns:
            filtered = filtered.sort_values('intensity', ascending=False)
        
        filtered = filtered.head(limit)
        
        # Convert to enriched dictionaries
        signals = []
        for _, row in filtered.iterrows():
            signal = row.to_dict()
            
            # Enrich with peer group explanation
            if signal.get('method'):
                try:
                    # Use UI method name for peer group registry lookup
                    signal_ui_method = ui_method if signal['method'] == data_method else signal['method']
                    explanation = PeerGroupRegistry.get_human_readable_explanation(
                        iso3, signal_ui_method, signal.get('year', 2023)
                    )
                    signal['methodology'] = explanation
                except Exception:
                    pass
            
            # Add missing frontend fields for display
            # TODO: Load from reference data files for proper names
            signal['hs6_name'] = f"HS6 {signal.get('hs6', '')}"  # Placeholder
            signal['partner_name'] = signal.get('partner_iso3', '')  # Use ISO3 as fallback

            # M7: the ETL stores YoY as a RATIO (delta/prev; etl/02), so the
            # raw `yoy` field was 100× smaller than every percent surface
            # (value_fmt below ×100s it; /insights_data speaks percent).
            # Serve `yoy` in PERCENT too so all magnitudes agree.
            if str(signal.get('type', '')).startswith('YoY'):
                try:
                    if signal.get('yoy') is not None and not pd.isna(signal['yoy']):
                        signal['yoy'] = float(signal['yoy']) * 100.0
                except (TypeError, ValueError):
                    pass

            # Format values
            signal['value_fmt'], signal['unit'] = fmt_value(
                float(signal.get('intensity', 0.0)),
                signal.get('type', '')
            )
            
            # Ensure JSON-safe
            signal = {k: to_json_safe(v) for k, v in signal.items()}
            signals.append(signal)
        
        return signals
    
    def get_peer_countries_for_chart(
        self, 
        country: str = "CZE", 
        method: str = "geographic", 
        hs6: Optional[str] = None
    ) -> List[str]:
        """
        Get peer countries for bar chart display.
        
        Args:
            country: Target country
            method: Peer group methodology
            hs6: Product filter
            
        Returns:
            List of peer country ISO3 codes
        """
        # Use peer group registry for consistent results
        return PeerGroupRegistry.get_peer_countries_for_charts(country, method, 2023)
    
    def get_all_available_methodologies(self) -> List[Dict[str, Any]]:
        """Get all available peer group methodologies"""
        signals_df = self._load_signals()
        
        if 'method' not in signals_df.columns:
            return [{'method': 'default', 'name': 'Default', 'signal_count': len(signals_df)}]
        
        # Reverse mapping from data method to UI method names
        data_to_ui_method = {
            'trade_structure': 'trade_structure',
            'kmeans_cosine_hs2_shares': 'trade_structure',  # legacy alias
            'human': 'human',
            'yoy_export': 'yoy_export',
            'yoy_share': 'yoy_share'
        }
        
        methodologies = []
        for data_method in signals_df['method'].unique():
            if pd.isna(data_method):
                continue
                
            method_signals = signals_df[signals_df['method'] == data_method]
            
            # Get UI method name
            ui_method = data_to_ui_method.get(data_method, data_method)
            methodology_info = PeerGroupRegistry.get_methodology_config(ui_method)
            
            methodologies.append({
                'method': ui_method,  # Use UI method name
                'name': methodology_info.get('name', ui_method.title()),
                'description': methodology_info.get('description', ''),
                'signal_count': len(method_signals),
                'signal_types': method_signals['type'].unique().tolist()
            })
        
        return methodologies
    
    def get_signals_for_country_product(
        self, 
        country: str, 
        hs6: str, 
        include_all_methodologies: bool = False
    ) -> Dict[str, Any]:
        """
        Get comprehensive signal data for a specific country-product combination.
        
        Returns data needed for insights, charts, and explanations.
        """
        iso3 = normalize_iso(country)
        if not iso3:
            return {"error": "Invalid country code"}
        
        hs6_padded = str(hs6).zfill(6)
        signals_df = self._load_signals()
        
        if signals_df.empty:
            return {"error": "No signals data available"}
        
        # Get all signals for this country-product
        product_signals = signals_df[
            (signals_df['hs6'] == hs6_padded)
        ]
        
        if product_signals.empty:
            return {"error": f"No signals found for product {hs6}"}
        
        result = {
            'country': iso3,
            'hs6': hs6_padded,
            'methodologies': {}
        }
        
        # Group by methodology
        for method in product_signals['method'].unique():
            if pd.isna(method):
                method = 'default'
                
            method_signals = product_signals[product_signals['method'] == method]
            
            if method_signals.empty:
                continue
            
            # Get the strongest signal for this methodology (NaN-safe for JSON)
            strongest_signal = {k: to_json_safe(v) for k, v in method_signals.iloc[0].to_dict().items()}

            # Get peer countries and explanation
            peer_explanation = PeerGroupRegistry.get_human_readable_explanation(
                iso3, method, strongest_signal.get('year', 2023)
            )

            result['methodologies'][method] = {
                'signal': strongest_signal,
                'peer_countries': peer_explanation['peer_countries'],
                'explanation': peer_explanation['explanation_text'],
                'methodology_name': peer_explanation['methodology_name']
            }

        return result

    # --- M5: two-tier selection (strong first, backfill weak) ---------------
    LIVE_METHODS = ["human", "trade_structure", "yoy_export", "yoy_share"]

    def select_two_tier(self, country: str, strong_cap: int = 10, min_strong: int = 5) -> List[Dict[str, Any]]:
        """Surface up to `strong_cap` STRONG signals for a country, balanced
        across the 4 live methods; if fewer than `min_strong` strong exist,
        backfill (flagged) with WEAK band up to the cap. Selection happens at
        request time — the ETL serves the full banded set."""
        pools = {
            m: self.get_signals_by_methodology(country=country, method=m, limit=strong_cap * 3)
            for m in self.LIVE_METHODS
        }
        strong = {m: [s for s in pools[m] if str(s.get("band", "strong")) == "strong"] for m in self.LIVE_METHODS}
        weak = {m: [s for s in pools[m] if str(s.get("band")) == "weak"] for m in self.LIVE_METHODS}
        seen = set()

        def key(s):
            return (s.get("partner_iso3"), s.get("hs6"), s.get("type"))

        def round_robin(pmap, cap):
            out, ptr = [], {m: 0 for m in self.LIVE_METHODS}
            progressed = True
            while len(out) < cap and progressed:
                progressed = False
                for m in self.LIVE_METHODS:
                    lst = pmap[m]
                    while ptr[m] < len(lst):
                        s = lst[ptr[m]]; ptr[m] += 1
                        if key(s) not in seen:
                            seen.add(key(s)); out.append(s); progressed = True
                            break
                    if len(out) >= cap:
                        break
            return out

        selected = round_robin(strong, strong_cap)
        if len(selected) < min_strong:
            selected += round_robin(weak, strong_cap - len(selected))
        return selected[:strong_cap]

    # --- M5: lean serving for the analytics side-tab (full set, no per-row
    # peer-explanation enrichment — too slow at ~108k rows) -----------------
    def get_all_signals(self, country: Optional[str] = None, method: Optional[str] = None,
                        signal_type: Optional[str] = None, band: Optional[str] = None,
                        hs6: Optional[str] = None, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        df = self._load_signals()
        # Drop BACI pseudo-aggregates (e.g. partner 'S19' = "Other Asia, nes") —
        # they are not countries and must not surface in the analytics tab.
        from api.data.loaders import load_real_country_iso3
        real_iso3 = load_real_country_iso3()
        if real_iso3 and "partner_iso3" in df.columns:
            df = df[df["partner_iso3"].isin(real_iso3)]
        if country:
            iso = normalize_iso(country)
            if iso and iso != "CZE":
                df = df[df["partner_iso3"] == iso]
        if method:
            df = df[df["method"] == method]
        if signal_type:
            df = df[df["type"] == signal_type]
        if band:
            df = df[df["band"] == band]
        if hs6:
            df = df[df["hs6"] == str(hs6).zfill(6)]
        if "intensity" in df.columns:
            df = df.sort_values("intensity", ascending=False)
        total = int(len(df))
        page = max(1, int(page)); page_size = max(1, min(int(page_size), 500))
        rows = df.iloc[(page - 1) * page_size: (page - 1) * page_size + page_size]
        cols = ["type", "method", "band", "year", "hs6", "partner_iso3", "intensity",
                "value", "peer_median", "delta_vs_peer", "rel_gap", "peer_count"]
        recs = [{c: to_json_safe(r.get(c)) for c in cols if c in df.columns} for _, r in rows.iterrows()]
        return {"total": total, "page": page, "page_size": page_size, "rows": recs}

