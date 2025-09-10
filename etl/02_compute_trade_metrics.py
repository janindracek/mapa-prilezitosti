import os
import pandas as pd
import numpy as np

INPUT = "data/out/fact_base.parquet"
OUTPUT = "data/out/metrics.parquet"

def safe_div(numer, denom):
    return numer / denom.where(denom != 0)

def main():
    df = pd.read_parquet(INPUT)
    df.sort_values(["hs6","partner_iso3","year"], inplace=True)

    # 1) Share of imports
    df["podil_cz_na_importu"] = safe_div(df["export_cz_to_partner"], df["import_partner_total"])

    # 2) YoY export change
    df["prev_export"] = df.groupby(["hs6","partner_iso3"])["export_cz_to_partner"].shift(1)
    df["YoY_export_change"] = safe_div(df["export_cz_to_partner"] - df["prev_export"], df["prev_export"])

    # 3) Partner share in CZ exports (for other analytics)
    df["partner_share_in_cz_exports"] = safe_div(df["export_cz_to_partner"], df["export_cz_total_for_hs6"])

    # 4) YoY change in Czech share of partner imports (CORRECTED LOGIC)
    df["prev_cz_import_share"] = df.groupby(["hs6","partner_iso3"])["podil_cz_na_importu"].shift(1)
    df["YoY_partner_share_change"] = safe_div(df["podil_cz_na_importu"] - df["prev_cz_import_share"], df["prev_cz_import_share"])

    # Clean up temp helpers
    df.drop(columns=["prev_export","prev_cz_import_share"], inplace=True)

    # Save
    df.to_parquet(OUTPUT, index=False)
    print(f"[PASS] Metrics written to {OUTPUT}, rows: {len(df):,}")
    print(df.head(5))

if __name__ == "__main__":
    main()
