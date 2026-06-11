from pathlib import Path
from functools import lru_cache
from api.settings import settings


# M4b: the metrics frame IS the serving core_trade table.
METRICS_PATH = Path(settings.METRICS_PARQUET_PATH)
_CORE = settings.METRICS_PARQUET_PATH  # 'data/serving/core_trade.parquet'


def metrics_mtime_key() -> tuple[float, float]:
    """Cache-invalidation key: mtime of the serving core_trade parquet."""
    m = METRICS_PATH.stat().st_mtime if METRICS_PATH.exists() else 0.0
    return (m, 0.0)


def query_core(columns, *, year=None, hs6=None, partner_iso3=None):
    """On-demand DuckDB read of a BOUNDED slice of core_trade.

    The fact table is 1.78M rows; loading it whole into pandas (even optimized)
    leaves a ~700 MB RSS high-water mark that OOM-crashes the 512 MB hosting
    tier. Instead, every endpoint that used the full frame now reads only the
    rows (predicate pushdown on year/hs6/partner_iso3) and columns it needs,
    straight from the parquet via DuckDB — which streams row groups instead of
    materializing the table. core_trade.parquet is written sorted by (year, hs6)
    in small row groups (etl/07) so these filters skip most of the file.

    Returns a pandas DataFrame (numpy/object dtypes) so existing downstream
    pandas logic is unchanged. `columns` come from our code (safe to inline);
    user-supplied filter values are passed as bound parameters.
    """
    import duckdb
    sel = ", ".join(columns)
    where, params = [], []
    if year is not None:
        where.append("year = ?"); params.append(int(year))
    if hs6 is not None:
        where.append("hs6 = ?"); params.append(str(hs6).zfill(6))
    if partner_iso3 is not None:
        where.append("partner_iso3 = ?"); params.append(str(partner_iso3))
    sql = f"SELECT {sel} FROM read_parquet('{_CORE}')"
    if where:
        sql += " WHERE " + " AND ".join(where)
    con = duckdb.connect()
    try:
        return con.execute(sql, params).df()
    finally:
        con.close()


@lru_cache(maxsize=1)
def core_max_year(_key: tuple[float, float]) -> int | None:
    """Latest year in core_trade (cheap aggregate; cached, invalidated by mtime)."""
    import duckdb
    con = duckdb.connect()
    try:
        row = con.execute(f"SELECT max(year) FROM read_parquet('{_CORE}')").fetchone()
        return int(row[0]) if row and row[0] is not None else None
    finally:
        con.close()


@lru_cache(maxsize=1)
def get_metrics_cached(_key: tuple[float, float]):
    """DEPRECATED full-frame load. No live endpoint calls this anymore — the
    map/products path uses ServingDataLoader and every other consumer uses
    query_core() / core_max_year() above. Kept only for the dead legacy
    SignalsService import. Do NOT reintroduce on a request path: it loads all
    1.78M rows and OOMs the 512 MB tier.
    """
    import pandas as pd
    if not METRICS_PATH.exists():
        return pd.DataFrame()
    return pd.read_parquet(METRICS_PATH, dtype_backend="pyarrow")
