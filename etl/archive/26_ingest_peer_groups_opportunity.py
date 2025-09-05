#!/usr/bin/env python3
"""
26_ingest_peer_groups_opportunity.py

Ingestuje CSV peer skupin pro "opportunity" do jednotného peer_groups.parquet.

Vstupy:
- data/out/peer_groups_opportunity.csv   # sloupce: iso(M49 numeric), cluster, method, k, year
- (volitelně) data/ref/iso_overrides.csv # manuální mapování: iso3_original -> iso3_alpha3

Výstup:
- data/out/peer_groups.parquet           # append (po odfiltrování staré verze stejné metody/roku)

Poznámky:
- Převádí iso (numeric) -> iso3 (alpha-3).
- Idempotentní: odstraní existující řádky pro stejnou (method, year) a teprve pak přidá nové.
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd
from typing import Optional, Dict
import argparse

IN_CSV = Path("data/out/peer_groups_opportunity.csv")
OUT_PARQUET = Path("data/out/peer_groups.parquet")
OVERRIDES_FILE = Path("data/ref/iso_overrides.csv")  # iso3_original, iso3_alpha3

# ---- Helpers (stejné principy jako v 99_fix_peer_groups) ----

def load_overrides() -> Dict[str, str]:
    if not OVERRIDES_FILE.exists():
        return {}
    df = pd.read_csv(OVERRIDES_FILE)
    df = df.dropna(subset=["iso3_original", "iso3_alpha3"])
    df["iso3_original"] = df["iso3_original"].astype(str).str.strip()
    df["iso3_alpha3"]   = df["iso3_alpha3"].astype(str).str.strip().str.upper()
    return dict(zip(df["iso3_original"], df["iso3_alpha3"]))

try:
    import pycountry  # optional
except Exception:
    pycountry = None

def to_int_like(x: object) -> Optional[int]:
    try:
        if pd.isna(x):
            return None
    except Exception:
        pass
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]
    if not s or not s.replace("-", "").replace("+", "").replace(" ", "").isdigit():
        return None
    try:
        return int(s)
    except Exception:
        return None

def numeric_to_alpha3(num: int) -> Optional[str]:
    if pycountry is None:
        return None
    try:
        rec = pycountry.countries.get(numeric=str(num).zfill(3))
        return rec.alpha_3 if rec else None
    except Exception:
        return None

def map_iso_numeric_to_alpha3(series: pd.Series, overrides: Dict[str,str]) -> pd.Series:
    out = []
    for v in series.tolist():
        key = "" if v is None else str(v).strip()
        # overrides nejdřív (můžeš mapovat zvláštnosti)
        if key in overrides:
            out.append(overrides[key]); continue
        num = to_int_like(v)
        if num is not None:
            mapped = numeric_to_alpha3(num)
            out.append(mapped)
        else:
            out.append(None)
    return pd.Series(out, index=series.index, dtype="object")

# ---- Main ----

def main(drop_unmapped: bool = False):
    if not IN_CSV.is_file():
        raise FileNotFoundError(f"Missing {IN_CSV}")

    df = pd.read_csv(IN_CSV)
    need = {"iso","cluster","method","k","year"}
    miss = need - set(df.columns)
    if miss:
        raise ValueError(f"{IN_CSV} missing columns: {sorted(miss)}")

    overrides = load_overrides()
    df["iso3"] = map_iso_numeric_to_alpha3(df["iso"], overrides)

    missing = int(df["iso3"].isna().sum())
    if missing:
        problems = sorted(df.loc[df["iso3"].isna(), "iso"].astype(str).unique().tolist())
        msg = (
            f"{missing} iso codes could not be mapped to alpha-3. Problem values: {problems}\n"
            f"Add rows to {OVERRIDES_FILE} (iso3_original,iso3_alpha3) and rerun, or run with --drop-unmapped to skip them."
        )
        if not drop_unmapped:
            raise ValueError(msg)
        # drop unmapped rows explicitly
        before = len(df)
        df = df[df["iso3"].notna()].copy()
        print(f"⚠️  Dropping {before - len(df)} unmapped iso rows: {problems}")

    # výstupní schéma
    out = df[["iso3","cluster","method","k","year"]].copy()
    # sanity
    assert out["iso3"].str.len().eq(3).all(), "iso3 must be alpha-3"
    assert out["year"].notna().all()
    assert out["method"].astype(str).str.len().ge(1).all()

    # načti existující peer_groups.parquet a odstraň staré řádky stejné metody/roku
    if OUT_PARQUET.is_file():
        base = pd.read_parquet(OUT_PARQUET)
        mask = ~((base["method"] == out["method"].iloc[0]) & (base["year"] == out["year"].iloc[0]))
        combined = pd.concat([base[mask], out], ignore_index=True)
    else:
        combined = out

    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(OUT_PARQUET, index=False)
    # info
    k_val = int(out["k"].iloc[0]) if not out.empty else -1
    print(f"✅ Ingested opportunity peers into {OUT_PARQUET} with method='{out['method'].iloc[0]}', k={k_val}, year={int(out['year'].iloc[0])}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--drop-unmapped", action="store_true", help="Skip rows with iso that cannot be mapped to alpha-3")
    args = ap.parse_args()
    main(drop_unmapped=args.drop_unmapped)