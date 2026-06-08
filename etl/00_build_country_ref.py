"""
ETL stage 00 — build the committed country crosswalk `data/ref/baci_country_codes.csv`.

The raw data is BACI, which uses its OWN numeric codes; the app and most
geo/trade libraries expect ISO-3166. This sheet is the canonical TRANSLATION
table between the two systems so either side can be used:

  country_code   BACI numeric code (the raw `exporter`/`importer` value)
  country_name   BACI country name
  country_iso2   ISO-3166 alpha-2
  country_iso3   ISO-3166 alpha-3  (also a pseudo-code for BACI aggregates, e.g. S19)
  iso_numeric    ISO-3166-1 numeric  (BLANK for aggregates/defunct entities)

The point of the sheet: BACI numeric != ISO numeric for several countries —
USA 842/840, France 251/250, Norway 579/578, Switzerland 757/756, India
699/356 (plus historical twins). Carrying both columns lets a consumer key on
whichever system its library wants. `country_ref.py` reads this file.

Source: BACI's published `country_codes_V202501.csv` (the first four columns,
already committed here). `iso_numeric` is derived from `country_iso3` via
pycountry. Re-run after a BACI version bump; idempotent.
"""
import os
import sys

import pandas as pd
import pycountry

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_PATH = os.path.join(ROOT, "data", "ref", "baci_country_codes.csv")
BACI_COLS = ["country_code", "country_name", "country_iso2", "country_iso3"]


def iso_numeric_for(iso3):
    rec = pycountry.countries.get(alpha_3=str(iso3))
    return int(rec.numeric) if rec and rec.numeric else pd.NA


def main():
    if not os.path.isfile(REF_PATH):
        print(f"ERROR: missing {REF_PATH}", file=sys.stderr)
        sys.exit(2)

    df = pd.read_csv(REF_PATH)[BACI_COLS].copy()
    df["country_code"] = pd.to_numeric(df["country_code"], errors="coerce").astype("Int64")
    df["iso_numeric"] = df["country_iso3"].map(iso_numeric_for).astype("Int64")

    df.to_csv(REF_PATH, index=False)

    n = len(df)
    mapped = int(df["iso_numeric"].notna().sum())
    diverge = df[df["iso_numeric"].notna() & (df["country_code"] != df["iso_numeric"])]
    print(f"[PASS] Wrote {REF_PATH}: {n} rows, {mapped} with ISO-3166 numeric, {n - mapped} aggregates/historical (no ISO numeric)")
    print(f"[PASS] BACI numeric != ISO numeric for {len(diverge)} entries: "
          + ", ".join(f"{r.country_iso3} {r.country_code}/{r.iso_numeric}" for r in diverge.itertuples()))


if __name__ == "__main__":
    main()
