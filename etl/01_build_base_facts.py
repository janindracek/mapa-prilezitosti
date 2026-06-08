"""
ETL stage 01 — build fact_base.parquet from raw BACI.

This is the ONLY place dollars are scaled (kUSD -> USD via TRADE_UNITS_SCALE)
and the ONLY place BACI numeric codes are resolved to ISO3 (via country_ref,
the single source of truth — NOT pycountry, which silently drops the ~6 BACI
codes that deviate from ISO-3166, e.g. USA=842, France=251).

The core table covers ALL importing countries (OUTER join), so the world map
has every market — not just the ~205 that Czechia exports to.
"""
import os
import sys

import pandas as pd

# Make the repo root importable so `country_ref` resolves when run from anywhere.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import country_ref as cr

# BACI values are in thousands of USD — apply scaling HERE and nowhere else.
TRADE_SCALE = int(os.environ.get("TRADE_UNITS_SCALE", "1000"))

DETAILED_PATHS = [
    "data/parquet/BACI_HS22_Y2022_V202501/data.parquet",
    "data/parquet/BACI_HS22_Y2023_V202501/data.parquet",
]
COUNTRY_ISO3 = cr.CZ_ISO3  # "CZE"
OUT_PATH = "data/out/fact_base.parquet"


def to_numeric(s):
    return pd.to_numeric(s, errors="coerce")


def main():
    # 1) Load + stack minimal columns for speed
    dfs = []
    for p in DETAILED_PATHS:
        if not os.path.isfile(p):
            raise FileNotFoundError(f"Missing detailed file: {p}")
        df = pd.read_parquet(p, columns=["year", "exporter", "importer", "hs6", "value_usd"])
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)

    # 2) Types and scaling (BACI values are in thousands of USD)
    df["value_usd"] = to_numeric(df["value_usd"]) * TRADE_SCALE
    df["year"] = to_numeric(df["year"]).astype("int32", copy=False)

    # 3) Numeric BACI codes -> ISO3 via the single source of truth.
    df.rename(columns={"exporter": "exporter_num", "importer": "importer_num"}, inplace=True)
    df["exporter_iso3"] = cr.map_series_num_to_iso3(df["exporter_num"])
    df["partner_iso3"] = cr.map_series_num_to_iso3(df["importer_num"])

    # Hard guard: zero dropped codes. Every BACI code in the data must resolve.
    bad_exp = sorted(df.loc[df["exporter_iso3"].isna(), "exporter_num"].unique().tolist())
    bad_imp = sorted(df.loc[df["partner_iso3"].isna(), "importer_num"].unique().tolist())
    assert not bad_exp, f"Unmapped exporter codes (not in country_ref): {bad_exp}"
    assert not bad_imp, f"Unmapped importer codes (not in country_ref): {bad_imp}"

    # hs6 to zero-padded 6-char string for consistency
    df["hs6"] = df["hs6"].astype("Int64").astype("string")
    df["hs6"] = df["hs6"].str.pad(6, fillchar="0")

    # 4) Czech exports slice
    cz = df[df["exporter_iso3"] == COUNTRY_ISO3].copy()

    # 5) Aggregates
    exp_cz_to_partner = (
        cz.groupby(["year", "hs6", "partner_iso3"], as_index=False)["value_usd"].sum()
          .rename(columns={"value_usd": "export_cz_to_partner"})
    )

    imp_partner_total = (
        df.groupby(["year", "hs6", "partner_iso3"], as_index=False)["value_usd"].sum()
          .rename(columns={"value_usd": "import_partner_total"})
    )

    exp_cz_total_for_hs6 = (
        cz.groupby(["year", "hs6"], as_index=False)["value_usd"].sum()
          .rename(columns={"value_usd": "export_cz_total_for_hs6"})
    )

    # 6) OUTER join: keep every (year, hs6, importer) the world imports, even
    #    where Czechia exports nothing — the world map needs all markets.
    base = exp_cz_to_partner.merge(
        imp_partner_total, on=["year", "hs6", "partner_iso3"], how="outer"
    )
    base = base.merge(exp_cz_total_for_hs6, on=["year", "hs6"], how="left")

    # CZ-side values are genuinely zero where CZ does not export.
    base["export_cz_to_partner"] = base["export_cz_to_partner"].fillna(0.0)
    base["export_cz_total_for_hs6"] = base["export_cz_total_for_hs6"].fillna(0.0)

    # 7) Integrity assertions (fail the build, don't ship silently-wrong data).
    full_universe = imp_partner_total["partner_iso3"].nunique()
    covered = base["partner_iso3"].nunique()
    assert covered == full_universe, f"Coverage {covered} != importer universe {full_universe}"
    assert base["partner_iso3"].notna().all(), "Null partner_iso3 in fact_base"
    # No bilateral CZ export can exceed the partner's total import of that HS6.
    over = int((base["export_cz_to_partner"] > base["import_partner_total"] + 1e-6).sum())
    assert over == 0, f"{over} rows where export_cz_to_partner > import_partner_total"

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    base.to_parquet(OUT_PATH, index=False)

    print(f"[PASS] Wrote {OUT_PATH} with {len(base):,} rows")
    print(f"[PASS] Importer coverage: {covered} countries (full BACI import universe)")
    print(f"[PASS] Zero dropped country codes; integrity (export <= import) holds")
    print(base.head(5))


if __name__ == "__main__":
    main()
