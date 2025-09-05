import os
import pandas as pd
from typing import Dict, Optional, Any
from api.settings import settings


class DataCache:
    """Centralized caching for data access"""
    
    def __init__(self):
        self._map_cache: Dict[str, Any] = {"df": None, "mtime": None}
    
    def get_map_data(self) -> pd.DataFrame:
        """Load and cache map parquet data"""
        try:
            if not os.path.isfile(settings.MAP_PARQUET_PATH):
                return pd.DataFrame()
            
            mtime = os.path.getmtime(settings.MAP_PARQUET_PATH)
            if self._map_cache["df"] is None or self._map_cache["mtime"] != mtime:
                df = pd.read_parquet(settings.MAP_PARQUET_PATH)
                cols = [
                    "hs6", "year", "iso3", "name",
                    "delta_export_abs", "cz_share_in_partner_import", "partner_share_in_cz_exports",
                    "cz_curr", "cz_world", "imp_total",
                ]
                df = df[cols].copy()
                self._map_cache["df"] = df
                self._map_cache["mtime"] = mtime
            
            return self._map_cache["df"]
        except Exception:
            return pd.DataFrame()


# Global cache instance
cache = DataCache()