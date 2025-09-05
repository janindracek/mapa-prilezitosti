#!/usr/bin/env python3
"""
28_build_top_signals.py

Produce a compact table of TOP signals per country for the latest year:
- S1:  YoY_export_change
- S2:  YoY_partner_share_change
- 3a:  Peer_gap_opportunity
- 3b:  Peer_gap_matching
- 3c:  Peer_gap_human

Inputs
- data/out/metrics_enriched.parquet
    cols: year, hs6, partner_iso3,
          YoY_export_change, YoY_partner_share_change, podil_cz_na_importu, ...
- data/out/metrics_peer_medians.parquet
    cols: year, hs6, partner_iso3, method, k, median_peer_share, delta_vs_peer
- data/config.yaml  (optional; thresholds; script has safe fallbacks)

Output
- data/out/top_signals.parquet
    cols: country_iso3, year, type, hs6, partner_iso3, intensity, value, method, k

Notes
- No new deps. Uses pandas and stdlib only. Safe fallbacks for thresholds.
- We rank by `intensity` and keep TOP 3 per type, per country.
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd
import argparse

P_METRICS   = Path("data/out/metrics_enriched.parquet")
P_MEDIANS   = Path("data/out/metrics_peer_medians.parquet")
P_CONFIG    = Path("data/config.yaml")
P_OUT       = Path("data/out/top_signals.parquet")

# ---------- tiny config loader with safe fallbacks ----------
def load_thresholds() -> dict:
    # Defaults if YAML missing/keys not found
    th = {
        "S1": 0.10,  # YoY export change min
        "S2": 0.10,  # YoY partner-share change min
        "PEER_GAP": 0.0,  # minimum negative gap magnitude to consider (abs)
    }
    try:
        import yaml  # PyYAML is usually present; if not, we just keep defaults
        if P_CONFIG.is_file():
            cfg = yaml.safe_load(P_CONFIG.read_text(encoding="utf-8"))
            # try some common keys; keep robust
            th["S1"] = float(
                cfg.get("S1")
                or cfg.get("S1_YOY_EXPORT_MIN")
                or cfg.get("S1_REL_GAP_MIN")
                or th["S1"]
            )
            th["S2"] = float(
                cfg.get("S2")
                or cfg.get("S2_YOY_PARTNER_SHARE_MIN")
                or th["S2"]
            )
            th["PEER_GAP"] = float(
                cfg.get("S3")
                or cfg.get("S1")  # some setups reuse S1 for gap filter
                or th["PEER_GAP"]
            )
    except Exception:
        pass
    return th

# ---------- helpers ----------
TYPE_ORDER = [
    "YoY_export_change",
    "YoY_partner_share_change",
    "Peer_gap_opportunity",
    "Peer_gap_matching",
    "Peer_gap_human",
]

def method_to_peer_type(method: str) -> str:
    m = (method or "").lower()
    if "opportunity" in m:
        return "Peer_gap_opportunity"
    if "hs2_shares" in m or "kmeans_cosine_hs2_shares" in m:
        return "Peer_gap_matching"
    if "human" in m:
        return "Peer_gap_human"
    return "Peer_gap_below_median"  # not exported

def top_k_per_type(df: pd.DataFrame, k: int) -> pd.DataFrame:
    """Keep top-k by intensity within each (country,type)."""
    if df.empty:
        return df
    return (
        df.sort_values(["country_iso3", "type", "intensity"], ascending=[True, True, False])
          .groupby(["country_iso3", "type"], as_index=False)
          .head(k)
          .reset_index(drop=True)
    )

def ensure_top_n(filtered: pd.DataFrame, fallback: pd.DataFrame, n: int) -> pd.DataFrame:
    """
    For each (country_iso3, type), keep top-n by intensity.
    If filtered rows are < n, top up from fallback (same type) excluding already selected rows.
    Assumes both frames have the same schema and 'intensity' present.
    """
    if filtered.empty and fallback.empty:
        return filtered

    # sort both pools by intensity desc for deterministic head(n)
    f_sorted = (
        filtered.sort_values(["country_iso3", "type", "intensity"], ascending=[True, True, False])
    )
    fb_sorted = (
        fallback.sort_values(["country_iso3", "type", "intensity"], ascending=[True, True, False])
    )

    out_blocks = []
    # compute desired groups from union of keys present in either frame
    keys = (
        pd.concat([
            f_sorted[["country_iso3", "type"]],
            fb_sorted[["country_iso3", "type"]]
        ], ignore_index=True)
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )

    for country_iso3, typ in keys:
        f_grp = f_sorted[(f_sorted["country_iso3"] == country_iso3) & (f_sorted["type"] == typ)]
        need = n - len(f_grp)
        if need <= 0:
            out_blocks.append(f_grp.head(n))
            continue
        # take from fallback of the same type, excluding already selected (by hs6+partner)
        fb_grp = fb_sorted[(fb_sorted["country_iso3"] == country_iso3) & (fb_sorted["type"] == typ)].copy()
        # a simpler duplicate filter using merge anti-join
        if not f_grp.empty:
            fb_grp = fb_grp.merge(
                f_grp[["hs6", "partner_iso3"]].assign(_sel=1),
                on=["hs6", "partner_iso3"], how="left"
            )
            fb_grp = fb_grp[fb_grp["_sel"].isna()].drop(columns=["_sel"])
        out_blocks.append(pd.concat([f_grp, fb_grp.head(max(0, need))], ignore_index=True))

    if not out_blocks:
        return filtered
    return pd.concat(out_blocks, ignore_index=True)

# ---------- main ----------
def main(top_n: int = 3, fill_under_threshold: bool = False) -> None:
    if not P_METRICS.is_file():
        raise FileNotFoundError(f"Missing {P_METRICS}")
    if not P_MEDIANS.is_file():
        raise FileNotFoundError(f"Missing {P_MEDIANS}")

    th = load_thresholds()

    # Base metrics
    me = pd.read_parquet(P_METRICS)
    latest = int(me["year"].max())
    me = me[me["year"] == latest].copy()

    # S1: YoY export
    s1 = me.loc[me["YoY_export_change"].notna()].copy()
    s1 = s1[s1["YoY_export_change"] >= th["S1"]]
    s1 = s1.assign(
        country_iso3=s1["partner_iso3"],
        type="YoY_export_change",
        value=s1["export_cz_to_partner"],
        intensity=s1["YoY_export_change"].abs(),
        method=None, k=None,
    )[["country_iso3","year","type","hs6","partner_iso3","intensity","value","method","k"]]

    # S2: YoY partner share
    s2 = me.loc[me["YoY_partner_share_change"].notna()].copy()
    s2 = s2[s2["YoY_partner_share_change"] >= th["S2"]]
    s2 = s2.assign(
        country_iso3=s2["partner_iso3"],
        type="YoY_partner_share_change",
        value=s2["export_cz_to_partner"],
        intensity=s2["YoY_partner_share_change"].abs(),
        method=None, k=None,
    )[["country_iso3","year","type","hs6","partner_iso3","intensity","value","method","k"]]

    # Peer gaps (use precomputed medians for all methods incl. human)
    pm = pd.read_parquet(P_MEDIANS)
    pm = pm[pm["year"] == latest].copy()
    pm["type"] = pm["method"].map(method_to_peer_type)
    pm = pm[pm["type"].isin(TYPE_ORDER)]  # keep only the three we expose
    pm["intensity"] = (pm["delta_vs_peer"] * -1.0)  # negative gap -> positive intensity
    pm = pm[pm["intensity"] >= abs(th["PEER_GAP"])]


    # standardize columns (keep both partner_iso3 and country_iso3)
    pkeep = pm.copy()
    pkeep["country_iso3"] = pkeep["partner_iso3"]
    pkeep["value"] = pkeep["delta_vs_peer"]
    pkeep = pkeep[["country_iso3","year","type","hs6","partner_iso3","intensity","value","method","k"]]

    # Unfiltered pools (for optional fill):
    s1_all = me.assign(
        country_iso3=me["partner_iso3"],
        type="YoY_export_change",
        value=me["export_cz_to_partner"],
        intensity=me["YoY_export_change"].abs(),
        method=None, k=None,
    )[["country_iso3","year","type","hs6","partner_iso3","intensity","value","method","k"]]

    s2_all = me.assign(
        country_iso3=me["partner_iso3"],
        type="YoY_partner_share_change",
        value=me["export_cz_to_partner"],
        intensity=me["YoY_partner_share_change"].abs(),
        method=None, k=None,
    )[["country_iso3","year","type","hs6","partner_iso3","intensity","value","method","k"]]

    pm_all = pd.read_parquet(P_MEDIANS)
    pm_all = pm_all[pm_all["year"] == latest].copy()
    pm_all["type"] = pm_all["method"].map(method_to_peer_type)
    pm_all = pm_all[pm_all["type"].isin(TYPE_ORDER)]
    pm_all["intensity"] = (pm_all["delta_vs_peer"] * -1.0)
    pkeep_all = pm_all.copy()
    pkeep_all["country_iso3"] = pkeep_all["partner_iso3"]
    pkeep_all["value"] = pkeep_all["delta_vs_peer"]
    pkeep_all = pkeep_all[["country_iso3","year","type","hs6","partner_iso3","intensity","value","method","k"]]

    # Combine filtered and (optionally) fallback pools
    filtered_rows = pd.concat([s1, s2, pkeep], ignore_index=True)
    if fill_under_threshold:
      fallback_rows = pd.concat([s1_all, s2_all, pkeep_all], ignore_index=True)
      top = ensure_top_n(filtered_rows, fallback_rows, top_n)
    else:
      top = top_k_per_type(filtered_rows, top_n)

    P_OUT.parent.mkdir(parents=True, exist_ok=True)
    top.to_parquet(P_OUT, index=False)
    print(f"✅ Wrote TOP signals to {P_OUT} | rows={len(top)} | latest_year={latest} | N={top_n} per type")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-n", type=int, default=3, help="Top N per type per country (default 3)")
    ap.add_argument("--fill-under-threshold", action="store_true", help="Fill missing slots up to N using under-threshold candidates")
    args = ap.parse_args()
    main(top_n=args.top_n, fill_under_threshold=args.fill_under_threshold)