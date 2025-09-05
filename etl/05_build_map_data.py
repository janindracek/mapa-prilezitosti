"""
ETL: build map_rows.parquet with three map metrics for all HS6 x year x partner.
Inputs (defaults match your paths):
  - data/parquet/trade_by_pair.parquet           (year, exporter, importer, hs6, value_usd)
  - data/parquet/trade_by_product.parquet        (unused for now; kept for future cross-checks)
  - data/parquet/trade_by_exporter.parquet       (unused for now; could speed CZ world totals)
  - optional country map CSV/Parquet with columns: id, iso3, name

Usage:
  python etl/30_map_rows.py --cz-id 203 \\
      --country-map data/parquet/country_map.parquet

If --country-map is omitted, iso3 will be a stringified numeric id and name will be empty.
No new dependencies; uses pandas/pyarrow.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import sys
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# BACI values are in thousands of USD - apply scaling
TRADE_SCALE = int(os.environ.get("TRADE_UNITS_SCALE", "1000"))

ROOT = Path(__file__).resolve().parents[1]
P_IN = ROOT / "data" / "parquet"
P_OUT = ROOT / "data" / "out" / "ui_shapes"
P_OUT.mkdir(parents=True, exist_ok=True)

PAIR_PATH = P_IN / "trade_by_pair.parquet"
PROD_PATH = P_IN / "trade_by_product.parquet"  # reserved
EXP_PATH  = P_IN / "trade_by_exporter.parquet"  # reserved
OUT_PATH  = P_OUT / "map_rows.parquet"


def to_num(v):
    """Coerce value_usd that may be string to float; treat None/empty as 0."""
    if pd.isna(v):
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s == "":
        return 0.0
    s = s.replace(",", "")
    try:
        return float(s)
    except Exception:
        return 0.0


def load_country_map(path: Path | None) -> pd.DataFrame:
    if not path:
        return pd.DataFrame({"id": [], "iso3": [], "name": []})
    if not path.exists():
        print(f"WARN: country map not found: {path}; proceeding without it", file=sys.stderr)
        return pd.DataFrame({"id": [], "iso3": [], "name": []})
    if path.suffix.lower() in (".parquet", ".pq"):
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}
    id_col = cols.get("id") or cols.get("code") or cols.get("country_id")
    iso_col = cols.get("iso3") or cols.get("iso") or cols.get("alpha3")
    name_col = cols.get("name") or cols.get("country") or cols.get("label")
    df = df.rename(columns={id_col: "id", iso_col: "iso3", name_col: "name"})
    keep = [c for c in ["id", "iso3", "name"] if c in df.columns]
    return df[keep]


def build_map_rows(pair_df: pd.DataFrame, cz_id: int, country_map: pd.DataFrame) -> pd.DataFrame:
    # Normalize columns
    cols = {c.lower(): c for c in pair_df.columns}
    df = pair_df.rename(columns={
        cols.get("year"): "year",
        cols.get("exporter"): "exporter",
        cols.get("importer"): "importer",
        cols.get("hs6"): "hs6",
        cols.get("value_usd"): "value_usd",
    })[["year", "exporter", "importer", "hs6", "value_usd"]].copy()

    # Types
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["exporter"] = pd.to_numeric(df["exporter"], errors="coerce").astype("Int64")
    df["importer"] = pd.to_numeric(df["importer"], errors="coerce").astype("Int64")
    df["hs6"] = pd.to_numeric(df["hs6"], errors="coerce").astype("Int64")
    df["value"] = df["value_usd"].map(to_num).astype("float64") * TRADE_SCALE

    # Guard: drop NA rows
    df = df.dropna(subset=["year", "exporter", "importer", "hs6"])

    # Current year CZ -> partner by HS6
    cz = df[df["exporter"] == cz_id]
    cz_group = cz.groupby(["year", "hs6", "importer"], as_index=False)["value"].sum()
    cz_curr = cz_group.rename(columns={"value": "cz_curr"})

    # Previous year CZ -> partner (shift year - 1 so join hits prev)
    cz_prev = cz_curr.copy()
    cz_prev["year"] = cz_prev["year"] - 1
    cz_prev.rename(columns={"cz_curr": "cz_prev"}, inplace=True)


    # CZ world totals per HS6
    world_group = cz.groupby(["year", "hs6"], as_index=False)["value"].sum()
    cz_world = world_group.rename(columns={"value": "cz_world"})
    cz_world_prev = cz_world.copy()
    cz_world_prev["year"] = cz_world_prev["year"] - 1
    cz_world_prev.rename(columns={"cz_world": "cz_world_prev"}, inplace=True)
    

    # Partner import totals per HS6 (sum of all exporters into importer)
    imp_group = df.groupby(["year", "hs6", "importer"], as_index=False)["value"].sum()
    imp_tot = imp_group.rename(columns={"value": "imp_total"})

    # Merge all metrics
    out = (
        cz_curr.merge(cz_prev, on=["year", "hs6", "importer"], how="left")
              .merge(cz_world, on=["year", "hs6"], how="left")
              .merge(cz_world_prev, on=["year", "hs6"], how="left")
              .merge(imp_tot, on=["year", "hs6", "importer"], how="left")
    )

    # Safe fills
    for c in ["cz_prev", "cz_world", "cz_world_prev", "imp_total"]:
        out[c] = out[c].fillna(0.0)

    # Metrics
    out["delta_export_abs"] = out["cz_curr"] - out["cz_prev"]
    out["cz_share_in_partner_import"] = (out["cz_curr"] / out["imp_total"]).where(out["imp_total"] > 0, 0.0)
    out["partner_share_in_cz_exports"] = (out["cz_curr"] / out["cz_world"]).where(out["cz_world"] > 0, 0.0)

    # Map importer id -> iso3/name (optional)
    if not country_map.empty and {"id", "iso3"}.issubset(set(country_map.columns)):
        cm = country_map.rename(columns={"id": "importer"})
        out = out.merge(cm, on="importer", how="left")
        out["iso3"] = out["iso3"].fillna(out["importer"].astype(str))
        out["name"] = out.get("name").fillna("") if "name" in out.columns else ""
    else:
        out["iso3"] = out["importer"].astype(str)
        out["name"] = ""

    # Final column order
    out = out.rename(columns={"importer": "partner_id"})
    out = out[[
        "hs6", "year", "partner_id", "iso3", "name",
        "cz_curr", "cz_prev", "imp_total", "cz_world", "cz_world_prev",
        "delta_export_abs", "cz_share_in_partner_import", "partner_share_in_cz_exports",
    ]].sort_values(["year", "hs6", "partner_id"]).reset_index(drop=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", type=Path, default=PAIR_PATH)
    ap.add_argument("--country-map", type=Path, default=None)
    ap.add_argument("--cz-id", type=int, required=True, help="Numeric exporter id for Czech Republic (matches 'exporter' field)")
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args()

    if not args.pair.exists():
        print(f"ERROR: missing trade_by_pair parquet: {args.pair}", file=sys.stderr)
        sys.exit(2)

    # Load
    pair_df = pd.read_parquet(args.pair)
    country_map = load_country_map(args.country_map)

    # Build
    out_df = build_map_rows(pair_df, cz_id=args.cz_id, country_map=country_map)

    if out_df.empty:
        print("WARN: output is empty (check --cz-id and input coverage)", file=sys.stderr)

    # Write parquet
    table = pa.Table.from_pandas(out_df, preserve_index=False)
    pq.write_table(table, args.out)

    # Smoke assertion: required columns exist
    required_cols = {
        "hs6", "year", "iso3", "delta_export_abs",
        "cz_share_in_partner_import", "partner_share_in_cz_exports"
    }
    missing = required_cols - set(out_df.columns)
    assert not missing, f"Missing expected columns in output: {missing}"

    print(f"Wrote {len(out_df):,} rows → {args.out}")


if __name__ == "__main__":
    main()
