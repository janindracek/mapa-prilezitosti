#!/usr/bin/env python3
"""
27_compute_peer_medians.py

Výpočet mediánů podílu CZ na importu (podil_cz_na_importu) napříč peers pro všechny peer skupiny
a výpočet delta_vs_peer = share(target) - median(peers).

Vstupy:
- data/out/metrics_enriched.parquet
  nutné sloupce: year, hs6, partner_iso3, podil_cz_na_importu
- data/out/peer_groups.parquet
  sloupce: iso3, cluster, method, k, year   (obsahuje matching + opportunity)
- data/out/peer_groups_human.parquet
  sloupce: iso3, cluster, (method), (k), year

Výstup:
- data/out/metrics_peer_medians.parquet
  sloupce: year, hs6, partner_iso3, method, k, median_peer_share, delta_vs_peer

Poznámky:
- Počítáno pro nejnovější rok v metrics_enriched.
- U human skupiny, pokud chybí k či method, doplní se defaulty (k = počet clusterů, method = 'human_geo_econ_v2').
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd

METRICS = Path("data/out/metrics_enriched.parquet")
PG_STAT = Path("data/out/peer_groups.parquet")
PG_HUM  = Path("data/out/peer_groups_human.parquet")
OUT     = Path("data/out/metrics_peer_medians.parquet")

def _require_cols(df: pd.DataFrame, need: set, name: str):
    miss = need - set(df.columns)
    if miss:
        raise ValueError(f"{name} missing columns: {sorted(miss)}")

def _compute_for_pg(cur: pd.DataFrame, pg: pd.DataFrame, method: str, k: int | None, year: int) -> pd.DataFrame:
    """
    cur: rows for given year, cols: hs6, partner_iso3, podil_cz_na_importu
    pg : rows for given year, cols: iso3, cluster
    → returns cols: year, hs6, partner_iso3, method, k, median_peer_share, delta_vs_peer
    """
    if pg.empty:
        return pd.DataFrame(columns=["year","hs6","partner_iso3","method","k","median_peer_share","delta_vs_peer"])

    # membership per cluster
    m = pg[["iso3","cluster"]].dropna().drop_duplicates().copy()
    # all (target, peer) pairs in the same cluster, excluding self
    pairs = m.merge(m, on="cluster", suffixes=("_t","_p"))
    pairs = pairs[pairs["iso3_t"] != pairs["iso3_p"]]

    # attach peer shares by hs6
    peers_shares = pairs.merge(
        cur[["hs6","partner_iso3","podil_cz_na_importu"]],
        left_on="iso3_p", right_on="partner_iso3", how="left"
    )
    peers_shares = peers_shares.dropna(subset=["podil_cz_na_importu"])

    if peers_shares.empty:
        return pd.DataFrame(columns=["year","hs6","partner_iso3","method","k","median_peer_share","delta_vs_peer"])

    # median over peers per (target country, hs6)
    med = (
        peers_shares
        .groupby(["iso3_t","hs6"], as_index=False)["podil_cz_na_importu"].median()
        .rename(columns={"iso3_t":"partner_iso3","podil_cz_na_importu":"median_peer_share"})
    )

    # join target's own share
    cur_tgt = cur[["partner_iso3","hs6","podil_cz_na_importu"]].rename(columns={"podil_cz_na_importu":"target_share"})
    out = med.merge(cur_tgt, on=["partner_iso3","hs6"], how="left")

    # compute delta
    out["delta_vs_peer"] = out["target_share"] - out["median_peer_share"]
    out["year"] = year
    out["method"] = method
    out["k"] = k
    return out[["year","hs6","partner_iso3","method","k","median_peer_share","delta_vs_peer"]]

def main():
    if not METRICS.is_file():
        raise FileNotFoundError(f"Missing {METRICS}")
    df = pd.read_parquet(METRICS)
    _require_cols(df, {"year","hs6","partner_iso3","podil_cz_na_importu"}, "metrics_enriched")

    latest_year = int(df["year"].max())
    cur = df[df["year"] == latest_year][["hs6","partner_iso3","podil_cz_na_importu"]].copy()

    blocks: list[pd.DataFrame] = []

    # --- statistical peer groups (matching + opportunity) ---
    if PG_STAT.is_file():
        pg_all = pd.read_parquet(PG_STAT)
        _require_cols(pg_all, {"iso3","cluster","method","k","year"}, "peer_groups.parquet")
        pg_all = pg_all[pg_all["year"] == latest_year].copy()
        if not pg_all.empty:
            combos = (
                pg_all[["method","k"]]
                .drop_duplicates()
                .sort_values(["method","k"])
                .to_dict("records")
            )
            for c in combos:
                method = str(c["method"])
                k = int(c["k"])
                pg = pg_all[(pg_all["method"] == method) & (pg_all["k"] == k)][["iso3","cluster"]].copy()
                blk = _compute_for_pg(cur, pg, method=method, k=k, year=latest_year)
                if not blk.empty:
                    blocks.append(blk)

    # --- human peer groups ---
    if PG_HUM.is_file():
        ph = pd.read_parquet(PG_HUM)
        _require_cols(ph, {"iso3","cluster","year"}, "peer_groups_human.parquet")
        ph = ph[ph["year"] == latest_year].copy()
        if not ph.empty:
            method = str(ph["method"].iloc[0]) if "method" in ph.columns and pd.notna(ph["method"]).any() else "human_geo_econ_v2"
            k = int(ph["k"].iloc[0]) if "k" in ph.columns and pd.notna(ph["k"]).any() else int(ph["cluster"].nunique())
            pg = ph[["iso3","cluster"]].copy()
            blk = _compute_for_pg(cur, pg, method=method, k=k, year=latest_year)
            if not blk.empty:
                blocks.append(blk)

    if not blocks:
        # write empty schema for predictability
        empty = pd.DataFrame(columns=["year","hs6","partner_iso3","method","k","median_peer_share","delta_vs_peer"])
        empty.to_parquet(OUT, index=False)
        print(f"⚠️ No medians computed. Wrote empty schema to {OUT}")
        return

    out = pd.concat(blocks, ignore_index=True)
    # basic sanity
    assert out["year"].eq(latest_year).all()
    assert out["hs6"].astype(str).str.len().ge(1).all()
    assert out["partner_iso3"].astype(str).str.len().eq(3).all()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT, index=False)
    print(f"✅ Wrote {len(out)} rows to {OUT} for year={latest_year} across {out['method'].nunique()} methods.")

if __name__ == "__main__":
    main()