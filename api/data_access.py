from pathlib import Path
from functools import lru_cache
from api.settings import settings


# Cesty k parquetům
METRICS_ENR = Path(settings.METRICS_ENRICHED_PATH)
METRICS_FALLBACK = Path(settings.METRICS_PATH)

def metrics_mtime_key() -> tuple[float, float]:
    """
    Key for cache invalidation: (mtime of enriched, mtime of fallback).
    Pokud soubor neexistuje, použije se 0.0.
    """
    m1 = METRICS_ENR.stat().st_mtime if METRICS_ENR.exists() else 0.0
    m2 = METRICS_FALLBACK.stat().st_mtime if METRICS_FALLBACK.exists() else 0.0
    return (m1, m2)

@lru_cache(maxsize=8)
def get_metrics_cached(_key: tuple[float, float]):
    """
    Cached wrapper around load_metrics(). Key is (mtime_enr, mtime_fallback),
    so changing either parquet invalidates cache.
    """
    import pandas as pd
    
    # Load enriched metrics first, fallback to basic metrics
    if METRICS_ENR.exists():
        return pd.read_parquet(METRICS_ENR)
    elif METRICS_FALLBACK.exists():
        return pd.read_parquet(METRICS_FALLBACK)
    else:
        return pd.DataFrame()  # Empty DataFrame if no files exist