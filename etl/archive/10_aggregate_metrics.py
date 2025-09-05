#!/usr/bin/env python3
"""
Aggregate core metrics from Parquet into tidy tables.
Outputs:
- trade_by_pair.parquet: year, exporter, importer, value_usd
- trade_by_product.parquet: year, exporter, hs6, value_usd
- trade_by_hs2.parquet: year, exporter, hs2, value_usd
- trade_by_exporter.parquet: year, exporter, value_usd
"""
from pathlib import Path
import pandas as pd

PARQ = Path(__file__).resolve().parents[1] / "data" / "parquet"
OUT = PARQ


def load_baci_frames():
    parts = []
    found = []
    patterns = [
        "BACI_HS22_*/data.parquet",      # expected layout from 00_convert_to_parquet.py
        "BACI_HS22_*/*/data.parquet",   # legacy two-level layout
    ]
    for pat in patterns:
        for p in PARQ.glob(pat):
            found.append(p)
    # de-duplicate while preserving order
    seen = set()
    for p in found:
        if p not in seen:
            seen.add(p)
            parts.append(pd.read_parquet(p))

    if not parts:
        raise SystemExit(f"No Parquet inputs found under {PARQ}. Expected files like data/parquet/BACI_HS22_YYYY_*/data.parquet. Run 00_convert_to_parquet.py first.")
    df = pd.concat(parts, ignore_index=True)
    return df


def main():
    df = load_baci_frames()
    # Core numeric
    if "value_usd" not in df:
        raise SystemExit("Missing value_usd column after conversion.")

    # Trade by country pair
    pair = (
        df.groupby(["year", "exporter", "importer"], as_index=False)["value_usd"].sum()
    )
    pair.to_parquet(OUT / "trade_by_pair.parquet", index=False)

    # Trade by product (hs6)
    if "hs6" in df:
        prod = (
            df.groupby(["year", "exporter", "hs6"], as_index=False)["value_usd"].sum()
        )
        prod.to_parquet(OUT / "trade_by_product.parquet", index=False)

        # HS2 rollup
        prod["hs2"] = (prod["hs6"].astype("Int64") // 10_000).astype("Int64")
        hs2 = prod.groupby(["year", "exporter", "hs2"], as_index=False)["value_usd"].sum()
        hs2.to_parquet(OUT / "trade_by_hs2.parquet", index=False)

    # Totals by exporter
    exp = df.groupby(["year", "exporter"], as_index=False)["value_usd"].sum()
    exp.to_parquet(OUT / "trade_by_exporter.parquet", index=False)

    print("Saved aggregated tables to:")
    for f in ["trade_by_pair.parquet", "trade_by_product.parquet", "trade_by_hs2.parquet", "trade_by_exporter.parquet"]:
        fp = OUT / f
        if fp.exists():
            print(" -", fp)


if __name__ == "__main__":
    main()