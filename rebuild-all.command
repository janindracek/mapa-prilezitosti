#!/bin/bash
# ============================================================================
# rebuild-all — raw BACI → the single serving layer, end to end (M4b).
#
# Runs the whole ETL chain with loud per-stage failure, then asserts the
# serving layer == ETL output and the API reads only data/serving/.
# Double-click to refresh everything after a BACI bump. Requires the raw BACI
# data (data/parquet/, data/raw/) present locally.
# ============================================================================
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR" || exit 1
if [ -x ".venv/bin/python" ]; then PY=".venv/bin/python"; else PY="python3"; fi
export TRADE_UNITS_SCALE=1000
FAIL=0
run() { echo "  → $1"; $PY "$1" >/dev/null 2>&1 || { echo "  ✗ FAILED: $1"; FAIL=1; }; }
line() { printf '%s\n' "------------------------------------------------------------"; }

echo; echo "rebuild-all  (repo: $DIR)   TRADE_UNITS_SCALE=$TRADE_UNITS_SCALE"; line
echo "[ETL] raw → serving"
run etl/00_build_country_ref.py
run etl/01_build_base_facts.py
run etl/02_compute_trade_metrics.py
run etl/05_build_map_data.py
run etl/03b_compute_all_peer_medians.py
run etl/04b_enrich_metrics_with_all_peers.py
run etl/06b_generate_comprehensive_signals.py
run etl/07_build_serving.py
line

echo "[CHECK] serving == ETL output, single source"
$PY - <<'PYEOF'
import sys, pandas as pd
ok = True
def check(name, cond, detail=""):
    global ok
    print(f"  {'PASS' if cond else 'FAIL'} — {name}{'' if cond else ' :: '+detail}")
    ok = ok and cond

etl = pd.read_parquet("data/out/metrics_all_peers.parquet")
sig_etl = pd.read_parquet("data/out/signals_comprehensive.parquet")
core = pd.read_parquet("data/serving/core_trade.parquet")
sig = pd.read_parquet("data/serving/signals.parquet")
pg = pd.read_parquet("data/serving/peer_groups.parquet")

check("core_trade == metrics_all_peers (rows)", len(core) == len(etl), f"{len(core)} vs {len(etl)}")
check("all-country coverage (226 importers)", core["partner_iso3"].nunique() == 226, str(core["partner_iso3"].nunique()))
check("single import_partner_total (no _x/_y)", not any(c.endswith(("_x","_y")) for c in core.columns))
check("signals == full ETL set", len(sig) == len(sig_etl), f"{len(sig)} vs {len(sig_etl)}")
check("signals carry band (strong/weak)", "band" in sig.columns and set(sig["band"]) <= {"strong","weak"})
check("two methods only, opportunity retired", set(pg["method"].unique()) == {"trade_structure","human"}, str(set(pg["method"].unique())))
check("no opportunity in signals", not any("opportunit" in str(t).lower() for t in sig["type"].unique()))

# API reads only data/serving (static check on settings)
from api.settings import settings
paths = [settings.CORE_TRADE_PATH, settings.SIGNALS_PATH, settings.PEER_GROUPS_PATH, settings.METRICS_PARQUET_PATH]
check("API settings point only at data/serving", all(p.startswith("data/serving/") for p in paths), str(paths))
import os
check("old data/deployment path is gone", not os.path.exists("data/deployment/core_trade.csv"))

sys.exit(0 if ok else 1)
PYEOF
[ $? -ne 0 ] && FAIL=1
line
if [ "$FAIL" -eq 0 ]; then echo "RESULT: ✅ rebuild-all OK — serving layer fresh & single-source"; else echo "RESULT: ❌ rebuild-all FAILED — see above"; fi
echo
read -r -p "Press Return to close..." _ 2>/dev/null || true
exit $FAIL
