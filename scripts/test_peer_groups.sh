#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8000}"
COUNTRY="${1:-DEU}"
YEAR="${2:-2023}"
HS6="${3:-010121}"

jq_ok() { command -v jq >/dev/null 2>&1; }

echo "== Peer-group sanity for country=$COUNTRY year=$YEAR hs6=$HS6 =="

# 1) Získáme (method,k) comba z /debug/peer_groups
COMBOS_JSON="$(curl -s "$BASE/debug/peer_groups?country=$COUNTRY")"
if ! jq_ok; then
  echo "This script needs 'jq' on PATH."
  exit 1
fi

MATCHING_SPEC=$(echo "$COMBOS_JSON" | jq -r '.combos[] | select(.method|test("hs2_shares"; "i")) | "\(.method):\(.k)"' | head -n1)
OPPORT_SPEC=$(echo "$COMBOS_JSON" | jq -r '.combos[] | select(.method|test("opportunity"; "i")) | "\(.method):\(.k)"' | head -n1)

echo "  matching spec  : ${MATCHING_SPEC:-<not found>}"
echo "  opportunity spec: ${OPPORT_SPEC:-<not found>}"
echo

# helper: vytiskni souhrn pro daný peer_group param
summ() {
  local label="$1"; local pg="$2"
  local url="$BASE/signals?country=$COUNTRY&year=$YEAR&hs6=$HS6&peer_group=$pg"
  local data="$(curl -s "$url")"
  local count="$(echo "$data" | jq 'length')"
  if [ "$count" -eq 0 ]; then
    printf "• %-11s: empty\n" "$label"
    return
  fi
  local types="$(echo "$data" | jq -c '[.[].type] | group_by(.) | map({type: .[0], n: length})')"
  local labels="$(echo "$data" | jq -c '[.[].peer_group_label] | unique | sort')"
  printf "• %-11s: %s  labels=%s\n" "$label" "$types" "$labels"
}

# 2) Spuštění pro všechny tři peer‑groups
[ -n "${MATCHING_SPEC:-}" ]   && summ "matching"    "$MATCHING_SPEC"    || echo "• matching   : <combo not found>"
[ -n "${OPPORT_SPEC:-}" ]     && summ "opportunity" "$OPPORT_SPEC"      || echo "• opportunity: <combo not found>"
summ "human" "human"

# 3) Kontrola 'all' – má ukázat všechny typy pohromadě
echo
summ "all" "all"
