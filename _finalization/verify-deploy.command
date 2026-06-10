#!/bin/bash
# ============================================================================
# verify-deploy — smoke-test a running deployment (or a local prod build) (M7).
#
# Hits the live endpoints + the SPA root and asserts each one. Pass the base URL
# as $1, or set BASE_URL, else defaults to the local prod-build port (:8000).
#
#   ./_finalization/verify-deploy.command https://mapa-prilezitosti.onrender.com
#
# Double-clickable: with no arg it tests http://127.0.0.1:8000 (e.g. after
# build-ui.command). Exit 0 = all green.
# ============================================================================
set -u
BASE="${1:-${BASE_URL:-http://127.0.0.1:8000}}"
BASE="${BASE%/}"
PY="$(cd "$(dirname "$0")/.." && pwd)/.venv/bin/python"; [ -x "$PY" ] || PY="python3"

echo; echo "verify-deploy → $BASE"; echo "------------------------------------------------------------"
FAIL=0
pass() { echo "  PASS — $1"; }
fail() { echo "  FAIL — $1 :: $2"; FAIL=1; }

# 1. /health
BODY=$(curl -s --max-time 30 "$BASE/health")
echo "$BODY" | grep -q '"status":"ok"' && pass "/health → status ok" || fail "/health" "$BODY"

# 2. /map_v2 — per-product importer coverage (cars HS6 870323). Full universe is
#    226 importers; a single product covers most of them (>200 expected).
N=$(curl -s --max-time 60 "$BASE/map_v2?hs6=870323&year=2023&metric=cz_share_in_partner_import" \
    | $PY -c "import sys,json; d=json.load(sys.stdin); print(len(d) if isinstance(d,list) else 0)" 2>/dev/null)
[ "${N:-0}" -ge 200 ] 2>/dev/null && pass "/map_v2 → $N importers (≥200)" || fail "/map_v2" "got $N rows"

# 3. /top_signals?country=DEU — request-time two-tier selection, ≤10, ≥1 signal.
SIG=$(curl -s --max-time 60 "$BASE/top_signals?country=DEU" \
    | $PY -c "import sys,json;from collections import Counter; d=json.load(sys.stdin); r=d if isinstance(d,list) else d.get('signals',[]); print(len(r), len(Counter(x.get('type') for x in r)))" 2>/dev/null)
read -r SN ST <<<"$SIG"
[ "${SN:-0}" -ge 1 ] 2>/dev/null && pass "/top_signals DEU → $SN signals, $ST types" || fail "/top_signals DEU" "got '$SIG'"

# 4. /signals/all — full analytics set, paginated total ~108k.
TOT=$(curl -s --max-time 60 "$BASE/signals/all?limit=5" \
    | $PY -c "import sys,json; d=json.load(sys.stdin); print(d.get('total',0))" 2>/dev/null)
[ "${TOT:-0}" -ge 50000 ] 2>/dev/null && pass "/signals/all → total $TOT (≥50k)" || fail "/signals/all" "total $TOT"

# 5. /insights — non-empty Czech text (AI if key set, else deterministic fallback).
ILEN=$(curl -s --max-time 90 "$BASE/insights?importer=DEU&hs6=870323&year=2023" \
    | $PY -c "import sys,json; d=json.load(sys.stdin); t=d.get('insight','') if isinstance(d,dict) else str(d); print(len(t))" 2>/dev/null)
[ "${ILEN:-0}" -ge 40 ] 2>/dev/null && pass "/insights → $ILEN chars" || fail "/insights" "len $ILEN"

# 6. / — SPA root (must be HTML with #root, NOT JSON).
ROOT=$(curl -s --max-time 30 "$BASE/")
echo "$ROOT" | grep -q 'id="root"' && pass "/ → SPA HTML (#root)" || fail "/" "root is not the SPA (got: $(echo "$ROOT" | head -c 80))"

# 7. /world.json — bundled map geometry (offline-safe).
WC=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 "$BASE/world.json")
[ "$WC" = "200" ] && pass "/world.json → 200" || fail "/world.json" "HTTP $WC"

echo "------------------------------------------------------------"
if [ "$FAIL" -eq 0 ]; then echo "RESULT: ✅ deploy smoke-test PASSED — $BASE"; else echo "RESULT: ❌ deploy smoke-test FAILED — see above"; fi
echo
read -r -p "Press Return to close..." _ 2>/dev/null || true
exit $FAIL
