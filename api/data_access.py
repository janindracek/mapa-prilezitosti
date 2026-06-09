from pathlib import Path
from functools import lru_cache
from api.settings import settings


# M4b: the metrics frame IS the serving core_trade table.
METRICS_PATH = Path(settings.METRICS_PARQUET_PATH)


def metrics_mtime_key() -> tuple[float, float]:
    """Cache-invalidation key: mtime of the serving core_trade parquet."""
    m = METRICS_PATH.stat().st_mtime if METRICS_PATH.exists() else 0.0
    return (m, 0.0)


@lru_cache(maxsize=8)
def get_metrics_cached(_key: tuple[float, float]):
    """Cached load of the serving core_trade fact table."""
    import pandas as pd
    if METRICS_PATH.exists():
        return pd.read_parquet(METRICS_PATH)
    return pd.DataFrame()
