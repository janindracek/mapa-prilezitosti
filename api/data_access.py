import threading
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


_DUCK = None

# DuckDB's memory_limit caps only DuckDB-internal memory; the pandas DataFrames
# each query materializes are uncapped Python memory. Under concurrent load those
# result frames stack up (the 2023 slice alone is ~56 MB as pandas) and OOM the
# 512 MB tier even though DuckDB itself stays within its cap. Bound how many
# results can be materializing at once; excess requests queue briefly instead of
# crashing the worker.
_QUERY_SEM = threading.Semaphore(4)


def _duck():
    """One shared DuckDB connection, hard-capped so it can never balloon past
    the hosting RAM. Per-request connections accumulated memory under load and
    OOM-crashed the 512 MB tier; a single capped connection (reused via cursors)
    is memory-stable. memory_limit is a HARD ceiling DuckDB respects by
    spilling/erroring rather than growing; threads kept low (each buffers).
    """
    global _DUCK
    if _DUCK is None:
        import duckdb
        c = duckdb.connect()
        c.execute("SET memory_limit='200MB'")  # hard cap — DuckDB spills, never OOMs the process
        c.execute("SET threads TO 2")
        c.execute("SET preserve_insertion_order=false")
        _DUCK = c
    return _DUCK


def query_core(columns, *, year=None, hs6=None, partner_iso3=None):
    """On-demand DuckDB read of a BOUNDED slice of core_trade.

    The fact table is 1.78M rows; loading it whole into pandas (even optimized)
    leaves a ~700 MB RSS high-water mark that OOM-crashes the 512 MB hosting
    tier. Instead, every endpoint that used the full frame reads only the rows
    (predicate pushdown on year/hs6/partner_iso3) and columns it needs, straight
    from the parquet via DuckDB — which streams row groups instead of
    materializing the table. core_trade.parquet is written sorted by (year, hs6)
    in small row groups (etl/07) so these filters skip most of the file.

    Returns a pandas DataFrame (numpy/object dtypes) so existing downstream
    pandas logic is unchanged. `columns` come from our code (safe to inline);
    user-supplied filter values are passed as bound parameters. A fresh cursor
    per call keeps it thread-safe under uvicorn's worker threadpool.
    """
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
    with _QUERY_SEM:
        return _duck().cursor().execute(sql, params).df()


def top_products(year, partner_iso3=None, hs2=None, top=10):
    """Top HS6 by summed CZ export, aggregated INSIDE DuckDB.

    The pandas equivalent (read the whole year slice, then groupby) materializes
    ~894k rows / ~56 MB per request; a handful of concurrent calls OOMs the
    512 MB tier. Aggregating in SQL returns `top` rows instead. lpad() guards
    against any non-zero-padded hs6 values, matching the old .str.zfill(6).
    """
    where, params = ["year = ?"], [int(year)]
    if partner_iso3 is not None:
        where.append("partner_iso3 = ?"); params.append(str(partner_iso3))
    if hs2 is not None:
        where.append("lpad(hs6, 6, '0') LIKE ?"); params.append(f"{str(hs2).zfill(2)}%")
    sql = (
        "SELECT lpad(hs6, 6, '0') AS hs6, SUM(export_cz_to_partner) AS value "
        f"FROM read_parquet('{_CORE}') WHERE {' AND '.join(where)} "
        f"GROUP BY 1 ORDER BY value DESC LIMIT {max(int(top), 1)}"
    )
    with _QUERY_SEM:
        return _duck().cursor().execute(sql, params).df()


@lru_cache(maxsize=1)
def core_max_year(_key: tuple[float, float]) -> int | None:
    """Latest year in core_trade (cheap aggregate; cached, invalidated by mtime)."""
    row = _duck().cursor().execute(f"SELECT max(year) FROM read_parquet('{_CORE}')").fetchone()
    return int(row[0]) if row and row[0] is not None else None


@lru_cache(maxsize=1)
def country_import_totals(_key: tuple[float, float]) -> dict:
    """Total imports per country for the latest year: sum of import_partner_total
    across all hs6 (one small GROUP BY inside DuckDB, cached by parquet mtime).
    Used to order peer-group teaser examples by market size."""
    sql = (
        "SELECT partner_iso3, SUM(import_partner_total) AS total_imports "
        f"FROM read_parquet('{_CORE}') "
        f"WHERE year = (SELECT max(year) FROM read_parquet('{_CORE}')) "
        "GROUP BY 1"
    )
    with _QUERY_SEM:
        rows = _duck().cursor().execute(sql).fetchall()
    return {str(iso): float(total) for iso, total in rows
            if iso is not None and total is not None}


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
