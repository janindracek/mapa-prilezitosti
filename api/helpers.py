from __future__ import annotations
from typing import Optional, List, Dict, Any
import os
import pandas as pd

from api.formatting import fmt_value as _fmt_value, to_json_safe as _to_json_safe
from api.normalizers import normalize_iso as _normalize_iso, norm_hs2 as _norm_hs2

# ------------------------
# Trend glue (pure)
# ------------------------
def build_trend(df: pd.DataFrame, hs6: str, years: int = 10) -> List[Dict[str, Any]]:
    """
    Return time series for selected HS6 aggregated across partners.
    Returns [{ year, value, value_fmt, unit }]
    """
    hs6 = str(hs6).zfill(6)
    # FIXED: Use pre-calculated world total instead of summing bilateral exports
    # This ensures consistency and avoids issues with filtered/missing data
    cur = (
        df[df["hs6"] == hs6]
        .groupby("year")["export_cz_total_for_hs6"]
        .first()  # Take first value (should be same for all partners in same year/hs6)
        .reset_index(name="value")
        .sort_values("year")
        .tail(years)
    )
    records = cur.to_dict(orient="records")
    for r in records:
        r["value_fmt"], r["unit"] = _fmt_value(r["value"], "export")
        r["value"] = _to_json_safe(r["value"])
    return records
