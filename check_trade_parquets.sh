#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 3 ]; then
  echo "Usage: $0 <HS6> <IMPORTER_ISO3> <YEAR>"
  echo "Example: $0 845180 BEL 2023"
  exit 1
fi

HS6_RAW="$1"
IMPORTER="$(echo "$2" | tr '[:lower:]' '[:upper:]')"
YEAR="$3"

# Zdroje dle serveru
BACI_PATH="${BACI_PARQUET:-data/parquet/baci.parquet}"
METRICS_PATH="data/out/metrics_enriched.parquet"
MAP_ROWS_PATH="data/out/ui_shapes/map_rows.parquet"

python - << PY
import os, math
import pandas as pd

def z6(x:str)->str:
    x = str(x).strip()
    try: x = str(int(x)).zfill(6)
    except: x = x.zfill(6)
    return x

HS6 = z6("${HS6_RAW}")
IMPORTER = "${IMPORTER}"
YEAR = int("${YEAR}")

paths = {
    "BACI": "${BACI_PATH}",
    "METRICS": "${METRICS_PATH}",
    "MAP_ROWS": "${MAP_ROWS_PATH}",
}

def exists(p): 
    try:
        return os.path.isfile(p)
    except:
        return False

def fmt(x):
    if x is None or (isinstance(x,float) and (math.isnan(x) or math.isinf(x))):
        return None
    return float(x)

def from_baci(path):
    if not exists(path): return None
    # Očekávané sloupce v raw BACI:
    # year, reporter_iso3, partner_iso3, hs6, trade_value_usd, flow ("export"|"import")
    try:
        cols = ["year","reporter_iso3","partner_iso3","hs6","trade_value_usd","flow"]
        df = pd.read_parquet(path, columns=cols)
    except Exception as e:
        return {"error": f"Cannot read BACI parquet: {e}"}
    df["hs6"] = df["hs6"].astype(str).str.replace(r"\\D","",regex=True).str.zfill(6)
    sub = df[(df["year"]==YEAR) & (df["hs6"]==HS6)].copy()
    if sub.empty:
        return {"warning": "No rows for this HS6/YEAR in BACI"}
    # Import vybrané země (IMPORTER jako reporter, flow=import)
    imp = sub[(sub["reporter_iso3"]==IMPORTER) & (sub["flow"].str.lower()=="import")]["trade_value_usd"].sum()
    # CZ -> IMPORTER export (CZ jako reporter, importer jako partner, flow=export)
    cz_to_partner = sub[(sub["reporter_iso3"]=="CZE") & (sub["partner_iso3"]==IMPORTER) & (sub["flow"].str.lower()=="export")]["trade_value_usd"].sum()
    # CZ globální export HS6
    cz_world = sub[(sub["reporter_iso3"]=="CZE") & (sub["flow"].str.lower()=="export")]["trade_value_usd"].sum()
    share = (cz_to_partner/imp) if imp>0 else None
    return {
        "import_partner_total": fmt(imp),
        "export_cz_to_partner": fmt(cz_to_partner),
        "export_cz_total_for_hs6": fmt(cz_world),
        "cz_share_in_partner_import": fmt(share),
        "_rows": int(len(sub)),
    }

def from_metrics(path):
    if not exists(path): return None
    try:
        cols = ["year","partner_iso3","hs6","import_partner_total","export_cz_to_partner","export_cz_total_for_hs6","podil_cz_na_importu"]
        df = pd.read_parquet(path, columns=cols)
    except Exception as e:
        return {"error": f"Cannot read METRICS parquet: {e}"}
    df["hs6"] = df["hs6"].astype(str).str.replace(r"\\D","",regex=True).str.zfill(6)
    sub = df[(df["year"]==YEAR) & (df["hs6"]==HS6)].copy()
    if sub.empty: return {"warning": "No rows for this HS6/YEAR in METRICS"}
    # agregace na partnera
    g = sub.groupby("partner_iso3", as_index=False).agg({
        "import_partner_total":"sum",
        "export_cz_to_partner":"sum",
        "export_cz_total_for_hs6":"sum",
        "podil_cz_na_importu":"max",
    })
    row = g[g["partner_iso3"]==IMPORTER]
    if row.empty:
        # pokud chybí vybraná země, vrať alespoň globální sumy
        return {
            "warning": f"No row for importer {IMPORTER} in METRICS for {YEAR}/{HS6}",
            "import_partner_total": None,
            "export_cz_to_partner": None,
            "export_cz_total_for_hs6": float(sub["export_cz_total_for_hs6"].sum()),
            "cz_share_in_partner_import": None,
        }
    r = row.iloc[0]
    return {
        "import_partner_total": fmt(r["import_partner_total"]),
        "export_cz_to_partner": fmt(r["export_cz_to_partner"]),
        "export_cz_total_for_hs6": fmt(row["export_cz_total_for_hs6"].sum()),
        "cz_share_in_partner_import": fmt(r.get("podil_cz_na_importu")),
        "_rows": int(len(sub)),
    }

