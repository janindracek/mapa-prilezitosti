#!/bin/bash
# run-local.command — double-click to boot Mapa příležitosti locally (API + UI)
# Produced in M1. API on :8000 (FastAPI, deployment-CSV data path), UI on :5173 (Vite).
set -e
cd "$(dirname "$0")"
ROOT="$(pwd)"

echo "▶ Mapa příležitosti — local boot"
echo "  repo: $ROOT"

# --- pick Python (repo venv has the deps) ---
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="python3"
echo "  python: $($PY --version 2>&1)"

# --- free ports if something is already running ---
for p in 8000 5173; do
  pid=$(lsof -ti:$p 2>/dev/null || true)
  [ -n "$pid" ] && { echo "  freeing port $p (pid $pid)"; kill "$pid" 2>/dev/null || true; }
done
sleep 1

# --- start API ---
echo "▶ starting API on http://127.0.0.1:8000 ..."
PYTHONUNBUFFERED=1 "$PY" -m uvicorn api.server_full:app --host 127.0.0.1 --port 8000 \
  > /tmp/mapa_api.log 2>&1 &
API_PID=$!

# --- start UI ---
echo "▶ starting UI on http://localhost:5173 ..."
( cd ui && npm run dev > /tmp/mapa_ui.log 2>&1 ) &
UI_PID=$!

# --- wait for API health ---
echo -n "  waiting for API"
for i in $(seq 1 30); do
  if curl -s -m 2 http://127.0.0.1:8000/health >/dev/null 2>&1; then echo " ✓"; break; fi
  echo -n "."; sleep 1
done

sleep 3
echo "▶ opening browser ..."
open "http://localhost:5173"

echo
echo "✅ Running.  API log: /tmp/mapa_api.log   UI log: /tmp/mapa_ui.log"
echo "   API pid $API_PID · UI pid $UI_PID"
echo "   Press Ctrl-C in this window to stop both."
trap "echo; echo 'stopping...'; kill $API_PID $UI_PID 2>/dev/null; exit 0" INT TERM
wait
