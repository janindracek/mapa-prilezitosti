import os
from typing import Dict, Any


class Settings:
    """Centralized configuration for the API"""
    
    # Deployment data paths
    DEPLOYMENT_DATA_PATH: str = "data/deployment"
    CORE_TRADE_PATH: str = "data/deployment/core_trade.parquet"
    SIGNALS_PATH: str = "data/deployment/signals_filtered.parquet" 
    PEERS_PATH: str = "data/deployment/peer_relationships.parquet"
    METADATA_PATH: str = "data/deployment/metadata.parquet"
    
    # Legacy paths for backward compatibility
    BACI_PARQUET_PATH: str = CORE_TRADE_PATH
    MAP_PARQUET_PATH: str = CORE_TRADE_PATH
    METRICS_PARQUET_PATH: str = CORE_TRADE_PATH
    HS6_REF_PATH: str = "data/ref/hs_mapping.csv"
    
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