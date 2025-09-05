import os, json
import pandas as pd

ENRICHED = "data/out/metrics_enriched.parquet"
BASIC    = "data/out/metrics.parquet"
OUT_DIR  = "data/out/ui_shapes"
DST      = os.path.join(OUT_DIR, "controls.json")

def main():
    src = ENRICHED if os.path.isfile(ENRICHED) else BASIC
    if not os.path.isfile(src):
        raise FileNotFoundError(f"Missing metrics file: {src}")
    df = pd.read_parquet(src)

    countries = sorted(df["partner_iso3"].dropna().unique().tolist())
    years     = sorted([int(y) for y in df["year"].dropna().unique().tolist()])

    # expose original metrics + new peer metrics
    metrics = [
        "podil_cz_na_importu",
        "YoY_export_change",
        "partner_share_in_cz_exports",
        "YoY_partner_share_change",
        # new peer-driven ones
        "median_peer_share",
        "delta_vs_peer"
    ]

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(DST, "w") as f:
        json.dump({"countries": countries, "years": years, "metrics": metrics}, f, indent=2)

    print(f"[PASS] Wrote {DST}")
    print({"countries": countries[:5], "years": years, "metrics": metrics})

if __name__ == "__main__":
    main()
