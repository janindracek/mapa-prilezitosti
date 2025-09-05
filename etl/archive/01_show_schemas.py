import os, glob
import pyarrow.parquet as pq

PARQUET_DIR = "data/parquet"

def main():
    paths = glob.glob(os.path.join(PARQUET_DIR, "*.parquet"))
    if not paths:
        print("No parquet files in data/parquet")
        return
    for p in sorted(paths):
        print("="*80)
        print(p)
        try:
            pf = pq.ParquetFile(p)
            print(pf.schema_arrow)
        except Exception as e:
            print(f"ERROR reading schema: {e}")

if __name__ == "__main__":
    main()