#!/bin/bash
# ============================================================================
# Render deploy build (M7).
#
# One code path: install deps → download the serving layer from the latest
# GitHub Release → build the UI fresh → validate the API imports.
# No data/deployment/ CSV fallback (deleted in M4b). A failure here fails the
# whole deploy on purpose (set -e): better to keep the last good version live
# than ship a broken page or an API with no data.
# ============================================================================
set -e

echo "🚀 Starting deployment build..."

export TRADE_UNITS_SCALE=1000
export YEAR=2023

# --- 1. Python dependencies --------------------------------------------------
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# --- 2. Serving layer (GitHub Release asset) ---------------------------------
# The serving layer (~43 MB) is gitignored and machine-generated; the deploy
# pulls it from the latest GitHub Release (public repo → no auth). Publish it
# with deploy/release-serving.sh after rebuild-all.command.
#
# Resolve the asset URL via the API (immediately consistent — the
# releases/latest/download redirect can lag a few seconds right after publish),
# and fall back to the redirect if the API is rate-limited/unavailable.
REPO="janindracek/mapa-prilezitosti"
REDIRECT_URL="https://github.com/$REPO/releases/latest/download/serving.tar.gz"
REQUIRED=(core_trade.parquet signals.parquet peer_groups.parquet hs6_names.parquet countries.parquet)

echo "⬇️  Resolving serving-layer asset from latest release..."
ASSET_URL=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" 2>/dev/null \
    | python -c "import sys,json
try:
    d=json.load(sys.stdin)
    print(next(a['browser_download_url'] for a in d.get('assets',[]) if a['name']=='serving.tar.gz'))
except Exception:
    pass" 2>/dev/null)
[ -z "$ASSET_URL" ] && ASSET_URL="$REDIRECT_URL"
echo "    $ASSET_URL"

mkdir -p data/serving
if ! curl -fL --retry 3 "$ASSET_URL" -o /tmp/serving.tar.gz; then
    echo "❌ Could not download the serving layer."
    echo "   Ensure a GitHub Release with asset 'serving.tar.gz' exists and is marked latest."
    echo "   Locally: rebuild-all.command  →  deploy/release-serving.sh"
    exit 1
fi
tar -xzf /tmp/serving.tar.gz -C data/serving
rm -f /tmp/serving.tar.gz

echo "🔍 Validating serving layer..."
missing=0
for f in "${REQUIRED[@]}"; do
    if [ ! -s "data/serving/$f" ]; then echo "  ✗ missing/empty data/serving/$f"; missing=1; fi
done
if [ "$missing" -ne 0 ]; then
    echo "❌ Serving layer incomplete after download — aborting deploy."
    exit 1
fi
echo "✅ Serving layer in place ($(du -sh data/serving | cut -f1))"

# --- 3. React frontend (built fresh every deploy) ----------------------------
# ui/dist is gitignored and never committed, so the served bundle always matches
# the committed source — no stale-dist blank page.
echo "🎨 Building React frontend (fresh)..."
if ! command -v npm >/dev/null 2>&1; then
    echo "❌ npm/Node not available in the build environment."
    echo "   build-on-deploy needs Node 20. Render's Python runtime ships Node — if absent,"
    echo "   set NODE_VERSION in the service env."
    exit 1
fi
export RENDER=true   # tells vite.config.js to drop console/debugger in the deployed bundle
cd ui
npm ci
npm run build
cd ..
echo "✅ Frontend build succeeded"

# --- 4. Validate API imports against the serving layer -----------------------
echo "🔍 Validating API configuration..."
python -c "
import sys
sys.path.append('.')
try:
    from api.server_full import app
    print('✅ API configuration valid')
except Exception as e:
    print(f'❌ API configuration error: {e}')
    sys.exit(1)
"

echo "✅ Deployment build complete!"
