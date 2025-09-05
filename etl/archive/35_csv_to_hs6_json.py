#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Convert HS6_CZ_map.csv (columns: HS6, POPIS) -> hs6_labels.json mapping.
- Pads HS6 to 6 digits with leading zeros (e.g., 10121 -> 010121).
- Trims whitespace.
- Writes pretty UTF-8 JSON with Czech diacritics.
Input : ui/public/ref/HS6_CZ_map.csv
Output: ui/public/ref/hs6_labels.json
"""

import csv
import json
import os

IN_PATH  = "ui/public/ref/HS6_CZ_map.csv"
OUT_PATH = "ui/public/ref/hs6_labels.json"

def pad_hs6(value: str) -> str:
    v = value.strip().strip('"').strip("'")
    # remove possible non-digits (safety), then pad
    v = "".join(ch for ch in v if ch.isdigit())
    if not v:
        raise ValueError(f"Empty/invalid HS6 code in input row: {value!r}")
    if len(v) > 6:
        # some sources include HS8/HS10; keep last 6 digits
        v = v[-6:]
    return v.zfill(6)

def main():
    # Ensure input exists
    if not os.path.exists(IN_PATH):
        raise SystemExit(f"Input CSV not found: {IN_PATH}")

    mapping = {}
    with open(IN_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        # Allow both "HS6,POPIS" and "Hs6,Popis" variants (just in case)
        # Normalize fieldnames
        cols = { (name or "").strip().lower(): name for name in reader.fieldnames or [] }
        col_code  = cols.get("hs6")
        col_label = cols.get("popis")
        if not col_code or not col_label:
            raise SystemExit(f"Expected header with columns HS6, POPIS. Got: {reader.fieldnames}")

        for i, row in enumerate(reader, start=2):  # start=2 to account for header line=1
            raw_code = str(row[col_code])
            raw_lab  = str(row[col_label]) if row[col_label] is not None else ""
            code = pad_hs6(raw_code)
            label = raw_lab.strip()
            if not label:
                # Skip empty labels but warn
                print(f"[warn] Empty POPIS at line {i} for code {raw_code!r}; skipping")
                continue
            mapping[code] = label  # last one wins if duplicates

    # Write JSON
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as out:
        json.dump(mapping, out, ensure_ascii=False, indent=2, sort_keys=True)

    print(f"[ok] Wrote {OUT_PATH} with {len(mapping)} items.")

    # --- tiny smoke test / assertions ---
    # a few codes present in your CSV (will be zero-padded):
    expected_samples = {
        "010130": "Osli, živí",
        "030231": "Tuňáci bílí,kříd.čerst,chl,ne játra,jikry,mlíčí",  # if present
        "040510": "Máslo o obsahu tuku >= 80 % a <= 95 % (kromě másla dehydrovaného nebo ghee)",
        "070200": "Rajčata čerstvá,chlazená",
        "080810": "Jablka čerstvá",
        "090111": "Káva nepražená s kofeinem",
        "100590": "Kukuřice ostatní",
    }
    hit = 0
    for code, must_contain in expected_samples.items():
        if code in mapping:
            assert must_contain[:6].lower().replace(" ", "")[:6] in mapping[code].lower().replace(" ", ""), \
                f"Code {code} has unexpected label: {mapping[code]!r}"
            hit += 1
    print(f"[ok] Basic checks passed ({hit} sample hits).")

if __name__ == "__main__":
    main()