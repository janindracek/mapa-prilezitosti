from pathlib import Path
import pandas as pd

FILES = [
    "data/parquet/trade_by_hs2.parquet",
    "data/parquet/trade_by_pair.parquet",
    "data/parquet/trade_by_exporter.parquet",
    "data/parquet/trade_by_importer.parquet",
]

def inspect(path):
    p = Path(path)
    print(f"\n=== {p} ===")
    if not p.exists():
        print("  (missing)")
        return
    # Read tiny sample without loading everything
    try:
        df = pd.read_parquet(p)
    except Exception as e:
        print(f"  ! read error: {e}")
        return
    cols = list(df.columns)
    print("  columns:", cols)
    # Basic hints
    lc = [c.lower() for c in cols]
    if {"exporter","hs2","value_usd"}.issubset(lc):
        print("  hint: exporter×hs2 totals (likely exports-only aggregation)")
    if {"importer","hs2","value_usd"}.issubset(lc):
        print("  hint: importer×hs2 totals (good for imports structure)")
    if {"importer","exporter","hs6","flow","value_usd"}.issubset(lc):
        print("  hint: full pair-level table with flow (best fallback)")
    if "year" in lc:
        years = sorted(set(df["year"]))[:10]
        print("  sample years:", years)
    print("  head(3):")
    print(df.head(3).to_string(index=False))

if __name__ == "__main__":
    for f in FILES:
        inspect(f)
