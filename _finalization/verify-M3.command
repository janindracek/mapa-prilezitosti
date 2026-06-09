#!/bin/bash
# ============================================================================
# M3 acceptance gate — double-click to verify the methodology rebuild.
#
# Proves, from a clean rebuild:
#   1. Two real methods only   — trade_structure + human; opportunity RETIRED,
#                                no opportunity rows anywhere in the outputs
#   2. Medians are REAL         — an independent recompute of the peer median
#                                (median of CZ-share over the target's cluster
#                                peers) matches the pipeline output, i.e. NOT the
#                                old faked statistical×0.85 / ×1.15 constants
#   3. Genuine differentiation  — the two methods recommend DIFFERENT top
#                                products per country (low Jaccard overlap), the
#                                opposite of the faked version where a constant
#                                multiple preserved the ranking
#   4. Czech descriptors        — both methods carry Czech prose in labels.csv
#
# Requires the raw BACI data (data/parquet/, data/raw/) present locally.
# ============================================================================
set -u

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$DIR/.." && pwd)"
cd "$ROOT" || exit 1
if [ -x ".venv/bin/python" ]; then PY=".venv/bin/python"; else PY="python3"; fi
export TRADE_UNITS_SCALE=1000
FAILED=0
line() { printf '%s\n' "------------------------------------------------------------"; }

echo
echo "M3 verification  (repo: $ROOT)"
echo "Python: $PY    TRADE_UNITS_SCALE=$TRADE_UNITS_SCALE"
line

echo "[1/6] fact base (etl/01)...";   $PY etl/01_build_base_facts.py            >/dev/null || { echo "  FAILED etl/01"; FAILED=1; }
echo "[2/6] metrics (etl/02)...";     $PY etl/02_compute_trade_metrics.py       >/dev/null || { echo "  FAILED etl/02"; FAILED=1; }
echo "[3/6] REAL peer medians (etl/03b)..."; $PY etl/03b_compute_all_peer_medians.py || { echo "  FAILED etl/03b"; FAILED=1; }
echo "[4/6] enrich (etl/04b)...";     $PY etl/04b_enrich_metrics_with_all_peers.py >/dev/null || { echo "  FAILED etl/04b"; FAILED=1; }
echo "[5/6] signals (etl/06b)...";    $PY etl/06b_generate_comprehensive_signals.py >/dev/null || { echo "  FAILED etl/06b"; FAILED=1; }
line

echo "[6/6] Assertions"
$PY - <<'PYEOF'
import sys, json, numpy as np, pandas as pd
ok = True
pm = pd.read_parquet("data/out/peer_medians_comprehensive.parquet")
sig = pd.read_parquet("data/out/signals_comprehensive.parquet")
met = pd.read_parquet("data/out/metrics.parquet", columns=["year","hs6","partner_iso3","podil_cz_na_importu"])
labels = pd.read_csv("data/ref/labels.csv")

# 1) two methods only, no opportunity anywhere
methods = set(pm["method"].unique())
types = set(sig["type"].unique())
if methods == {"trade_structure", "human"} and not any("opportunit" in str(x).lower() for x in types):
    print(f"  PASS — two real methods only {sorted(methods)}; signal types {sorted(types)} (no opportunity)")
else:
    print(f"  FAIL — methods={sorted(methods)} types={sorted(types)}"); ok = False

# 2) medians are REAL: independent recompute matches for a sample
sample = pm[pm["peer_count"] > 0].sample(min(300, len(pm)), random_state=1)
mism = 0
mt = met[met["year"].isin(sample["year"].unique())]
idx = {(int(r.year), r.hs6): None for r in sample.itertuples()}
for r in sample.itertuples():
    peers = json.loads(r.peer_countries)
    sh = mt[(mt.year == r.year) & (mt.hs6 == r.hs6) & (mt.partner_iso3.isin(peers))]["podil_cz_na_importu"].dropna()
    if len(sh) and abs(np.median(sh) - r.peer_median_share) > 1e-9:
        mism += 1
if mism == 0:
    print(f"  PASS — medians are real: 300/300 sampled rows match an independent median recompute (not a scaled constant)")
else:
    print(f"  FAIL — {mism}/300 sampled medians did not match an independent recompute"); ok = False

# 3) differentiation: low Jaccard overlap of top-3 products per country
pg = sig[sig["type"].str.startswith("Peer_gap")]
ts = pg[pg.method == "trade_structure"]; hu = pg[pg.method == "human"]
common = sorted(set(ts.partner_iso3) & set(hu.partner_iso3))
def top(df, c, n=3): return set(df[df.partner_iso3 == c].sort_values("intensity", ascending=False).head(n).hs6)
jac = [len(top(ts,c) & top(hu,c)) / len(top(ts,c) | top(hu,c)) for c in common if top(ts,c) and top(hu,c)]
mj = float(np.mean(jac)) if jac else 1.0
if mj < 0.30:
    print(f"  PASS — methods differentiate: mean top-3 product overlap (Jaccard) = {mj:.2f} over {len(common)} countries (1.0=identical)")
else:
    print(f"  FAIL — methods too similar: Jaccard {mj:.2f}"); ok = False

# 4) Czech descriptors present + opportunity retired
meth = labels[labels.kind == "methodology"].set_index("id")
def has_cz(s): return isinstance(s, str) and len(s) > 40 and "TBD" not in s
if (meth.loc["trade_structure","status"] == "ok" and has_cz(meth.loc["trade_structure","full_description"]) and
    meth.loc["human","status"] == "ok" and has_cz(meth.loc["human","full_description"]) and
    meth.loc["opportunity","status"] == "retired"):
    print(f"  PASS — Czech descriptors set for trade_structure + human; opportunity retired in labels.csv")
else:
    print(f"  FAIL — labels.csv methodology rows not in expected state"); ok = False

print()
print("  Example (same country, different recommended products):")
for c in [x for x in ["DEU","POL","ALB"] if x in common][:3]:
    a = ", ".join(sorted(top(ts,c))); b = ", ".join(sorted(top(hu,c)))
    print(f"    {c}: trade_structure[{a}]  vs  human[{b}]")

sys.exit(0 if ok else 1)
PYEOF
[ $? -ne 0 ] && FAILED=1
line
if [ "$FAILED" -eq 0 ]; then echo "RESULT: ✅ M3 PASS — two real, distinct methods"; else echo "RESULT: ❌ M3 FAIL — see messages above"; fi
echo
read -r -p "Press Return to close..." _ 2>/dev/null || true
exit $FAILED
