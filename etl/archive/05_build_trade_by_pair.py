from pathlib import Path
import pandas as pd

PARQUET_ROOT = Path("data/parquet")
# These are the per-file outputs from 00_convert_to_parquet.py:
#   data/parquet/BACI_HS22_YYYY.../data.parquet
sources = sorted(PARQUET_ROOT.glob("BACI_HS22_*/data.parquet"))
if not sources:
    raise SystemExit("No converted BACI files found under data/parquet/BACI_HS22_*/data.parquet")

def load_one(p: Path) -> pd.DataFrame:
    df = pd.read_parquet(p)
    # normalize cols to lower
    df.columns = [c.lower() for c in df.columns]
    # tolerate variants (per 00_convert_to_parquet.py)
    ren = {}
    if "i" in df.columns: ren["i"] = "exporter"
    if "j" in df.columns: ren["j"] = "importer"
    if "k" in df.columns: ren["k"] = "hs6"
    if "t" in df.columns: ren["t"] = "year"
    if "v" in df.columns: ren["v"] = "value_usd"
    if ren:
        df = df.rename(columns=ren)
    needed = {"year","exporter","importer","hs6","value_usd"}
    missing = needed - set(df.columns)
    if missing:
        # Keep only what exists; skip files that don't have the core columns
        raise ValueError(f"{p} missing columns: {missing}")
    # keep minimal cols; ensure dtypes friendly for concat
    return df[["year","exporter","importer","hs6","value_usd"]].copy()

parts = []
for src in sources:
    try:
        parts.append(load_one(src))
    except Exception as e:
        print(f"[skip] {src}: {e}")

if not parts:
    raise SystemExit("No usable BACI parquet parts found; cannot build pair table.")

df = pd.concat(parts, ignore_index=True)

# Write unified pair table
pair_out = PARQUET_ROOT / "trade_by_pair.parquet"
df.to_parquet(pair_out, index=False)
print(f"Wrote {pair_out} with {len(df):,} rows and columns {list(df.columns)}")

# Optional: speed-up aggregation for imports by HS2 (importer × hs2 × year)
has_year = "year" in df.columns
group_cols = ["importer","hs6"] + (["year"] if has_year else [])
agg = df.groupby(group_cols, as_index=False)["value_usd"].sum()
agg = agg.rename(columns={"importer":"reporter_iso3","hs6":"hs2","value_usd":"trade_value_usd"})
hs2_out = PARQUET_ROOT / "trade_by_hs2_imports.parquet"
agg.to_parquet(hs2_out, index=False)
print(f"Wrote {hs2_out} with {len(agg):,} rows (aggregated imports by importer×HS2).")
