#!/bin/bash
# ============================================================================
# M4a acceptance gate — double-click to verify the data foundation.
#
# Proves, from a clean rebuild off raw BACI:
#   1. All-country coverage   — importer count rises from 205 -> full universe
#   2. Single dollar-scale     — kUSD->USD applied in exactly ONE place (etl/01)
#   3. Zero dropped codes       — every BACI code resolves via country_ref
#   4. Integrity                — no bilateral exceeds the partner's world/import
#
# Requires the raw BACI data (data/parquet/, data/raw/) present locally.
# ============================================================================
set -u

# Resolve repo root = this script's parent directory's parent (_finalization/..)
DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$DIR/.." && pwd)"
cd "$ROOT" || exit 1

# Pick interpreter
if [ -x ".venv/bin/python" ]; then PY=".venv/bin/python"; else PY="python3"; fi

export TRADE_UNITS_SCALE=1000
FAILED=0
line() { printf '%s\n' "------------------------------------------------------------"; }

echo
echo "M4a verification  (repo: $ROOT)"
echo "Python: $PY    TRADE_UNITS_SCALE=$TRADE_UNITS_SCALE"
line

# --- Rebuild the chain from raw -------------------------------------------
echo "[1/5] Rebuilding fact base (etl/01, outer-join + country_ref)..."
$PY etl/01_build_base_facts.py            || { echo "  BUILD FAILED (etl/01)"; FAILED=1; }
echo "[2/5] Rebuilding metrics (etl/02)..."
$PY etl/02_compute_trade_metrics.py       || { echo "  BUILD FAILED (etl/02)"; FAILED=1; }
echo "[3/5] Rebuilding map rows (etl/05, rebased on metrics, no re-scale)..."
$PY etl/05_build_map_data.py              || { echo "  BUILD FAILED (etl/05)"; FAILED=1; }
line

# --- Check 2: single dollar-scale point -----------------------------------
echo "[4/5] Single dollar-scale point: '* TRADE_SCALE' must appear in one file"
SCALE_HITS="$(grep -rln '\* *TRADE_SCALE' etl/ 2>/dev/null)"
echo "  scaling code found in: ${SCALE_HITS:-(none)}"
if [ "$SCALE_HITS" = "etl/01_build_base_facts.py" ]; then
  echo "  PASS — scaled only in etl/01"
else
  echo "  FAIL — expected exactly etl/01_build_base_facts.py"; FAILED=1
fi
line

# --- Checks 1, 3, 4: coverage, dropped codes, integrity -------------------
echo "[5/5] Coverage / dropped codes / integrity"
$PY - <<'PYEOF'
import sys
import pandas as pd
import country_ref as cr

BASELINE = 205  # documented pre-M4a coverage (CZ-export partners, pycountry-dropped)
ok = True

# Full importer universe straight from raw BACI
imp = set()
for y in (2022, 2023):
    d = pd.read_parquet(f"data/parquet/BACI_HS22_Y{y}_V202501/data.parquet", columns=["importer"])
    imp |= set(d["importer"].unique().tolist())
universe = len(imp)

# Check 3: zero dropped codes
dropped = [c for c in sorted(imp) if cr.num_to_iso3(c) is None]
if dropped:
    print(f"  FAIL — {len(dropped)} BACI importer codes unmapped: {dropped}"); ok = False
else:
    print(f"  PASS — zero dropped codes ({universe} BACI importer codes all resolve)")

# Check 1: coverage
fb = pd.read_parquet("data/out/fact_base.parquet")
cov = fb["partner_iso3"].nunique()
if cov == universe:
    print(f"  PASS — coverage {BASELINE} -> {cov} importers (full BACI import universe)")
else:
    print(f"  FAIL — coverage {cov} != universe {universe}"); ok = False

# Check 4: integrity
over_imp = int((fb["export_cz_to_partner"] > fb["import_partner_total"] + 1e-6).sum())
over_world = int((fb["export_cz_to_partner"] > fb["export_cz_total_for_hs6"] + 1e-6).sum())
nulls = int(fb["partner_iso3"].isna().sum())
if over_imp == 0 and over_world == 0 and nulls == 0:
    print(f"  PASS — integrity holds (no bilateral > partner import or CZ world total; no null iso3)")
else:
    print(f"  FAIL — over_import={over_imp} over_world={over_world} null_iso3={nulls}"); ok = False

sys.exit(0 if ok else 1)
PYEOF
[ $? -ne 0 ] && FAILED=1
line

if [ "$FAILED" -eq 0 ]; then
  echo "RESULT: ✅ M4a PASS — all checks green"
else
  echo "RESULT: ❌ M4a FAIL — see messages above"
fi
echo
# Keep the Terminal window open when double-clicked
read -r -p "Press Return to close..." _ 2>/dev/null || true
exit $FAILED
