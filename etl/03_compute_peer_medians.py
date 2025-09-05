import os, json
import pandas as pd
import pycountry
import numpy as np

DETAILED_PATHS = [
    "data/parquet/BACI_HS22_Y2022_V202501/data.parquet",
    "data/parquet/BACI_HS22_Y2023_V202501/data.parquet",
]
PEER_FILE = "data/ref/peer_groups.json"
OUT_PATH = "data/out/peer_medians_statistical.parquet"

COUNTRY = "CZE"  # our focal exporter
def num_to_iso3(n):
    rec = pycountry.countries.get(numeric=f"{int(n):03d}")
    return rec.alpha_3 if rec else None

def to_num(x):
    return pd.to_numeric(x, errors="coerce")

def main():
    # 0) peers
    if not os.path.isfile(PEER_FILE):
        raise FileNotFoundError(f"Missing {PEER_FILE}")
    with open(PEER_FILE, "r") as f:
        peers_by_country = json.load(f)
    peers = set(peers_by_country.get(COUNTRY, []))
    if not peers:
        raise RuntimeError(f"No peers found for {COUNTRY} in {PEER_FILE}")

    # 1) load detailed
    dfs = []
    for p in DETAILED_PATHS:
        if not os.path.isfile(p):
            raise FileNotFoundError(f"Missing detailed file: {p}")
        df = pd.read_parquet(p, columns=["year","exporter","importer","hs6","value_usd"])
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)

    # 2) normalize
    df["value_usd"] = to_num(df["value_usd"])
    df["year"] = to_num(df["year"]).astype("int32", copy=False)
    # map country codes
    df["exporter_iso3"] = df["exporter"].map(num_to_iso3)
    df["partner_iso3"]  = df["importer"].map(num_to_iso3)
    # hs6 → zero-padded string
    df["hs6"] = df["hs6"].astype("Int64").astype("string").str.pad(6, fillchar="0")

    # 3) total partner imports per (y,hs6,partner)
    imp_total = (
        df.groupby(["year","hs6","partner_iso3"], as_index=False)
          .agg(import_partner_total=("value_usd", "sum"))
    )

    # 4) peer exports to partner per (y,hs6,partner,exporter)
    peer_flows = df[df["exporter_iso3"].isin(peers)].copy()
    peer_by_exp = (
        peer_flows.groupby(["year","hs6","partner_iso3","exporter_iso3"], as_index=False)["value_usd"].sum()
    )

    # 5) compute each peer's share = value / partner import total
    peer_by_exp = peer_by_exp.merge(imp_total, on=["year","hs6","partner_iso3"], how="left")
    peer_by_exp["peer_share"] = peer_by_exp["value_usd"] / peer_by_exp["import_partner_total"].replace({0:np.nan})

    # 6) median across peers per (y,hs6,partner)
    med = (
        peer_by_exp
        .groupby(["year","hs6","partner_iso3"])["peer_share"]
        .median()
        .reset_index(name="median_peer_share")
    )

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    med.to_parquet(OUT_PATH, index=False)
    print(f"[PASS] Wrote {OUT_PATH} with {len(med):,} rows")
    print(med.head(5))

if __name__ == "__main__":
    main()
