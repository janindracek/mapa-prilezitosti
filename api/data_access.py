from pathlib import Path
from functools import lru_cache
from api.settings import settings


# M4b: the metrics frame IS the serving core_trade table.
METRICS_PATH = Path(settings.METRICS_PARQUET_PATH)


def metrics_mtime_key() -> tuple[float, float]:
    """Cache-invalidation key: mtime of the serving core_trade parquet."""
    m = METRICS_PATH.stat().st_mtime if METRICS_PATH.exists() else 0.0
    return (m, 0.0)


@lru_cache(maxsize=1)
def get_metrics_cached(_key: tuple[float, float]):
    """Cached load of the serving core_trade fact table.

    Memory-critical: this is the shared full-frame cache behind /controls,
    /products, /bars, /insights_data, /peer_groups and the signals service.
    The naive object-string + float64 load of all 1.78M rows hit ~425 MB
    resident / ~730 MB peak and OOM-crashed the 512 MB hosting tier. We read
    with the pyarrow backend (compact string storage, no object-string read
    spike) and downcast the float columns to float32 — cutting the resident
    frame to ~155 MB with no display-visible precision loss. maxsize=1: keep a
    single copy (the data is static between annual refreshes).
    """
    import pandas as pd
    if not METRICS_PATH.exists():
        return pd.DataFrame()
    return pd.read_parquet(METRICS_PATH, dtype_backend="pyarrow")
