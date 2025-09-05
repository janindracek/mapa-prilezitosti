import os, json
import pandas as pd
import numpy as np

INPUT = "data/out/metrics.parquet"
OUTPUT = "data/out/signals.json"

# Tunables
MIN_EXPORT_USD   = 100_000
MIN_IMPORT_USD   = 5_000_000
S2_YOY_THRESHOLD = 0.30
S3_YOY_SHARE_THRESHOLD = 0.20

MAX_TOTAL = 10
MAX_PER_TYPE = 4

def shortlist_signals(df: pd.DataFrame) -> list[dict]:
    # latest year
    year = int(df["year"].max())
    cur = df[df["year"] == year].copy()

    # Basic significance filters
    cur = cur[(cur["export_cz_to_partner"] >= MIN_EXPORT_USD) | (cur["import_partner_total"] >= MIN_IMPORT_USD)]

    items = []

    # --- Signal 2: YoY export change ---
    s2 = cur[["year","hs6","partner_iso3","export_cz_to_partner","YoY_export_change"]].dropna(subset=["YoY_export_change"]).copy()
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
            "yoy": float(r["YoY_export_change"])
        })

    # --- Signal 3: YoY partner-share change ---
    s3 = cur[["year","hs6","partner_iso3","partner_share_in_cz_exports","YoY_partner_share_change","export_cz_to_partner"]].dropna(subset=["YoY_partner_share_change"]).copy()
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
            "yoy": float(r["YoY_partner_share_change"])
        })

    # Global sort by intensity and cut to MAX_TOTAL
    items = sorted(items, key=lambda x: x["intensity"], reverse=True)[:MAX_TOTAL]
    return items

def main():
    df = pd.read_parquet(INPUT)
    signals = shortlist_signals(df)

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(signals, f, indent=2)

    print(f"[PASS] Wrote {OUTPUT} with {len(signals)} signals")
    # tiny preview
    for it in signals[:5]:
        print(it)

if __name__ == "__main__":
    main()
