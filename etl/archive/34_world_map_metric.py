import os, json
import pandas as pd
import pycountry
from etl._env import env

SRC = "data/out/metrics_enriched.parquet"
OUT_DIR = "data/out/ui_shapes"
DST = os.path.join(OUT_DIR, "world_map.json")

def iso3_to_name(code):
    c = pycountry.countries.get(alpha_3=code)
    return c.name if c else code

def main():
    if not os.path.isfile(SRC):
        raise FileNotFoundError(f"Missing {SRC}. Run 26_merge_peer_into_metrics.py first.")
    df = pd.read_parquet(SRC)

    # parameters via env vars with safe fallbacks
    metric = env("METRIC", "delta_vs_peer", str)
    if metric not in df.columns:
        raise KeyError(f"Metric '{metric}' not found in columns")

    # year: default to latest available
    year = env("YEAR", int(df["year"].max()), int)
    cur = df[df["year"] == year].copy()

    # hs6: default to top by CZ export in that year if not provided
    hs6_env = env("HS6", None, str)
    if hs6_env:
        sel_hs6 = hs6_env.zfill(6)
    else:
        top = cur.groupby("hs6")["export_cz_to_partner"].sum().sort_values(ascending=False)
        if top.empty:
            raise RuntimeError("No data to select top HS6.")
        sel_hs6 = top.index[0]

    # build world map for the selected hs6 & metric
    sub = cur[cur["hs6"] == sel_hs6][["partner_iso3", metric]].dropna().copy()
    sub["name"] = sub["partner_iso3"].apply(iso3_to_name)
    world_map = sub.rename(columns={"partner_iso3":"iso3", metric:"value"})[["iso3","name","value"]]

    os.makedirs(OUT_DIR, exist_ok=True)
    world_map.to_json(DST, orient="records")

    print(f"[PASS] Wrote {DST} for year={year}, hs6={sel_hs6}, metric={metric}")
    print(world_map.head())

if __name__ == "__main__":
    main()
