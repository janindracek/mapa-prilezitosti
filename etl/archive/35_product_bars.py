import os
import pandas as pd
from etl._env import env

SRC = "data/out/metrics_enriched.parquet"
CODES = "data/parquet/product_codes_HS22.parquet"
OUT = "data/out/ui_shapes/product_bars.json"

def hs_names():
    if os.path.isfile(CODES):
        df = pd.read_parquet(CODES, columns=["code","description"]).copy()
        df["code"] = df["code"].astype("Int64").astype("string").str.pad(6, fillchar="0")
        return dict(zip(df["code"], df["description"]))
    return {}

def main():
    if not os.path.isfile(SRC):
        raise FileNotFoundError(f"Missing {SRC}")
    df = pd.read_parquet(SRC)
    year = env("YEAR", int(df["year"].max()), int)
    top  = env("TOP", 10, int)

    cur = df[df["year"] == year]
    if cur.empty:
        raise RuntimeError(f"No data for year={year}")

    # top HS6 by CZ export
    bars = (cur.groupby("hs6")["export_cz_to_partner"]
              .sum()
              .nlargest(top)
              .reset_index())
    bars["id"] = bars["hs6"].astype(str).str.zfill(6)
    bars = bars.rename(columns={"export_cz_to_partner":"value"})[["id","value"]]

    names = hs_names()
    bars["name"] = bars["id"].map(lambda x: names.get(x, x))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bars.to_json(OUT, orient="records")
    print(f"[PASS] Wrote {OUT} for year={year}, top={top}")
    print(bars.head())

if __name__ == "__main__":
    main()
