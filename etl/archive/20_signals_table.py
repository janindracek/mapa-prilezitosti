#!/usr/bin/env python3
"""
Example signals table combining country and product refs.
Creates: signals_table.parquet
"""
from pathlib import Path
import pandas as pd

PARQ = Path(__file__).resolve().parents[1] / "data" / "parquet"


def main():
    pair = pd.read_parquet(PARQ / "trade_by_pair.parquet")

    # Optional joins for human-readable labels
    countries = None
    if (PARQ / "country_codes.parquet").exists():
        countries = pd.read_parquet(PARQ / "country_codes.parquet")
        # try to standardize columns
        # expect columns like: code, iso3, name_en
        cols = {c.lower(): c for c in countries.columns}
        code_col = next((c for c in countries.columns if c.lower() in ("code", "iso3", "iso3n", "iso_num")), None)
        name_col = next((c for c in countries.columns if c.lower() in ("name", "name_en", "country")), None)
        if code_col and name_col:
            countries = countries[[code_col, name_col]].rename(columns={code_col: "code", name_col: "country"})
        else:
            countries = None

    # Example: top partners per exporter in latest year
    latest = int(pair["year"].max())
    cur = pair[pair["year"] == latest].copy()

    if countries is not None:
        cur = cur.merge(countries.add_prefix("exp_"), left_on="exporter", right_on="exp_code", how="left")
        cur = cur.merge(countries.add_prefix("imp_"), left_on="importer", right_on="imp_code", how="left")

    # Rank partners by value
    cur["rank"] = cur.groupby("exporter")["value_usd"].rank(ascending=False, method="first")

    # Keep top 10 per exporter
    cur = cur[cur["rank"] <= 10].sort_values(["exporter", "rank"])

    out = PARQ / "signals_table.parquet"
    cur.to_parquet(out, index=False)
    print("→", out)


if __name__ == "__main__":
    main()