def from_map_rows(path):
    if not exists(path): return None
    try:
        df = pd.read_parquet(path)
    except Exception as e:
        return {"error": f"Cannot read MAP_ROWS parquet: {e}"}
    need = {"hs6","year","iso3","imp_total","cz_curr","cz_world"}
    if not need.issubset(df.columns):
        return {"error": f"MAP_ROWS missing columns: {sorted(list(need - set(df.columns)))}"}
    # hs6 v map_rows je často int
    df = df[(df["year"]==YEAR) & (df["hs6"].astype(str).str.replace(r'\\D','',regex=True).str.zfill(6)==HS6)]
    if df.empty: return {"warning": "No rows for this HS6/YEAR in MAP_ROWS"}
    row = df[df["iso3"]==IMPORTER]
    if row.empty:
        return {"warning": f"No row for importer {IMPORTER} in MAP_ROWS for {YEAR}/{HS6}"}
    imp = float(row["imp_total"].sum())
    czp = float(row["cz_curr"].sum())
    czw = float(row["cz_world"].sum())
    share = (czp/imp) if imp>0 else None
    return {
        "import_partner_total": fmt(imp),
        "export_cz_to_partner": fmt(czp),
        "export_cz_total_for_hs6": fmt(czw),
        "cz_share_in_partner_import": fmt(share),
        "_rows": int(len(df)),
    }

def check_scale(a, b, name):
    """Vrátí hrubý odhad škálovacího faktoru mezi dvěma zdroji (např. ~1000)."""
    if a is None or b is None or a==0 or b==0:
        return None
    r = max(a,b)/min(a,b)
    return round(r,2)

out = {}
out["BACI"]    = from_baci(paths["BACI"])
out["METRICS"] = from_metrics(paths["METRICS"])
out["MAP_ROWS"]= from_map_rows(paths["MAP_ROWS"])

print("=== Inputs ===")
print(f"HS6={HS6}  IMPORTER={IMPORTER}  YEAR={YEAR}")
for k,v in paths.items():
    print(f"{k}_PATH: {v}  (exists={exists(v)})")

print("\\n=== Results (per source) ===")
for k in ["BACI","METRICS","MAP_ROWS"]:
    print(f"[{k}] -> {out[k]}")

def safe_get(src, key):
    v = out.get(src) or {}
    return None if not isinstance(v, dict) else v.get(key)

print("\\n=== Cross-checks (scale guesses) ===")
pairs = [("BACI","METRICS"), ("BACI","MAP_ROWS"), ("METRICS","MAP_ROWS")]
for a,b in pairs:
    s_imp = check_scale(safe_get(a,"import_partner_total"), safe_get(b,"import_partner_total"), "import_partner_total")
    s_czp = check_scale(safe_get(a,"export_cz_to_partner"), safe_get(b,"export_cz_to_partner"), "export_cz_to_partner")
    print(f"{a} vs {b}: scale(import)≈{s_imp}, scale(CZ->partner)≈{s_czp}")

print("\\n=== Notes ===")
print("* Pokud vidíš scale ≈ 1000 mezi BACI a METRICS/MAP_ROWS, BACI je zřejmě v '000 USD.")
print("* Podíl CZ na importu musí být velmi podobný (nezávisí na škále).")
PY
