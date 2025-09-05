
"""
Quick validator for Parquet inputs we will use to build map_rows.parquet.
No new deps. Uses pandas/pyarrow if available.

Runs a set of checks:
 - file exists
 - schema columns present (with flexible alternatives)
 - sample rows preview
 - basic sanity (ISO3 length=3, hs6 length=6 digits, year int)
 - presence of CZE as reporter (where applicable)
Outputs a JSON report to data/out/ui_shapes/validate_report.json and prints a summary table.
"""
from __future__ import annotations
import json
import os
from pathlib import Path

import pandas as pd  # assumed present
import pyarrow.parquet as pq  # assumed present

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "out" / "ui_shapes"
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = OUT_DIR / "validate_report.json"

FILES = {
    # likely sources (adjust if needed)
    "trade_by_pair": ROOT / "data" / "parquet" / "trade_by_pair.parquet",
    "trade_by_product": ROOT / "data" / "parquet" / "trade_by_product.parquet",
    "trade_by_exporter": ROOT / "data" / "parquet" / "trade_by_exporter.parquet",
    "product_codes": ROOT / "data" / "parquet" / "product_codes_HS22.parquet",
}

# expected/alternative columns for each dataset (loose to match your pipelines)
EXPECTED = {
    "trade_by_pair": [
        ["year"],
        ["reporter_iso3", "exporter_iso3", "iso3_reporter"],
        ["partner_iso3", "importer_iso3", "iso3_partner"],
        ["hs6", "hs", "product_code"],
        ["trade_value_usd", "value_usd", "export_value_usd", "imports_usd", "exports_usd"],
        ["flow"],  # export/import; optional but helpful
    ],
    "trade_by_product": [
        ["year"],
        ["reporter_iso3", "exporter_iso3"],
        ["hs6", "hs"],
        ["export_value_usd", "value_usd", "trade_value_usd"],
    ],
    "trade_by_exporter": [
        ["year"],
        ["reporter_iso3", "exporter_iso3"],
        ["hs6", "hs"],
        ["export_value_usd", "value_usd", "trade_value_usd"],
    ],
    "product_codes": [
        ["hs6", "code"],
        ["name_en", "label_en", "label"],
    ],
}

def pick_column(cols: list[str], options: list[str]) -> str | None:
    for cand in options:
        if cand in cols:
            return cand
    return None

def scan_file(name: str, path: Path) -> dict:
    info: dict = {
        "name": name,
        "path": str(path),
        "exists": path.exists(),
        "schema": [],
        "rows_preview": [],
        "checks": [],
        "ok": False,
    }
    if not path.exists():
        info["checks"].append(f"ERROR: file missing: {path}")
        return info
    try:
        pf = pq.ParquetFile(path)
        cols = [f.name for f in pf.schema_arrow]
        info["schema"] = cols
        # read light preview (first row group slice)
        table = pf.read_row_group(0) if pf.num_row_groups > 0 else pf.read()
        df = table.slice(0, min(5, len(table))).to_pandas() if len(table) else pd.DataFrame()
        info["rows_preview"] = df.to_dict(orient="records")
    except Exception as e:
        info["checks"].append(f"ERROR: parquet read failed: {e}")
        return info

    # column presence checks
    expected = EXPECTED.get(name, [])
    present_map = {}
    for opt_group in expected:
        picked = pick_column(cols, opt_group)
        present_map[str(opt_group)] = picked
        if picked is None:
            info["checks"].append(f"ERROR: none of expected columns present {opt_group}")
    # basic sanity checks on data
    if info["rows_preview"]:
        row = info["rows_preview"][0]
        # year int
        ycol = present_map.get(str(["year"]))
        if ycol and not isinstance(row.get(ycol), (int,)):
            info["checks"].append(f"WARN: year not int on preview: {row.get(ycol)!r}")
        # hs6 len
        hscol = present_map.get(str(["hs6", "hs", "product_code"]))
        if hscol:
            v = str(row.get(hscol, ""))
            if not (v.isdigit() and len(v) in (6, 4)):  # allow hs4 just in case
                info["checks"].append(f"WARN: hs code looks odd on preview: {v!r}")
        # iso3 lengths
        for key in (["reporter_iso3", "exporter_iso3", "iso3_reporter"],
                    ["partner_iso3", "importer_iso3", "iso3_partner"]):
            col = pick_column(cols, key)
            if col and row.get(col) is not None:
                s = str(row.get(col))
                if len(s) != 3:
                    info["checks"].append(f"WARN: {col} not ISO3 length=3 on preview: {s!r}")
        # CZE presence quick scan on first 5 rows where applicable
        rcol = pick_column(cols, ["reporter_iso3", "exporter_iso3", "iso3_reporter"])
        if rcol and all((r.get(rcol) != "CZE" for r in info["rows_preview"])):
            info["checks"].append("INFO: CZE not in first 5 rows (could still be present later)")
    # overall ok flag
    has_errors = any(c.startswith("ERROR") for c in info["checks"])
    info["ok"] = (len(info["schema"]) > 0) and not has_errors
    return info

def main():
    report = {"files": [], "summary": {}}
    for name, path in FILES.items():
        info = scan_file(name, path)
        report["files"].append(info)
    total = len(report["files"])
    oks = sum(1 for f in report["files"] if f["ok"])
    report["summary"] = {"total": total, "ok": oks, "failed": total - oks}
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    # human summary
    print("\n=== Parquet Validation Summary ===")
    for f in report["files"]:
        mark = "✅" if f["ok"] else "❌"
        print(f"{mark} {f['name']}: {f['path']}")
        if f["checks"]:
            for c in f["checks"]:
                print("   -", c)
        print("   schema:", ", ".join(f["schema"][:12]), ("..." if len(f["schema"]) > 12 else ""))
    print(f"\nSummary: {oks}/{total} OK | report → {REPORT_PATH}")
    # tiny assert to fail CI if any error
    assert oks == total, f"Some parquet inputs failed validation ({total-oks} of {total})"

if __name__ == "__main__":
    main()
