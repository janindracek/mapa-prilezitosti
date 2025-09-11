from pathlib import Path
from functools import lru_cache
import pandas as pd
from api.settings import settings

# Paths to UI shape files - use settings for deployment/local compatibility
MAP_ROWS_PATH = Path(settings.MAP_PARQUET_PATH)
PRODUCT_ROWS_PATH = Path(settings.METRICS_PARQUET_PATH)  # Fallback to metrics for product data

def map_cache_key() -> float:
    """Cache key for map data based on file modification time."""
    return MAP_ROWS_PATH.stat().st_mtime if MAP_ROWS_PATH.exists() else 0.0

def product_cache_key() -> float:
    """Cache key for product data based on file modification time."""
    return PRODUCT_ROWS_PATH.stat().st_mtime if PRODUCT_ROWS_PATH.exists() else 0.0

@lru_cache(maxsize=8)
def get_map_rows(_key: float):
    """Get cached map rows data."""
    if MAP_ROWS_PATH.exists():
        return pd.read_parquet(MAP_ROWS_PATH)
    else:
        # Return empty DataFrame if file doesn't exist
        return pd.DataFrame(columns=['iso3', 'name', 'value', 'value_fmt', 'unit'])

@lru_cache(maxsize=8)
def get_product_rows(_key: float):
    """Get cached product rows data."""
    if PRODUCT_ROWS_PATH.exists():
        return pd.read_parquet(PRODUCT_ROWS_PATH)
    else:
        # Return empty DataFrame if file doesn't exist
        return pd.DataFrame(columns=['id', 'name', 'value', 'value_fmt', 'unit'])