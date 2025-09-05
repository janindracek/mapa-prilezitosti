#!/usr/bin/env python3
"""
30_human_peer_medians.py

Compute median CZ import share for each (target country, hs6, year) based on the
'geographical/economic' human peer groups.

Inputs:
- data/out/peer_groups_human.parquet   # columns: iso3, cluster, method, k, year
- data/out/metrics_enriched.parquet    # must include: year, hs6, partner_iso3, podil_cz_na_importu

Output:
- data/out/human_peer_medians.parquet  # columns: country_iso3, hs6, year, median_peer_share_human
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd

HUMAN_PG = Path("data/out/peer_groups_human.parquet")
ENRICHED = Path("data/out/metrics_enriched.parquet")
OUT_PATH = Path("data/out/human_peer_medians.parquet")

def main(latest_year: int = 2023) -> None:
    if not HUMAN_PG.is_file():
        raise FileNotFoundError(f"Missing {HUMAN_PG}")
    if not ENRICHED.is_file():
        raise FileNotFoundError(f"Missing {ENRICHED}")

    pg = pd.read_parquet(HUMAN_PG)
    pg = pg[pg["year"] == latest_year].copy()
    if pg.empty:
        raise ValueError(f"No human peer rows for year {latest_year} in {HUMAN_PG}")

    # Sanity
    need_pg = {"iso3","cluster","year"}
    miss_pg = need_pg - set(pg.columns)
    if miss_pg:
        raise ValueError(f"{HUMAN_PG} missing columns: {sorted(miss_pg)}")

    df = pd.read_parquet(ENRICHED)
    # Required columns in enriched
    need_sub = {"year","hs6","partner_iso3","podil_cz_na_importu"}
    miss_sub = need_sub - set(df.columns)
    if miss_sub:
        raise ValueError(f"{ENRICHED} missing columns: {sorted(miss_sub)}")

    df = df[df["year"] == latest_year].copy()
    if df.empty:
        raise ValueError(f"No rows for year {latest_year} in {ENRICHED}")

    # For each target country, find its peers from the same human cluster (excluding itself),
    # then compute median of podil_cz_na_importu across those peers per HS6.
    # Build a mapping: country_iso3 -> list of peer iso3
    clusters = pg.groupby("cluster")["iso3"].apply(list).to_dict()

    # Reverse index: country -> cluster
    country_to_cluster = pg.set_index("iso3")["cluster"].to_dict()

    out_blocks = []
    # Iterate over all countries that appear in metrics for this year
    countries = df["partner_iso3"].dropna().unique().tolist()
    for c in countries:
        cluster = country_to_cluster.get(c)
        if cluster is None:
            # Country not present in human peers for this year -> skip
            continue
        peers = [x for x in clusters.get(cluster, []) if x != c]
        if not peers:
            continue
        peers_df = df[df["partner_iso3"].isin(peers)][["hs6","podil_cz_na_importu"]].copy()
        if peers_df.empty:
            continue
        med = peers_df.groupby("hs6", as_index=False)["podil_cz_na_importu"].median()
        med = med.rename({"podil_cz_na_importu": "median_peer_share_human"}, axis=1)
        med["country_iso3"] = c
        med["year"] = latest_year
        out_blocks.append(med)

    if not out_blocks:
        # produce an empty file with the right schema, for predictable downstream behavior
        empty = pd.DataFrame(columns=["country_iso3","hs6","year","median_peer_share_human"])
        empty.to_parquet(OUT_PATH, index=False)
        print(f"⚠️ No medians computed. Wrote empty schema to {OUT_PATH}")
        return

    out = pd.concat(out_blocks, ignore_index=True)
    # Final sanity
    assert out["country_iso3"].str.len().eq(3).all()
    assert out["hs6"].astype(str).str.len().ge(1).all()
    assert out["year"].eq(latest_year).all()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT_PATH, index=False)
    print(f"✅ Wrote {len(out)} rows to {OUT_PATH}")

if __name__ == "__main__":
    main(latest_year=2023)