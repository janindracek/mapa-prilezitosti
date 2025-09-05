#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8000}"
COUNTRY="${1:-DEU}"
YEAR="${2:-2023}"
LIMIT="${3:-50}"   # kolik HS6 kandidátů projít z /products

need_jq() { command -v jq >/dev/null 2>&1 || { echo "This script needs 'jq'."; exit 1; }; }
need_jq

echo "== Searching HS6 with non-empty signals for all peer groups =="
echo "country=$COUNTRY  year=$YEAR  candidates=$LIMIT"

# 1) získej metody z /debug/peer_groups pro danou zemi
DBG=$(curl -s "$BASE/debug/peer_groups?country=$COUNTRY")
MATCHING=$(echo "$DBG" | jq -r '.combos[] | select(.method|test("hs2_shares";"i")) | "\(.method):\(.k)"' | head -n1)
OPPORT=$(echo "$DBG" | jq -r '.combos[] | select(.method|test("opportunity";"i")) | "\(.method):\(.k)"' | head -n1)

if [ -z "$MATCHING" ] || [ -z "$OPPORT" ]; then
  echo "No matching/opportunity combos found for $COUNTRY (check peer_groups.parquet)."
  exit 2
fi

# 2) kandidátní HS6 z /products (top podle exportu do dané země)
HS6S=$(curl -s "$BASE/products?country=$COUNTRY&year=$YEAR&top=$LIMIT" | jq -r '.[].hs6')

found_any=0
for H in $HS6S; do
  # vyhodnoť 3 peer skupiny + 'all'
  M=$(curl -s "$BASE/signals?country=$COUNTRY&year=$YEAR&hs6=$H&peer_group=$MATCHING" | jq 'map(select(.type|test("^Peer_gap"))) | length')
  O=$(curl -s "$BASE/signals?country=$COUNTRY&year=$YEAR&hs6=$H&peer_group=$OPPORT"  | jq 'map(select(.type|test("^Peer_gap"))) | length')
  HN=$(curl -s "$BASE/signals?country=$COUNTRY&year=$YEAR&hs6=$H&peer_group=human"   | jq 'map(select(.type|test("^Peer_gap"))) | length')
  ALL=$(curl -s "$BASE/signals?country=$COUNTRY&year=$YEAR&hs6=$H&peer_group=all"    | jq 'map(select(.type|test("^Peer_gap"))) | length')
  if [ "$M" -gt 0 ] || [ "$O" -gt 0 ] || [ "$HN" -gt 0 ]; then
    printf "%s  hs6=%s  matching=%s  opportunity=%s  human=%s  all=%s\n" "$(date +%H:%M:%S)" "$H" "$M" "$O" "$HN" "$ALL"
    found_any=1
  fi
  # pokud všechny tři mají zásah, vypiš detaily a skonči
  if [ "$M" -gt 0 ] && [ "$O" -gt 0 ] && [ "$HN" -gt 0 ]; then
    echo "---- DETAILS (first 3 rows per group) ----"
    echo "matching ($MATCHING):"
    curl -s "$BASE/signals?country=$COUNTRY&year=$YEAR&hs6=$H&peer_group=$MATCHING" \
      | jq 'map(select(.type|test("^Peer_gap")))[:3] | map({type,hs6,partner_iso3,intensity,value,peer_group_label})'
    echo "opportunity ($OPPORT):"
    curl -s "$BASE/signals?country=$COUNTRY&year=$YEAR&hs6=$H&peer_group=$OPPORT" \
      | jq 'map(select(.type|test("^Peer_gap")))[:3] | map({type,hs6,partner_iso3,intensity,value,peer_group_label})'
    echo "human:"
    curl -s "$BASE/signals?country=$COUNTRY&year=$YEAR&hs6=$H&peer_group=human" \
      | jq 'map(select(.type|test("^Peer_gap")))[:3] | map({type,hs6,partner_iso3,intensity,value,peer_group_label})'
    exit 0
  fi
done

if [ "$found_any" -eq 0 ]; then
  echo "No HS6 returned any peer-gap for $COUNTRY (thresholds may be strict or data sparse). Try another country or increase LIMIT."
  exit 3
else
  echo "Found some hits, but not all three groups together. Try rerunning with a higher LIMIT or different COUNTRY."
fi
