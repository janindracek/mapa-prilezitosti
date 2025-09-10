import os
from typing import Dict, Any


class Settings:
    """Centralized configuration for the API"""
    
    def __init__(self):
        # Check if deployment data is available
        self.DEPLOYMENT_AVAILABLE = os.path.exists("data/deployment/core_trade.csv")
        
        if self.DEPLOYMENT_AVAILABLE:
            # Deployment: Use CSV-based data
            self.DEPLOYMENT_DATA_PATH = "data/deployment"
            self.CORE_TRADE_PATH = "data/deployment/core_trade.parquet"
            self.SIGNALS_PATH = "data/deployment/signals_filtered.parquet" 
            self.PEERS_PATH = "data/deployment/peer_relationships.parquet"
            self.METADATA_PATH = "data/deployment/metadata.parquet"
            
            # Point to deployment data
            self.BACI_PARQUET_PATH = self.CORE_TRADE_PATH
            self.MAP_PARQUET_PATH = self.CORE_TRADE_PATH
            self.METRICS_PARQUET_PATH = self.CORE_TRADE_PATH
        else:
            # Local development: Use original parquet system
            self.DEPLOYMENT_DATA_PATH = "data/deployment"
            self.CORE_TRADE_PATH = "data/out/fact_base.parquet"
            self.SIGNALS_PATH = "data/out/signals_comprehensive.parquet" 
            self.PEERS_PATH = "data/out/peer_groups_statistical.parquet"
            self.METADATA_PATH = "data/out/metadata.parquet"
            
            # Point to original development data
            self.BACI_PARQUET_PATH = self.CORE_TRADE_PATH
            self.MAP_PARQUET_PATH = "data/out/ui_shapes/map_rows.parquet"
            self.METRICS_PARQUET_PATH = "data/out/metrics_enriched.parquet"
        
        self.HS6_REF_PATH = "data/ref/hs_mapping.csv"
    
    # UI shapes paths
    UI_SIGNALS_ENRICHED_PATH: str = "data/out/ui_shapes/signals_enriched.json"
    WORLD_MAP_JSON_PATH: str = "data/out/ui_shapes/world_map.json"
    
    # Peer group paths
    PEER_GROUPS_STATISTICAL_PATH: str = "data/out/peer_groups_statistical.parquet"
    PEER_GROUPS_HUMAN_PATH: str = "data/out/peer_groups_human.parquet"
    PEER_GROUPS_OPPORTUNITY_PATH: str = "data/out/peer_groups_opportunity.parquet"
    PEER_GROUPS_HS2_PATH: str = "data/out/peer_groups_hs2.parquet"
    PEER_MEDIANS_HUMAN_PATH: str = "data/out/peer_medians_human.parquet"
    TOP_SIGNALS_PATH: str = "data/out/top_signals.parquet"
    
    # Cache settings
    CACHE_TTL: int = 300  # 5 minutes
    
    @property
    def ENV(self) -> Dict[str, Any]:
        """Legacy ENV dict for backward compatibility"""
        return {
            "out": {
                "ui_signals_enriched": self.UI_SIGNALS_ENRICHED_PATH,
                "baci_parquet": self.BACI_PARQUET_PATH,
            }
        }


settings = Settings()