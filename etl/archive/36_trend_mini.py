import os
import pandas as pd
from etl._env import env

SRC = "data/out/metrics_enriched.parquet"
OUT = "data/out/ui_shapes/trend_mini.json"

def main():
    if not os.path.isfile(SRC):
        raise FileNotFoundError(f"Missing {SRC}")
    df = pd.read_parquet(SRC)

    # Params
    year = env("YEAR", int(df["year"].max()), int)
    hs6  = env("HS6", None, str)
    tail = env("YEARS", 10, int)  # number of most recent years to show

    # Pick HS6 if not provided: top by CZ export in selected year
    cur_year = df[df["year"] == year]
    if cur_year.empty:
        raise RuntimeError(f"No data for year={year}")
    if not hs6:
        top = cur_year.groupby("hs6")["export_cz_to_partner"].sum().sort_values(ascending=False)
        if top.empty:
            raise RuntimeError("No HS6 found for the selected year.")
        hs6 = str(top.index[0]).zfill(6)
    else:
        hs6 = str(hs6).zfill(6)

    # Build trend: aggregate across partners (one point per year)
    trend = (
        df[df["hs6"] == hs6]
        .groupby("year", as_index=False)["export_cz_to_partner"].sum()
        .rename(columns={"export_cz_to_partner": "value"})
        .sort_values("year")
        .tail(tail)
    )

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    trend.to_json(OUT, orient="records")
    print(f"[PASS] Wrote {OUT} for hs6={hs6}, years={tail} (ending {trend['year'].max() if not trend.empty else 'N/A'})")
    print(trend.head())

if __name__ == "__main__":
    main()
