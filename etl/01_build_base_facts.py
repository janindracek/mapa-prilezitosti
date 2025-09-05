import os
import pandas as pd

# BACI values are in thousands of USD - apply scaling
TRADE_SCALE = int(os.environ.get("TRADE_UNITS_SCALE", "1000"))

# Inputs: detailed BACI files you probed
DETAILED_PATHS = [
    "data/parquet/BACI_HS22_Y2022_V202501/data.parquet",
    "data/parquet/BACI_HS22_Y2023_V202501/data.parquet",
]
COUNTRY_ISO3 = "CZE"
OUT_PATH = "data/out/fact_base.parquet"

# Map numeric exporter/importer -> ISO3 using pycountry
def num_to_iso3(n):
    try:
        import pycountry
    except ImportError as e:
        raise RuntimeError("pycountry not installed. Run: pip install pycountry") from e
    try:
        rec = pycountry.countries.get(numeric=f"{int(n):03d}")
        return getattr(rec, "alpha_3", None)
    except Exception:
        return None

def to_numeric(s):
    return pd.to_numeric(s, errors="coerce")

def main():
    # 1) Load + stack minimal columns for speed
    dfs = []
    for p in DETAILED_PATHS:
        if not os.path.isfile(p):
            raise FileNotFoundError(f"Missing detailed file: {p}")
        df = pd.read_parquet(p, columns=["year","exporter","importer","hs6","value_usd"])
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)

    # 2) Types and scaling (BACI values are in thousands of USD)
    df["value_usd"] = to_numeric(df["value_usd"]) * TRADE_SCALE
    df["year"] = to_numeric(df["year"]).astype("int32", copy=False)

    # exporter/importer are numeric codes -> ISO3
    # keep originals as backup columns
    df.rename(columns={"exporter":"exporter_num","importer":"importer_num"}, inplace=True)
    df["exporter_iso3"] = df["exporter_num"].map(num_to_iso3)
    df["partner_iso3"]  = df["importer_num"].map(num_to_iso3)

    # hs6 to zero-padded 6-char string for consistency
    df["hs6"] = df["hs6"].astype("Int64").astype("string")
    df["hs6"] = df["hs6"].str.pad(6, fillchar="0")

    # 3) Split Czech exports
    cz = df[df["exporter_iso3"] == COUNTRY_ISO3].copy()

    # 4) Metrics
    exp_cz_to_partner = (
        cz.groupby(["year","hs6","partner_iso3"], as_index=False)["value_usd"].sum()
          .rename(columns={"value_usd":"export_cz_to_partner"})
    )

    imp_partner_total = (
        df.groupby(["year","hs6","partner_iso3"], as_index=False)["value_usd"].sum()
          .rename(columns={"value_usd":"import_partner_total"})
    )

    exp_cz_total_for_hs6 = (
        cz.groupby(["year","hs6"], as_index=False)["value_usd"].sum()
          .rename(columns={"value_usd":"export_cz_total_for_hs6"})
    )

    # 5) Merge into base fact
    base = exp_cz_to_partner.merge(imp_partner_total, on=["year","hs6","partner_iso3"], how="left")
    base = base.merge(exp_cz_total_for_hs6, on=["year","hs6"], how="left")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    base.to_parquet(OUT_PATH, index=False)

    print(f"[PASS] Wrote {OUT_PATH} with {len(base):,} rows")
    print(base.head(5))

if __name__ == "__main__":
    main()
