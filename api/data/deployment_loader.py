"""
Unified data access for deployment-optimized dataset

Single source of truth for all API endpoints using the deployment dataset.
This ensures consistency across all API responses and simplifies data access.
"""

import os
import pandas as pd
from typing import Dict, List, Optional, Any
from functools import lru_cache


class DeploymentDataLoader:
    """Unified data access for deployment-optimized dataset"""
    
    def __init__(self):
        self.base_path = "data/deployment"
        self._core_trade = None
        self._signals = None 
        self._peers = None
        self._metadata = None
        
    @property
    def core_trade(self) -> pd.DataFrame:
        """Full global trade data for map and trade endpoints"""
        if self._core_trade is None:
            path = f"{self.base_path}/core_trade.parquet"
            if os.path.exists(path):
                self._core_trade = pd.read_parquet(path)
                print(f"Loaded core trade data: {len(self._core_trade):,} rows")
            else:
                print(f"Warning: {path} not found")
                self._core_trade = pd.DataFrame()
        return self._core_trade
        
    @property  
    def signals(self) -> pd.DataFrame:
        """Filtered signals data for signals endpoints"""
        if self._signals is None:
            path = f"{self.base_path}/signals_filtered.parquet"
            if os.path.exists(path):
                self._signals = pd.read_parquet(path)
                print(f"Loaded signals data: {len(self._signals):,} rows")
            else:
                print(f"Warning: {path} not found")
                self._signals = pd.DataFrame()
        return self._signals
        
    @property
    def peers(self) -> pd.DataFrame:
        """Peer relationships for all methodologies"""
        if self._peers is None:
            path = f"{self.base_path}/peer_relationships.parquet"
            if os.path.exists(path):
                self._peers = pd.read_parquet(path)
                print(f"Loaded peer relationships: {len(self._peers):,} rows")
            else:
                print(f"Warning: {path} not found")
                self._peers = pd.DataFrame()
        return self._peers
        
    @property
    def metadata(self) -> Dict[str, Any]:
        """Reference data: countries, HS6 names, configurations"""
        if self._metadata is None:
            path = f"{self.base_path}/metadata.parquet"
            if os.path.exists(path):
                meta_df = pd.read_parquet(path)
                self._metadata = meta_df.iloc[0].to_dict() if len(meta_df) > 0 else {}
                print("Loaded metadata")
            else:
                print(f"Warning: {path} not found")
                self._metadata = {'countries': [], 'hs6_names': {}, 'config': {}}
        return self._metadata
    
    @lru_cache(maxsize=100)
    def get_country_names(self) -> pd.DataFrame:
        """Get country ISO3 to name mapping"""
        countries_data = self.metadata.get('countries', [])
        if len(countries_data) > 0:
            return pd.DataFrame(countries_data)
        else:
            # Fallback to basic ISO3 codes
            return pd.DataFrame({'iso3': [], 'name': []})
    
    def get_map_data(self, hs6: str = None, metric: str = 'export_cz_to_partner', year: int = 2023) -> List[Dict]:
        """
        Global map data with full coverage
        
        Args:
            hs6: Filter by specific HS6 code
            metric: Metric to display (export_cz_to_partner, podil_cz_na_importu, etc.)
            year: Year filter (only 2023 available in deployment data)
        
        Returns:
            List of {iso3, name, value, value_fmt, unit} for map display
        """
        df = self.core_trade.copy()
        
        # Apply filters
        if hs6:
            df = df[df['hs6'] == hs6]
            
        if len(df) == 0:
            return []
            
        # Aggregate by country for map display
        if metric in df.columns:
            map_data = df.groupby('partner_iso3')[metric].sum().reset_index()
        else:
            print(f"Warning: metric '{metric}' not found, using export_cz_to_partner")
            map_data = df.groupby('partner_iso3')['export_cz_to_partner'].sum().reset_index()
            metric = 'export_cz_to_partner'
        
        # Add country names (with fallback to ISO3)
        countries = self.get_country_names()
        if not countries.empty and 'iso3' in countries.columns:
            map_data = map_data.merge(
                countries[['iso3', 'name']], 
                left_on='partner_iso3', 
                right_on='iso3', 
                how='left'
            )
        else:
            # Fallback: use ISO3 as name and add basic pycountry lookup
            map_data['name'] = map_data['partner_iso3']
        
        # Format for map display
        results = []
        for _, row in map_data.iterrows():
            value = row[metric]
            
            # Format value for display
            if value >= 1_000_000_000:
                value_fmt = f"{value/1_000_000_000:.1f}B"
                unit = "USD" if "export" in metric or "import" in metric else ""
            elif value >= 1_000_000:
                value_fmt = f"{value/1_000_000:.1f}M"
                unit = "USD" if "export" in metric or "import" in metric else ""
            elif "podil" in metric or "share" in metric:
                value_fmt = f"{value:.2%}"
                unit = ""
            else:
                value_fmt = f"{value:,.0f}"
                unit = "USD" if "export" in metric or "import" in metric else ""
            
            results.append({
                'iso3': row['partner_iso3'],
                'name': row.get('name', row['partner_iso3']),
                'value': float(value) if pd.notnull(value) else 0,
                'value_fmt': value_fmt,
                'unit': unit
            })
        
        # Sort by value descending
        results.sort(key=lambda x: x['value'], reverse=True)
        return results
        
    def get_signals_data(self, country: str = None, hs6: str = None, type: str = None, limit: int = None) -> List[Dict]:
        """
        Filtered signals data
        
        Args:
            country: Filter by partner country ISO3
            hs6: Filter by HS6 product code
            type: Filter by signal type
            limit: Limit number of results
            
        Returns:
            List of signal dictionaries
        """
        df = self.signals.copy()
        
        if len(df) == 0:
            return []
        
        # Apply filters
        if country:
            df = df[df['partner_iso3'] == country]
        if hs6:
            df = df[df['hs6'] == hs6]
        if type:
            df = df[df['type'] == type]
        if limit:
            df = df.head(limit)
            
        # Convert to records
        results = df.to_dict('records')
        
        # Add HS6 names if available
        hs6_names = self.metadata.get('hs6_names', {})
        for result in results:
            if result.get('hs6') in hs6_names:
                result['hs6_name'] = hs6_names[result['hs6']]
        
        return results
    
    def get_products_data(self, country: str = None, top: int = 50, year: int = 2023) -> List[Dict]:
        """
        Products data from core trade
        
        Args:
            country: Filter by partner country
            top: Number of top products to return
            year: Year filter
            
        Returns:
            List of {id, name, value, value_fmt, unit} for products
        """
        df = self.core_trade.copy()
        
        if country:
            df = df[df['partner_iso3'] == country]
            
        if len(df) == 0:
            return []
        
        # Aggregate by HS6
        products = df.groupby('hs6')['export_cz_to_partner'].sum().reset_index()
        products = products.sort_values('export_cz_to_partner', ascending=False).head(top)
        
        # Format for display
        hs6_names = self.metadata.get('hs6_names', {})
        results = []
        
        for _, row in products.iterrows():
            hs6 = row['hs6']
            value = row['export_cz_to_partner']
            
            # Format value
            if value >= 1_000_000:
                value_fmt = f"{value/1_000_000:.1f}M USD"
            else:
                value_fmt = f"{value:,.0f} USD"
            
            results.append({
                'id': hs6,
                'name': hs6_names.get(hs6, f"HS6 {hs6}"),
                'value': float(value),
                'value_fmt': value_fmt,
                'unit': 'USD'
            })
        
        return results
    
    def get_peer_groups_data(self, country: str, methodology: str = 'human') -> Dict[str, Any]:
        """
        Get peer group information for a country
        
        Args:
            country: Country ISO3 code
            methodology: Peer group methodology (human, hs2, opportunity, statistical)
            
        Returns:
            Dictionary with peer group information
        """
        df = self.peers.copy()
        
        if len(df) == 0:
            return {'peers': [], 'methodology': methodology}
        
        # Filter by methodology and country
        peer_data = df[
            (df['methodology'] == methodology) & 
            (df.get('country_iso3') == country)
        ]
        
        if len(peer_data) == 0:
            return {'peers': [], 'methodology': methodology}
        
        # Extract peer countries (implementation depends on data structure)
        # This may need adjustment based on actual peer group data format
        result = {
            'methodology': methodology,
            'peers': peer_data.to_dict('records')
        }
        
        return result


# Global instance for import
deployment_data = DeploymentDataLoader()