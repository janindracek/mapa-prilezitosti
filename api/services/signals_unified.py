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
        # Paths to comprehensive data - ONLY these are permitted
        self.comprehensive_signals_path = settings.SIGNALS_COMPREHENSIVE_PATH
        self.comprehensive_metrics_path = settings.METRICS_ALL_PEERS_PATH
        
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
        
        # Map new method names to data method names for backward compatibility
        method_mapping = {
            'trade_structure': 'kmeans_cosine_hs2_shares',  # New name -> Data name
            'kmeans_cosine_hs2_shares': 'kmeans_cosine_hs2_shares',  # Legacy support
            'human': 'human',
            'opportunity': 'opportunity',
            'default': 'default'
        }
        
        # Also map for peer group registry lookup (use UI method name)
        ui_method = method  # Keep original method name for peer group registry
        
        # Use mapped method name for data filtering
        data_method = method_mapping.get(method, method)
        
        # Filter signals
        filtered = signals_df.copy()
        
        # CRITICAL: Filter by country (partner_iso3) - signals FOR this country
        if 'partner_iso3' in filtered.columns:
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
            'kmeans_cosine_hs2_shares': 'trade_structure',
            'human': 'human',
            'opportunity': 'opportunity',
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
            
            # Get the strongest signal for this methodology
            strongest_signal = method_signals.iloc[0].to_dict()
            
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
    
