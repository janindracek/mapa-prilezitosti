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

    # 3) Partner share in CZ exports
    df["partner_share_in_cz_exports"] = safe_div(df["export_cz_to_partner"], df["export_cz_total_for_hs6"])

    # 4) YoY share change
    df["prev_share"] = df.groupby(["hs6","partner_iso3"])["partner_share_in_cz_exports"].shift(1)
    df["YoY_partner_share_change"] = safe_div(df["partner_share_in_cz_exports"] - df["prev_share"], df["prev_share"])

    # Clean up temp helpers
    df.drop(columns=["prev_export","prev_share"], inplace=True)

    # Save
    df.to_parquet(OUTPUT, index=False)
    print(f"[PASS] Metrics written to {OUTPUT}, rows: {len(df):,}")
    print(df.head(5))

if __name__ == "__main__":
    main()
