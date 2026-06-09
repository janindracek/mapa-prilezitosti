import os
from typing import Dict, Any


class Settings:
    """Centralized configuration for the API.

    M4b: ONE serving layer. The API reads only data/serving/*.parquet, produced
    by etl/07_build_serving.py. The old data/deployment CSV branch, the dead
    api.shapes path, and the /signals_unified second source are gone.
    """

    SERVING = "data/serving"

    def __init__(self):
        # The single source of truth — the serving layer.
        self.CORE_TRADE_PATH = f"{self.SERVING}/core_trade.parquet"
        self.SIGNALS_PATH = f"{self.SERVING}/signals.parquet"
        self.PEER_GROUPS_PATH = f"{self.SERVING}/peer_groups.parquet"
        self.HS6_NAMES_PATH = f"{self.SERVING}/hs6_names.parquet"
        self.COUNTRIES_PATH = f"{self.SERVING}/countries.parquet"

        # core_trade IS the metrics/map fact table (all 226 importers, both
        # years, real ×2 peer medians).
        self.METRICS_PARQUET_PATH = self.CORE_TRADE_PATH
        self.MAP_PARQUET_PATH = self.CORE_TRADE_PATH
        self.BACI_PARQUET_PATH = self.CORE_TRADE_PATH

        # Peer-group membership for every method lives in the one combined file;
        # loaders.load_peer_groups filters by method. These aliases keep older
        # call-sites working.
        self.PEER_GROUPS_HUMAN_PATH = self.PEER_GROUPS_PATH
        self.PEER_GROUPS_HS2_PATH = self.PEER_GROUPS_PATH
        self.PEER_GROUPS_STATISTICAL_PATH = self.PEER_GROUPS_PATH
        self.PEER_GROUPS_OPPORTUNITY_PATH = self.PEER_GROUPS_PATH

        self.HS6_REF_PATH = "data/ref/hs_mapping.csv"

    # UI shapes paths (legacy; unused by the serving path)
    UI_SIGNALS_ENRICHED_PATH: str = "data/out/ui_shapes/signals_enriched.json"
    WORLD_MAP_JSON_PATH: str = "data/out/ui_shapes/world_map.json"

    CACHE_TTL: int = 300

    @property
    def ENV(self) -> Dict[str, Any]:
        return {"out": {"baci_parquet": self.BACI_PARQUET_PATH}}


settings = Settings()
