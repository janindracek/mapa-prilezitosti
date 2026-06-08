"""
ETL stage 05 — build ui_shapes/map_rows.parquet for the world map.

M4a rebase: this stage now reads the already-built metrics.parquet (stage 02)
instead of re-reading raw BACI. Consequences:
  * Dollars are scaled in exactly ONE place (stage 01). The old version
    re-applied TRADE_UNITS_SCALE here — a duplicate that is now gone.
  * All-importer coverage flows in for free from the outer-join fact base.
  * Country codes/names come from country_ref (single source of truth).
Prior-year/delta columns are computed once in stage 02 and reused here.

Usage:  python etl/05_build_map_data.py            # reads data/out/metrics.parquet
        python etl/05_build_map_data.py --out <path>
(`--cz-id` is accepted but ignored; kept so older invocations don't break.)
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import country_ref as cr

ROOT = Path(__file__).resolve().parents[1]
METRICS_PATH = ROOT / "data" / "out" / "metrics.parquet"
P_OUT = ROOT / "data" / "out" / "ui_shapes"
P_OUT.mkdir(parents=True, exist_ok=True)
OUT_PATH = P_OUT / "map_rows.parquet"


def build_map_rows(metrics: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "hs6": metrics["hs6"],
        "year": pd.to_numeric(metrics["year"], errors="coerce").astype("Int64"),
        "iso3": metrics["partner_iso3"].astype("string"),
        "cz_curr": metrics["export_cz_to_partner"].fillna(0.0),
        "cz_prev": metrics["export_cz_to_partner_prev"].fillna(0.0),
        "imp_total": metrics["import_partner_total"].fillna(0.0),
        "cz_world": metrics["export_cz_total_for_hs6"].fillna(0.0),
        "cz_world_prev": metrics["export_cz_total_for_hs6_prev"].fillna(0.0),
        "cz_share_in_partner_import": metrics["podil_cz_na_importu"].fillna(0.0),
        "partner_share_in_cz_exports": metrics["partner_share_in_cz_exports"].fillna(0.0),
    })

    # Absolute YoY delta (recomputed from filled values to match map semantics).
    out["delta_export_abs"] = out["cz_curr"] - out["cz_prev"]

    # Country id + name from the single source of truth (no dollar scaling here).
    out["partner_id"] = out["iso3"].map(cr.iso3_to_num).astype("Int64")
    out["name"] = out["iso3"].map(cr.iso3_to_name).fillna("")

    out = out[[
        "hs6", "year", "partner_id", "iso3", "name",
        "cz_curr", "cz_prev", "imp_total", "cz_world", "cz_world_prev",
        "delta_export_abs", "cz_share_in_partner_import", "partner_share_in_cz_exports",
    ]].sort_values(["year", "hs6", "partner_id"]).reset_index(drop=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics", type=Path, default=METRICS_PATH)
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    ap.add_argument("--cz-id", type=int, default=None, help="(ignored; kept for backward compat)")
    args = ap.parse_args()

    if not args.metrics.exists():
        print(f"ERROR: missing metrics parquet: {args.metrics} (run etl/02 first)", file=sys.stderr)
        sys.exit(2)

    metrics = pd.read_parquet(args.metrics)
    out_df = build_map_rows(metrics)

    if out_df.empty:
        print("WARN: output is empty (check metrics coverage)", file=sys.stderr)

    table = pa.Table.from_pandas(out_df, preserve_index=False)
    pq.write_table(table, args.out)

    required_cols = {
        "hs6", "year", "iso3", "delta_export_abs",
        "cz_share_in_partner_import", "partner_share_in_cz_exports",
    }
    missing = required_cols - set(out_df.columns)
    assert not missing, f"Missing expected columns in output: {missing}"

    print(f"[PASS] Wrote {len(out_df):,} rows -> {args.out}")
    print(f"[PASS] Importer coverage: {out_df['iso3'].nunique()} countries")


if __name__ == "__main__":
    main()
