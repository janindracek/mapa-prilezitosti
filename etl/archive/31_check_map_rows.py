
"""
Integrity checks for data/out/ui_shapes/map_rows.parquet
Validates:
  - Required columns present and dtypes sane
  - No NaNs in required numeric columns
  - Shares within [0, 1] (allow a tiny epsilon)
  - delta_export_abs ~= cz_curr - cz_prev
  - Optional: if cz_world==0 then partner_share_in_cz_exports==0; if imp_total==0 then cz_share_in_partner_import==0
Prints a brief summary and fails with nonzero exit on violations.
"""
from __future__ import annotations
import sys
from pathlib import Path
import math
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data" / "out" / "ui_shapes" / "map_rows.parquet"

REQ_COLS = [
    "hs6", "year", "partner_id", "iso3",
    "cz_curr", "cz_prev", "imp_total", "cz_world", "cz_world_prev",
    "delta_export_abs", "cz_share_in_partner_import", "partner_share_in_cz_exports",
]

EPS = 1e-9

def fail(msg: str):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)

def main():
    if not PATH.exists():
        fail(f"missing file: {PATH}")
    df = pd.read_parquet(PATH)

    # Columns
    missing = [c for c in REQ_COLS if c not in df.columns]
    if missing:
        fail(f"missing columns: {missing}")

    # Basic types / coercions
    for c in ["hs6", "year", "partner_id"]:
        if not pd.api.types.is_integer_dtype(df[c]):
            try:
                df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
            except Exception:
                fail(f"column {c} is not integer dtype and cannot be coerced")
    for c in ["cz_curr", "cz_prev", "imp_total", "cz_world", "cz_world_prev",
              "delta_export_abs", "cz_share_in_partner_import", "partner_share_in_cz_exports"]:
        if not pd.api.types.is_float_dtype(df[c]):
            try:
                df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
            except Exception:
                fail(f"column {c} is not float dtype and cannot be coerced")

    # No NaNs in required numeric columns (except allowed zeros)
    num_cols = ["cz_curr","cz_prev","imp_total","cz_world","cz_world_prev",
                "delta_export_abs","cz_share_in_partner_import","partner_share_in_cz_exports"]
    nan_counts = df[num_cols].isna().sum()
    nan_viol = nan_counts[nan_counts > 0]
    if len(nan_viol):
        fail(f"NaNs present in numeric columns: {nan_viol.to_dict()}")

    # Shares in [0,1] with tiny epsilon
    def out_of_range(s):
        return ((s < -EPS) | (s > 1 + EPS)).sum()
    bad_partner_share = out_of_range(df["partner_share_in_cz_exports"])
    bad_cz_share = out_of_range(df["cz_share_in_partner_import"])
    if bad_partner_share or bad_cz_share:
        fail(f"share out-of-range rows: partner_share={bad_partner_share}, cz_share={bad_cz_share}")

    # Delta consistency
    delta_diff = (df["cz_curr"] - df["cz_prev"]) - df["delta_export_abs"]
    bad_delta = (delta_diff.abs() > 1e-6).sum()
    if bad_delta:
        # print a small sample of bad rows
        sample = df.loc[(delta_diff.abs() > 1e-6), ["hs6","year","partner_id","cz_curr","cz_prev","delta_export_abs"]].head(5)
        fail(f"delta mismatch in {bad_delta} rows; sample:\n{sample}")

    # Conditional zero checks (not failing, just warn)
    zero_world = df[(df["cz_world"] <= EPS) & (df["partner_share_in_cz_exports"] > EPS)]
    zero_imp = df[(df["imp_total"] <= EPS) & (df["cz_share_in_partner_import"] > EPS)]
    if len(zero_world) or len(zero_imp):
        print(f"WARN: non-zero shares with zero denominators: cz_world={len(zero_world)}, imp_total={len(zero_imp)}")

    # Summary
    rows = len(df)
    years = f"{int(df['year'].min())}–{int(df['year'].max())}" if rows else "n/a"
    print(f"OK: map_rows.parquet valid | rows={rows:,} | years={years} | unique HS6={df['hs6'].nunique():,} | partners={df['partner_id'].nunique():,}")

if __name__ == "__main__":
    main()
