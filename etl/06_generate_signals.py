# etl/41_signals_with_peer.py
import os
import json
import yaml
import pandas as pd
import numpy as np

METRICS = "data/out/metrics_enriched.parquet"
DST = "data/out/signals.json"
CFG = "data/config.yaml"

def load_thresholds() -> dict:
    """
    Load thresholds from data/config.yaml with safe defaults.
    """
    defaults = {
        "MIN_EXPORT_USD": 100_000,
        "MIN_IMPORT_USD": 5_000_000,
        "S1_REL_GAP_MIN": 0.20,
        "S2_YOY_THRESHOLD": 0.30,
        "S3_YOY_SHARE_THRESHOLD": 0.20,
        "MAX_TOTAL": 10,
        "MAX_PER_TYPE": 4,
    }
    if not os.path.isfile(CFG):
        return defaults
    try:
        with open(CFG, "r") as f:
            cfg = yaml.safe_load(f) or {}
        th = {**defaults, **(cfg.get("thresholds") or {})}
        return th
    except Exception:
        return defaults

def shortlist(df: pd.DataFrame) -> list[dict]:
    TH = load_thresholds()
    MIN_EXPORT_USD   = TH["MIN_EXPORT_USD"]
    MIN_IMPORT_USD   = TH["MIN_IMPORT_USD"]
    S1_REL_GAP_MIN   = TH["S1_REL_GAP_MIN"]
    S2_YOY_THRESHOLD = TH["S2_YOY_THRESHOLD"]
    S3_YOY_SHARE_THRESHOLD = TH["S3_YOY_SHARE_THRESHOLD"]
    MAX_TOTAL = TH["MAX_TOTAL"]
    MAX_PER_TYPE = TH["MAX_PER_TYPE"]

    latest = int(df["year"].max())
    cur = df[df["year"] == latest].copy()

    # significance filter
    cur = cur[(cur["export_cz_to_partner"] >= MIN_EXPORT_USD) | (cur["import_partner_total"] >= MIN_IMPORT_USD)]

    items: list[dict] = []

    # --- Signal 1: CZ below peer median (relative gap) ---
    if "median_peer_share" in cur.columns and "podil_cz_na_importu" in cur.columns:
        s1 = cur[["year","hs6","partner_iso3","podil_cz_na_importu","median_peer_share"]].dropna().copy()
        s1 = s1[s1["median_peer_share"] > 0]
        if not s1.empty:
            s1["rel_gap"] = (s1["median_peer_share"] - s1["podil_cz_na_importu"]) / s1["median_peer_share"]
            s1 = s1[s1["rel_gap"] >= S1_REL_GAP_MIN]
            s1 = s1.sort_values("rel_gap", ascending=False).head(MAX_PER_TYPE)
            for _, r in s1.iterrows():
                items.append({
                    "type": "Peer_gap_below_median",
                    "year": int(r["year"]),
                    "hs6": str(r["hs6"]),
                    "partner_iso3": r["partner_iso3"],
                    "intensity": float(r["rel_gap"]),
                    "value": float(r["podil_cz_na_importu"]),
                    "peer_median": float(r["median_peer_share"]),
                })

    # --- Signal 2: YoY export change ---
    if "YoY_export_change" in cur.columns:
        s2 = cur[["year","hs6","partner_iso3","export_cz_to_partner","YoY_export_change"]].dropna(subset=["YoY_export_change"]).copy()
        if not s2.empty:
            s2["intensity"] = s2["YoY_export_change"].abs()
            s2 = s2[s2["intensity"] >= S2_YOY_THRESHOLD]
            s2 = s2.sort_values("intensity", ascending=False).head(MAX_PER_TYPE)
            for _, r in s2.iterrows():
                items.append({
                    "type": "YoY_export_change",
                    "year": int(r["year"]),
                    "hs6": str(r["hs6"]),
                    "partner_iso3": r["partner_iso3"],
                    "intensity": float(r["intensity"]),
                    "value": float(r["export_cz_to_partner"]),
                    "yoy": float(r["YoY_export_change"]),
                })

    # --- Signal 3: YoY partner-share change ---
    if "YoY_partner_share_change" in cur.columns:
        s3 = cur[["year","hs6","partner_iso3","partner_share_in_cz_exports","YoY_partner_share_change","export_cz_to_partner"]].dropna(subset=["YoY_partner_share_change"]).copy()
        if not s3.empty:
            s3["intensity"] = s3["YoY_partner_share_change"].abs()
            s3 = s3[s3["intensity"] >= S3_YOY_SHARE_THRESHOLD]
            s3 = s3.sort_values("intensity", ascending=False).head(MAX_PER_TYPE)
            for _, r in s3.iterrows():
                items.append({
                    "type": "YoY_partner_share_change",
                    "year": int(r["year"]),
                    "hs6": str(r["hs6"]),
                    "partner_iso3": r["partner_iso3"],
                    "intensity": float(r["intensity"]),
                    "value": float(r["partner_share_in_cz_exports"]),
                    "yoy": float(r["YoY_partner_share_change"]),
                })

    # Global sort & cap
    items = sorted(items, key=lambda x: x["intensity"], reverse=True)[:MAX_TOTAL]
    return items

def main():
    if not os.path.isfile(METRICS):
        raise FileNotFoundError(f"Missing {METRICS}. Run 26_merge_peer_into_metrics.py first.")
    df = pd.read_parquet(METRICS)
    items = shortlist(df)

    os.makedirs(os.path.dirname(DST), exist_ok=True)
    with open(DST, "w") as f:
        json.dump(items, f, indent=2)

    src = CFG if os.path.isfile(CFG) else "defaults"
    print(f"[PASS] Wrote {DST} with {len(items)} signals (thresholds from {src})")
    for it in items[:5]:
        print(it)

if __name__ == "__main__":
    main()