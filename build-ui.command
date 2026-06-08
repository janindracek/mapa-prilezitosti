#!/bin/bash
# build-ui.command — double-click to build the React UI for production and serve it
# exactly the way the deploy does: through the API (FastAPI mounts ui/dist at "/",
# same-origin, so data loads too). This is the real "no blank page" end-to-end check.
# Produces ui/dist/ (gitignored). Mirrors deploy/build.sh's `npm run build`.
set -e
cd "$(dirname "$0")"
ROOT="$(pwd)"

echo "▶ Mapa příležitosti — build UI + serve via API"
echo "  repo: $ROOT"
echo "  node: $(node --version 2>&1)"

# --- build the production bundle ---
cd ui
echo "▶ installing dependencies (npm ci) ..."
npm ci
echo "▶ building production bundle (npm run build) ..."
npm run build
echo
echo "✅ Build complete → ui/dist/"
echo "   bundle sizes:"
( cd dist/assets && ls -lh *.js 2>/dev/null | awk '{print "     " $5 "  " $9}' )
cd "$ROOT"

# --- serve the built app through the API (same as production) ---
PY="$ROOT/.venv/bin/python"; [ -x "$PY" ] || PY="python3"
pid=$(lsof -ti:8000 2>/dev/null || true); [ -n "$pid" ] && { echo "  freeing port 8000 (pid $pid)"; kill "$pid" 2>/dev/null || true; }
sleep 1

echo
echo "▶ serving the BUILT app at http://localhost:8000 (Ctrl-C to stop) ..."
echo "   (production bundle served by the API — confirms no blank page and data loads)"
PYTHONUNBUFFERED=1 "$PY" -m uvicorn api.server_full:app --host 127.0.0.1 --port 8000 > /tmp/mapa_api.log 2>&1 &
API_PID=$!
for i in $(seq 1 30); do
  curl -s -m 2 http://127.0.0.1:8000/health >/dev/null 2>&1 && break
  sleep 1
done
sleep 1
open "http://localhost:8000"
echo "   API log: /tmp/mapa_api.log · pid $API_PID"
trap "echo; echo 'stopping...'; kill $API_PID 2>/dev/null; exit 0" INT TERM
wait
