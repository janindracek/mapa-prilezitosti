#!/usr/bin/env python3
"""
ETL stage 03b — compute REAL peer-group medians (M3).

Two methods only (opportunity retired in M3 v1; the dead "geographic" stub is
gone):
  - trade_structure : k-means cosine on HS2 import-share profiles (frozen
                      membership in peer_groups_hs2.parquet; descriptor in
                      peer_groups_hs2_explained.csv)
  - human           : expert-curated geographic/economic groups
                      (peer_groups_human.parquet / peer_groups_human_explained.csv)

The median is HONEST (no 0.85/1.15 scaling). For each (year, hs6, target market
t) and method m:

    peer_median_share = median over { p in cluster_m(t), p != t, p != CZE }
                        of podil_cz_na_importu(year, hs6, p)

i.e. the peer group is the TARGET market's cluster (leave-one-out on t; CZE
excluded since CZ does not export to itself). Mirrors the established honest
computation in etl/archive/27_compute_peer_medians.py, generalized to all years
and with CZE removed from peer sets.

Input : data/out/metrics.parquet (all-country coverage from M4a)
        data/out/peer_groups_hs2.parquet, data/out/peer_groups_human.parquet
Output: data/out/peer_medians_comprehensive.parquet
        cols: year, hs6, partner_iso3, method, peer_median_share,
              peer_countries (json), peer_count
"""

import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import country_ref as cr

METRICS = "data/out/metrics.parquet"
OUTPUT = "data/out/peer_medians_comprehensive.parquet"

# (method_id, membership parquet). method_id must match etl/06b's
# method->signal-type map and etl/04b's column suffixes.
METHODS = [
    ("trade_structure", "data/out/peer_groups_hs2.parquet"),
    ("human", "data/out/peer_groups_human.parquet"),
]

CZ = cr.CZ_ISO3  # "CZE"


def load_metrics() -> pd.DataFrame:
    if not os.path.isfile(METRICS):
        raise FileNotFoundError(f"Missing {METRICS}. Run etl/01 + etl/02 first.")
    df = pd.read_parquet(METRICS, columns=["year", "hs6", "partner_iso3", "podil_cz_na_importu"])
    return df


def load_membership(path: str) -> pd.DataFrame:
    """iso3 -> cluster, with CZE removed (CZ is never its own peer market)."""
    pg = pd.read_parquet(path)
    if "iso3" not in pg.columns or "cluster" not in pg.columns:
        raise ValueError(f"{path} must have iso3 + cluster columns; got {list(pg.columns)}")
    m = pg[["iso3", "cluster"]].dropna().drop_duplicates()
    m = m[m["iso3"] != CZ]
    return m.reset_index(drop=True)


def compute_method(metrics: pd.DataFrame, membership: pd.DataFrame, method_id: str) -> pd.DataFrame:
    # Peer membership shown to the user: each target's co-cluster members (excl. self).
    members_by_cluster = membership.groupby("cluster")["iso3"].apply(list).to_dict()
    cluster_of = dict(zip(membership["iso3"], membership["cluster"]))

    # (target, peer) pairs within a cluster, excluding self → leave-one-out.
    pairs = membership.merge(membership, on="cluster", suffixes=("_t", "_p"))
    pairs = pairs[pairs["iso3_t"] != pairs["iso3_p"]][["iso3_t", "iso3_p"]]

    out_blocks = []
    for year in sorted(metrics["year"].unique()):
        cur = metrics[metrics["year"] == year][["hs6", "partner_iso3", "podil_cz_na_importu"]]
        # attach each peer's CZ-share for every hs6, drop markets that didn't import it
        ps = pairs.merge(cur, left_on="iso3_p", right_on="partner_iso3", how="inner")
        ps = ps.dropna(subset=["podil_cz_na_importu"])
        if ps.empty:
            continue
        med = (
            ps.groupby(["iso3_t", "hs6"], as_index=False)["podil_cz_na_importu"]
              .median()
              .rename(columns={"iso3_t": "partner_iso3", "podil_cz_na_importu": "peer_median_share"})
        )
        med["year"] = int(year)
        med["method"] = method_id
        out_blocks.append(med)

    if not out_blocks:
        return pd.DataFrame(columns=["year", "hs6", "partner_iso3", "method",
                                     "peer_median_share", "peer_countries", "peer_count"])

    out = pd.concat(out_blocks, ignore_index=True)

    # Peer list/count per target (constant across hs6): co-cluster members minus self.
    peer_list = {
        t: [c for c in members_by_cluster.get(cluster_of.get(t), []) if c != t]
        for t in out["partner_iso3"].unique()
    }
    out["peer_countries"] = out["partner_iso3"].map(lambda t: json.dumps(peer_list.get(t, [])))
    out["peer_count"] = out["partner_iso3"].map(lambda t: len(peer_list.get(t, [])))
    return out[["year", "hs6", "partner_iso3", "method",
                "peer_median_share", "peer_countries", "peer_count"]]


def main():
    print("=== M3: computing REAL peer medians (trade_structure + human) ===")
    metrics = load_metrics()
    print(f"Loaded metrics: {len(metrics):,} rows, {metrics['partner_iso3'].nunique()} importers")

    blocks = []
    for method_id, path in METHODS:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Missing membership {path} for method {method_id}")
        membership = load_membership(path)
        n_clusters = membership["cluster"].nunique()
        print(f"  {method_id}: {len(membership)} markets in {n_clusters} clusters (CZE excluded)")
        blk = compute_method(metrics, membership, method_id)
        print(f"    -> {len(blk):,} (year,hs6,target) medians")
        blocks.append(blk)

    out = pd.concat(blocks, ignore_index=True)
    Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUTPUT, index=False)

    print(f"[PASS] Wrote {OUTPUT}: {len(out):,} rows")
    for method_id, _ in METHODS:
        sub = out[out["method"] == method_id]
        print(f"  {method_id}: {len(sub):,} rows, median peer_count={int(sub['peer_count'].median()) if len(sub) else 0}")


if __name__ == "__main__":
    main()
