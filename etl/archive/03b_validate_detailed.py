import pandas as pd

paths = [
    "data/parquet/BACI_HS22_Y2022_V202501/data.parquet",
    "data/parquet/BACI_HS22_Y2023_V202501/data.parquet",
]

def sniff_file(p):
    print("="*80)
    print(p)
    df = pd.read_parquet(p, columns=["year","exporter","importer","hs6","value_usd"])
    print(df.dtypes)
    # cast value_usd just to confirm it's numeric-castable
    df["value_usd_num"] = pd.to_numeric(df["value_usd"], errors="coerce")
    print("non-null % for value_usd_num:", df["value_usd_num"].notna().mean())
    # show a small sample of exporter/importer to see if they look like ISO3 or numeric
    print("sample exporter:", df["exporter"].astype(str).head(5).tolist())
    print("sample importer:", df["importer"].astype(str).head(5).tolist())
    print("years:", sorted(df["year"].dropna().unique())[:5], "...")

for p in paths:
    sniff_file(p)

print("=== Done ===")