#!/usr/bin/env python3
"""
ETL stage 07 — assemble the single SERVING LAYER (M4b).

Collapses the ETL outputs into a compact `data/serving/*.parquet` set that the
API reads through ONE loader. Nothing else is served; the heavy intermediates
stay in data/out/.

Outputs (data/serving/):
  core_trade.parquet  — the fact table (metrics_all_peers): per (year, hs6,
                        partner_iso3), all 226 importers, both years, real ×2
                        peer medians. ONE import_partner_total (no _x/_y).
                        Serves map, bars, trend, KeyData/insights, controls.
  signals.parquet     — the FULL banded signal set (no caps; request-time
                        selection is the API's job / M5).
  peer_groups.parquet — membership + Czech descriptor per cluster, for the two
                        methods. Serves /peer_groups/* and the embedded
                        methodology object.
  hs6_names.parquet   — hs6 -> Czech-tool product description.
  countries.parquet   — iso3 -> name (EN) + name_cz.

Run after etl/06b. Idempotent. Loud assertions (serving == ETL).
"""
import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import country_ref as cr

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "serving"

METRICS_ALL_PEERS = ROOT / "data" / "out" / "metrics_all_peers.parquet"
SIGNALS = ROOT / "data" / "out" / "signals_comprehensive.parquet"
PG = {
    "trade_structure": (ROOT / "data" / "out" / "peer_groups_hs2.parquet",
                        ROOT / "data" / "out" / "peer_groups_hs2_explained.csv"),
    "human": (ROOT / "data" / "out" / "peer_groups_human.parquet",
              ROOT / "data" / "out" / "peer_groups_human_explained.csv"),
}
PRODUCT_CODES = ROOT / "data" / "parquet" / "product_codes_HS22.parquet"
COUNTRY_NAMES_CZ = ROOT / "ui" / "public" / "ref" / "country_names_cz.json"

SIGNAL_TYPES = {"Peer_gap_matching", "Peer_gap_human", "YoY_export_change", "YoY_partner_share_change"}


def build_core_trade() -> pd.DataFrame:
    df = pd.read_parquet(METRICS_ALL_PEERS)
    assert "import_partner_total" in df.columns, "missing import_partner_total"
    assert not any(c.endswith(("_x", "_y")) for c in df.columns), f"collision cols: {df.columns.tolist()}"
    assert df["partner_iso3"].nunique() == 226, f"coverage {df['partner_iso3'].nunique()} != 226"
    for m in ("trade_structure", "human"):
        assert f"median_peer_share_{m}" in df.columns, f"missing median_peer_share_{m}"
    # Drop the bulky peer-membership JSON lists — not needed for map/bars/insights;
    # signals.parquet and peer_groups.parquet already carry peer memberships.
    df = df.drop(columns=[c for c in df.columns if c.startswith("peer_countries_")])
    return df


def build_signals() -> pd.DataFrame:
    s = pd.read_parquet(SIGNALS)
    assert "band" in s.columns, "signals missing band column"
    bad = set(s["type"].unique()) - SIGNAL_TYPES
    assert not bad, f"unexpected signal types (opportunity should be gone): {bad}"
    return s


def build_peer_groups() -> pd.DataFrame:
    rows = []
    for method, (parquet, explained) in PG.items():
        mem = pd.read_parquet(parquet)[["iso3", "cluster"]].dropna().drop_duplicates()
        exp = pd.read_csv(explained)
        name = dict(zip(exp["grouping_no"], exp["grouping_name"]))
        expl = dict(zip(exp["grouping_no"], exp["explanation"]))
        mem = mem.copy()
        mem["method"] = method
        mem["cluster_name"] = mem["cluster"].map(name)
        mem["explanation"] = mem["cluster"].map(expl)
        rows.append(mem[["method", "iso3", "cluster", "cluster_name", "explanation"]])
    pg = pd.concat(rows, ignore_index=True)
    assert set(pg["method"].unique()) == {"trade_structure", "human"}, pg["method"].unique()
    assert pg["explanation"].notna().all(), "some clusters lack a descriptor"
    return pg


def build_hs6_names() -> pd.DataFrame:
    pc = pd.read_parquet(PRODUCT_CODES)
    pc = pc.rename(columns={"code": "hs6", "description": "name"})
    pc["hs6"] = pc["hs6"].astype("Int64").astype("string").str.pad(6, fillchar="0")
    pc = pc[["hs6", "name"]].dropna().drop_duplicates("hs6")
    assert len(pc) > 5000, f"only {len(pc)} hs6 names"
    return pc


def build_countries(core_trade: pd.DataFrame) -> pd.DataFrame:
    isos = sorted(core_trade["partner_iso3"].dropna().unique().tolist())
    cz = json.loads(COUNTRY_NAMES_CZ.read_text()) if COUNTRY_NAMES_CZ.exists() else {}
    df = pd.DataFrame({"iso3": isos})
    df["name"] = df["iso3"].map(cr.iso3_to_name)
    df["name_cz"] = df["iso3"].map(lambda i: cz.get(i))
    return df


def main():
    print("=== M4b: building serving layer data/serving/ ===")
    OUT.mkdir(parents=True, exist_ok=True)

    core_trade = build_core_trade()
    # Sort by (year, hs6) and write small row groups so the API's on-demand
    # DuckDB reads (api/data_access.query_core, filtered by year/hs6) can skip
    # most of the file. Default 2 huge row groups defeat predicate pushdown and
    # spike memory; this is the load-bearing change that lets the full app run
    # under the 512 MB hosting tier. File size is unchanged (~38 MB).
    core_trade = core_trade.sort_values(["year", "hs6"]).reset_index(drop=True)
    core_trade.to_parquet(OUT / "core_trade.parquet", index=False, row_group_size=50_000)
    import pyarrow.parquet as _pq
    _rg = _pq.ParquetFile(OUT / "core_trade.parquet").metadata.num_row_groups
    print(f"[PASS] core_trade.parquet: {len(core_trade):,} rows, {core_trade['partner_iso3'].nunique()} importers, years {sorted(core_trade['year'].unique())}, {_rg} row groups")

    signals = build_signals()
    signals.to_parquet(OUT / "signals.parquet", index=False)
    by = signals.groupby(["type", "band"]).size().to_dict()
    print(f"[PASS] signals.parquet: {len(signals):,} (full set, banded) {by}")

    pg = build_peer_groups()
    pg.to_parquet(OUT / "peer_groups.parquet", index=False)
    print(f"[PASS] peer_groups.parquet: {len(pg):,} rows, methods {sorted(pg['method'].unique())}")

    hs6 = build_hs6_names()
    hs6.to_parquet(OUT / "hs6_names.parquet", index=False)
    print(f"[PASS] hs6_names.parquet: {len(hs6):,} products")

    countries = build_countries(core_trade)
    countries.to_parquet(OUT / "countries.parquet", index=False)
    miss_cz = int(countries["name_cz"].isna().sum())
    print(f"[PASS] countries.parquet: {len(countries):,} ({miss_cz} without Czech name)")

    print("=== serving layer ready ===")


if __name__ == "__main__":
    main()
