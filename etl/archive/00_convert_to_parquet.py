#!/usr/bin/env python3
"""
Read BACI CSV (HS22) from data/raw, standardize columns, and write Parquet to data/parquet.
Memory-safe(ish): set dtypes and iterate in chunks.
"""
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT = Path(__file__).resolve().parents[1] / "data" / "parquet"
OUT.mkdir(parents=True, exist_ok=True)

# Column maps seen in BACI variants
COL_ALIASES = {
    "year": ["t", "year"],
    "exporter": ["i", "exporter", "reporter"],
    "importer": ["j", "importer", "partner"],
    "hs6": ["k", "product", "hs6", "hs_code"],
    "value_usd": ["v", "value", "trade_value_usd"],
    "quantity": ["q", "quantity"],
    "weight_kg": ["w", "weight", "weight_kg"]
}

DTYPES = {
    "year": "int16",
    "exporter": "int32",
    "importer": "int32",
    "hs6": "int32",
    "value_usd": "int64",
    "quantity": "float64",
    "weight_kg": "float64",
}


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for std, aliases in COL_ALIASES.items():
        for a in aliases:
            if a in df.columns:
                rename[a] = std
                break
    df = df.rename(columns=rename)

    # keep only recognized columns
    keep = [c for c in DTYPES if c in df.columns]
    df = df[keep]

    # Enforce consistent dtypes across chunks
    # Use pandas nullable integers for ints to allow NaNs after coercion
    INT_COLS = {"year", "exporter", "importer", "hs6", "value_usd"}
    FLOAT_COLS = {"quantity", "weight_kg"}

    for c in df.columns:
        if c in INT_COLS:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
        elif c in FLOAT_COLS:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")

    # normalize hs6 to 6-digit integer if present
    if "hs6" in df.columns:
        df["hs6"] = pd.to_numeric(df["hs6"], errors="coerce").astype("Int64")

    return df


def convert_file(csv_path: Path, chunksize: int = 1_000_000):
    print(f"Converting {csv_path.name} …")
    parquet_dir = OUT / csv_path.stem
    parquet_dir.mkdir(parents=True, exist_ok=True)

    writer = None
    for chunk in pd.read_csv(csv_path, dtype=str, chunksize=chunksize, on_bad_lines="skip", low_memory=False):
        df = _standardize_columns(chunk)
        if df.empty:
            continue
        table = pa.Table.from_pandas(df, preserve_index=False)
        if writer is None:
            writer = pq.ParquetWriter(parquet_dir / "data.parquet", table.schema)
        writer.write_table(table)
    if writer is not None:
        writer.close()
    print(f"→ {parquet_dir}/data.parquet")


def main():
    files = sorted(RAW.glob("BACI_HS22_*.csv"))
    if not files:
        raise SystemExit("No BACI_HS22_*.csv files found in data/raw")
    for f in files:
        convert_file(f)

    # Save reference tables as Parquet too (if present)
    ref_country = RAW / "country_codes.csv"
    if ref_country.exists():
        pd.read_csv(ref_country).to_parquet(OUT / "country_codes.parquet", index=False)
    ref_prod = RAW / "product_codes_HS22_V202501.csv"
    if ref_prod.exists():
        pd.read_csv(ref_prod).to_parquet(OUT / "product_codes_HS22.parquet", index=False)


if __name__ == "__main__":
    main()