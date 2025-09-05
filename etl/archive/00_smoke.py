import os, sys, glob

def ok(label, cond):
    print(f"[{'PASS' if cond else 'FAIL'}] {label}")
    if not cond:
        sys.exit(1)

def main():
    print("=== Environment smoke check ===")

    # 1) Package check
    try:
        import pandas as pd
        import pyarrow as pa
        import yaml
        print(f"[PASS] pandas {pd.__version__}, pyarrow {pa.__version__}, pyyaml OK")
    except Exception as e:
        print(f"[FAIL] Import error: {e}")
        sys.exit(1)

    # 2) Directory checks
    for d in ["data/parquet", "data/ref", "etl"]:
        ok(f"directory exists: {d}", os.path.isdir(d))

    # 3) Reference file check
    ok("data/ref/countries.csv exists", os.path.isfile("data/ref/countries.csv"))

    # 4) Parquet presence
    parquet_files = glob.glob("data/parquet/*.parquet")
    ok("at least one .parquet file present", len(parquet_files) >= 1)

    # 5) Peek schema of one parquet
    sample = parquet_files[0]
    print(f"[INFO] sampling file: {sample}")
    try:
        import pyarrow.parquet as pq
        pf = pq.ParquetFile(sample)
        print("[PASS] pyarrow schema read:")
        print(pf.schema_arrow)
    except Exception as e:
        print(f"[WARN] pyarrow read failed ({e}), trying pandas")
        try:
            df = pd.read_parquet(sample)
            print("[PASS] pandas read_parquet succeeded. Columns:", list(df.columns)[:10])
        except Exception as ee:
            print(f"[FAIL] Unable to read parquet: {ee}")
            sys.exit(1)

    print("=== Smoke check complete ===")

if __name__ == "__main__":
    main()