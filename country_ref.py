"""
country_ref — the single source of truth for country-code conversion.

The raw trade data is BACI (CEPII). BACI assigns its OWN numeric country codes,
which deviate from ISO-3166 numeric for several major economies — e.g. BACI
codes France=251 (ISO 250), Norway=579 (578), India=699 (356), Switzerland=757
(756), USA=842 (840). Converting BACI numerics via an ISO-3166 library such as
pycountry therefore SILENTLY DROPS those countries (5 major economies + the
"Other Asia, nes" aggregate were missing from the world map before M4a).

The fix: convert numeric <-> ISO3 using BACI's OWN published code table
(`data/ref/baci_country_codes.csv`, committed so it travels with the code), and
nowhere else. Use this module everywhere a BACI numeric code is involved
(etl/01, etl/03b, etl/05). For parsing arbitrary *user input* (names, alpha-2),
the API keeps `api/normalizers.py` — that is a different job.

Reference columns: country_code (BACI numeric), country_name, country_iso2,
country_iso3. Aggregates (e.g. 490 "Other Asia, nes" -> "S19") carry
non-standard iso3 strings on purpose; they are real trade flows and must not be
dropped — they simply lack map geometry until one is supplied (an M5 concern).
"""
from __future__ import annotations

import functools
from pathlib import Path
from typing import Optional

import pandas as pd

# Committed canonical copy of BACI's country-code table (V202501).
REF_PATH = Path(__file__).resolve().parent / "data" / "ref" / "baci_country_codes.csv"

CZ_ISO3 = "CZE"


@functools.lru_cache(maxsize=1)
def load_ref() -> pd.DataFrame:
    """Load the BACI<->ISO-3166 crosswalk.

    Columns: country_code (BACI numeric), country_name, country_iso2,
    country_iso3, iso_numeric (ISO-3166-1 numeric; <NA> for aggregates such as
    S19 and defunct entities). Regenerate with etl/00_build_country_ref.py."""
    df = pd.read_csv(REF_PATH)
    expected = {"country_code", "country_name", "country_iso2", "country_iso3", "iso_numeric"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"{REF_PATH} missing columns: {missing} (run etl/00_build_country_ref.py)")
    df["country_code"] = pd.to_numeric(df["country_code"], errors="coerce").astype("Int64")
    df["iso_numeric"] = pd.to_numeric(df["iso_numeric"], errors="coerce").astype("Int64")
    return df


@functools.lru_cache(maxsize=1)
def _num_to_iso3_map() -> dict[int, str]:
    df = load_ref()
    return {int(c): str(i) for c, i in zip(df["country_code"], df["country_iso3"]) if pd.notna(c)}


@functools.lru_cache(maxsize=1)
def _active_ref() -> pd.DataFrame:
    """Ref with one row per iso3, preferring the active entry over historical
    twins. A handful of iso3 codes are shared by a current country and a defunct
    one (BEL 56/58, DEU 276/280, SDN 729/736); the historical rows carry a
    '(...YYYY)' suffix in the name. For reverse lookups (iso3 -> num / name) we
    keep the active row. Forward lookups (num -> iso3) are unaffected: numeric
    codes are unique."""
    df = load_ref().copy()
    df["_active"] = ~df["country_name"].str.contains(r"\(", regex=True, na=False)
    df = df.sort_values("_active", ascending=False)
    return df.drop_duplicates(subset="country_iso3", keep="first")


@functools.lru_cache(maxsize=1)
def _iso3_to_num_map() -> dict[str, int]:
    df = _active_ref()
    return {str(i): int(c) for c, i in zip(df["country_code"], df["country_iso3"]) if pd.notna(c)}


@functools.lru_cache(maxsize=1)
def _iso3_to_name_map() -> dict[str, str]:
    df = _active_ref()
    return {str(i): str(n) for i, n in zip(df["country_iso3"], df["country_name"])}


@functools.lru_cache(maxsize=1)
def _iso3_to_iso_numeric_map() -> dict[str, int]:
    df = _active_ref()
    return {str(i): int(n) for i, n in zip(df["country_iso3"], df["iso_numeric"]) if pd.notna(n)}


@functools.lru_cache(maxsize=1)
def _iso_numeric_to_iso3_map() -> dict[int, str]:
    df = _active_ref()
    return {int(n): str(i) for i, n in zip(df["country_iso3"], df["iso_numeric"]) if pd.notna(n)}


def num_to_iso3(code) -> Optional[str]:
    """BACI numeric code -> ISO3 (or BACI aggregate code). None if unknown."""
    if code is None or (isinstance(code, float) and pd.isna(code)):
        return None
    try:
        return _num_to_iso3_map().get(int(code))
    except (TypeError, ValueError):
        return None


def iso3_to_num(iso3) -> Optional[int]:
    """ISO3 (or BACI aggregate code) -> BACI numeric code. None if unknown."""
    if iso3 is None:
        return None
    return _iso3_to_num_map().get(str(iso3))


def iso3_to_name(iso3) -> Optional[str]:
    """ISO3 -> human-readable country name. None if unknown."""
    if iso3 is None:
        return None
    return _iso3_to_name_map().get(str(iso3))


def iso3_to_iso_numeric(iso3) -> Optional[int]:
    """ISO3 -> ISO-3166-1 numeric (e.g. USA -> 840). None for aggregates (S19)
    or unknown codes. NB: differs from the BACI code for several countries —
    use this when a downstream library expects ISO-3166 numeric, not BACI."""
    if iso3 is None:
        return None
    return _iso3_to_iso_numeric_map().get(str(iso3))


def iso_numeric_to_iso3(n) -> Optional[str]:
    """ISO-3166-1 numeric -> ISO3 (e.g. 840 -> USA). None if unknown."""
    if n is None or (isinstance(n, float) and pd.isna(n)):
        return None
    try:
        return _iso_numeric_to_iso3_map().get(int(n))
    except (TypeError, ValueError):
        return None


def baci_num_to_iso_numeric(code) -> Optional[int]:
    """BACI numeric code -> ISO-3166-1 numeric (e.g. 842 -> 840). None for
    aggregates/unknown. The two systems disagree for USA, France, Norway,
    Switzerland, India (+ historical twins)."""
    return iso3_to_iso_numeric(num_to_iso3(code))


def cz_numeric() -> int:
    """BACI numeric code for Czechia (203). Derived from the table, not hardcoded."""
    n = iso3_to_num(CZ_ISO3)
    if n is None:
        raise ValueError(f"{CZ_ISO3} not found in {REF_PATH}")
    return n


def map_series_num_to_iso3(s: pd.Series) -> pd.Series:
    """Vectorized numeric -> ISO3 over a pandas Series."""
    return s.map(_num_to_iso3_map())
