#!/usr/bin/env python3
"""
99_fix_peer_groups_v2.py

Cíl
----
Normalizovat sloupec `iso3` v peer souborech na ISO alpha-3:

Vstupy:
- data/out/peer_groups.parquet
- data/out/peer_groups_human.csv

Výstupy:
- data/out/peer_groups.parquet            (přepíše až po úspěchu)
- data/out/peer_groups_human.parquet      (nový soubor)
- data/out/peer_groups_iso_missing_report.csv  (při chybě/dry-run)
- volitelně smaže nemapovatelná ISO (přes --write-drop)

Podpora:
- Detekce formátu přes Path.suffixes (zvládá i .parquet.bak)
- CSV s fallbacky (utf-8, utf-8-sig, latin1)
- Pycountry (pokud je nainstalováno) + ruční overrides:
  data/ref/iso_overrides.csv se sloupci:
    iso3_original,iso3_alpha3

Použití
-------
1) Dry-run (doporučeno):
   python etl/99_fix_peer_groups_v2.py

2a) Zápis pouze pokud je vše namapováno:
   python etl/99_fix_peer_groups_v2.py --write

2b) Zápis i s odhozením nemapovatelných řádků (po logu):
   python etl/99_fix_peer_groups_v2.py --write-drop
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
import shutil
import pandas as pd
from typing import Optional, Dict, Tuple

# Optional: pycountry pro M49->alpha3
try:
    import pycountry  # type: ignore
except Exception:
    pycountry = None

BASE = Path("data/out")
REF_DIR = Path("data/ref")

PEER_PARQUET_IN = BASE / "peer_groups.parquet"
PEER_HUMAN_CSV_IN = BASE / "peer_groups_human.csv"

PEER_PARQUET_OUT = BASE / "peer_groups.parquet"
PEER_HUMAN_PARQUET_OUT = BASE / "peer_groups_human.parquet"

MISSING_REPORT = BASE / "peer_groups_iso_missing_report.csv"
OVERRIDES_FILE = REF_DIR / "iso_overrides.csv"

def ensure_backup_copy(src: Path) -> None:
    if not src.exists():
        return
    bak = src.with_suffix(src.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(src, bak)

def resolve_source(path: Path) -> Path:
    if path.exists():
        return path
    bak = path.with_suffix(path.suffix + ".bak")
    if bak.exists():
        return bak
    raise FileNotFoundError(f"Neither {path} nor {bak} exists")

def read_table_auto(path: Path) -> pd.DataFrame:
    suff = path.suffixes
    if ".parquet" in suff:
        return pd.read_parquet(path)
    if ".csv" in suff:
        for enc in ("utf-8", "utf-8-sig", "latin1"):
            try:
                return pd.read_csv(path, encoding=enc)
            except UnicodeDecodeError:
                continue
        return pd.read_csv(path, encoding="latin1", errors="replace")
    # Fallback heuristika
    try:
        return pd.read_parquet(path)
    except Exception:
        return pd.read_csv(path)

def load_overrides() -> Dict[str, str]:
    if not OVERRIDES_FILE.exists():
        return {}
    df = pd.read_csv(OVERRIDES_FILE)
    df = df.dropna(subset=["iso3_original", "iso3_alpha3"])
    df["iso3_original"] = df["iso3_original"].astype(str).str.strip()
    df["iso3_alpha3"]   = df["iso3_alpha3"].astype(str).str.strip().upper()
    return dict(zip(df["iso3_original"], df["iso3_alpha3"]))

def is_alpha3(x: object) -> bool:
    if not isinstance(x, str):
        return False
    s = x.strip()
    return len(s) == 3 and s.isalpha() and s.isupper()

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

def map_iso_series(series: pd.Series, overrides: Dict[str, str]) -> Tuple[pd.Series, pd.Series]:
    out = []
    failed_orig = []
    for v in series.tolist():
        key = "" if v is None else str(v).strip()
        # 1) už alpha‑3?
        if is_alpha3(v):
            out.append(str(v).strip().upper()); continue
        # 2) overrides
        if key in overrides:
            out.append(overrides[key]); continue
        # 3) numeric M49?
        num = to_int_like(v)
        if num is not None:
            mapped = numeric_to_alpha3(num)
            if mapped:
                out.append(mapped); continue
        # fail
        out.append(None); failed_orig.append(key)
    return pd.Series(out, index=series.index, dtype="object"), pd.Series(failed_orig, dtype="object")

def convert_one(path_in: Path, kind: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = read_table_auto(path_in)
    if "iso3" not in df.columns:
        raise ValueError(f"{path_in} missing required column 'iso3'")
    df["iso3_original"] = df["iso3"].astype("string")
    overrides = load_overrides()
    mapped, failed = map_iso_series(df["iso3_original"], overrides)
    df["iso3"] = mapped
    missing_mask = df["iso3"].isna()
    missing = int(missing_mask.sum())

    if missing:
        # report unikatních problematických vstupů
        prob = (
            df.loc[missing_mask, ["iso3_original"]]
              .assign(file=str(path_in), kind=kind)
              .value_counts()
              .reset_index(name="count")
              .rename(columns={"iso3_original":"original"})
        )
        return df, prob
    # sanity
    assert df["iso3"].str.len().eq(3).all()
    assert df["iso3"].str.isalpha().all()
    return df, pd.DataFrame(columns=["original","file","kind","count"])

def main(write: bool, write_drop: bool) -> int:
    # Zálohy
    ensure_backup_copy(PEER_PARQUET_IN)
    ensure_backup_copy(PEER_HUMAN_CSV_IN)

    # Vstupy
    stat_src  = resolve_source(PEER_PARQUET_IN)
    human_src = resolve_source(PEER_HUMAN_CSV_IN)

    print(f"Reading statistical peers from: {stat_src}")
    stat_df, stat_prob = convert_one(stat_src, kind="stat")
    print(f"Reading human peers from:       {human_src}")
    human_df, human_prob = convert_one(human_src, kind="human")

    # Report problémů
    problems = pd.concat([stat_prob, human_prob], ignore_index=True)
    total_missing = int(problems["count"].sum()) if not problems.empty else 0

    if total_missing:
        problems.to_csv(MISSING_REPORT, index=False)
        uniques = sorted(problems["original"].astype(str).unique().tolist())
        print(f"\n⚠️  Unmapped ISO values found: {uniques}")
        print(f"    Details written to: {MISSING_REPORT}")

        if not write and not write_drop:
            print("\nDry-run done. Add overrides to data/ref/iso_overrides.csv and rerun.")
            return 2

        if write_drop:
            # Drop a zalogovat
            before_stat, before_human = len(stat_df), len(human_df)
            stat_df = stat_df[stat_df["iso3"].notna()].copy()
            human_df = human_df[human_df["iso3"].notna()].copy()
            print(f"\nDropping unmapped rows: stat -{before_stat-len(stat_df)}, human -{before_human-len(human_df)}")
        else:
            print("\n--write requested but unmapped exist; refusing to write to avoid bad data.")
            print("Use --write-drop to drop unmapped rows explicitly, or add overrides.")
            return 3

    # Zápis výstupů
    if write or write_drop:
        print(f"\nWriting {PEER_PARQUET_OUT} ...")
        stat_df.to_parquet(PEER_PARQUET_OUT, index=False)
        print(f"Writing {PEER_HUMAN_PARQUET_OUT} ...")
        human_df.to_parquet(PEER_HUMAN_PARQUET_OUT, index=False)

        # Mini smoke
        rd = pd.read_parquet(PEER_PARQUET_OUT)
        rh = pd.read_parquet(PEER_HUMAN_PARQUET_OUT)
        assert rd["iso3"].str.len().eq(3).all()
        assert rh["iso3"].str.len().eq(3).all()
        print("✅ Write successful and verified.")
        return 0

    print("\nDry-run OK (no write). Re-run with --write or --write-drop.")
    return 0

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="Persist outputs only if everything is mapped (safe write)")
    ap.add_argument("--write-drop", action="store_true",
                    help="Persist outputs and drop any unmapped rows (explicit data loss)")
    args = ap.parse_args()
    sys.exit(main(write=args.write, write_drop=args.write_drop))