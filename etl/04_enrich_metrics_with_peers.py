import os
import pandas as pd
import numpy as np

METRICS = "data/out/metrics.parquet"
PEERS   = "data/out/peer_medians_statistical.parquet"
OUT     = "data/out/metrics_enriched.parquet"

def main():
    if not os.path.isfile(METRICS):
        raise FileNotFoundError(f"Missing {METRICS}")
    if not os.path.isfile(PEERS):
        raise FileNotFoundError(f"Missing {PEERS}")

    m = pd.read_parquet(METRICS)
    p = pd.read_parquet(PEERS)

    # Merge on keys
    df = m.merge(p, on=["year","hs6","partner_iso3"], how="left")

    # Compute delta vs peer (safe where both present)
    df["delta_vs_peer"] = df["podil_cz_na_importu"] - df["median_peer_share"]

    # Save
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    df.to_parquet(OUT, index=False)

    # Tiny validation summary
    nonnull = df["median_peer_share"].notna().sum()
    total = len(df)
    print(f"[PASS] Wrote {OUT} with {total:,} rows; median_peer_share non-null: {nonnull:,}")
    print(df[["year","hs6","partner_iso3","podil_cz_na_importu","median_peer_share","delta_vs_peer"]].head(5))

if __name__ == "__main__":
    main()
