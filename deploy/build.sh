#!/bin/bash
# Render deployment build script
# This script runs during deployment to build missing data files

set -e  # Exit on any error

echo "🚀 Starting deployment build..."

# Set environment variables for ETL
export TRADE_UNITS_SCALE=1000
export YEAR=2023

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check if essential data files exist, if not rebuild them
echo "🔍 Checking for essential data files..."

# Check for metrics data (needed by API)
if [ ! -f "data/out/metrics_enriched.parquet" ]; then
    echo "⚠️  Missing metrics_enriched.parquet - need to rebuild from scratch"
    echo "❌ This requires source data files that are too large for GitHub"
    echo "💡 Solution: Use the deployment files in data/deployment/ instead"
    
    # For now, we'll use a deployment mode that uses only the small files
    echo "🔄 Switching to deployment mode..."
    
    # Create minimal required directories
    mkdir -p data/out
    mkdir -p data/out/ui_shapes
    
    # Copy deployment files to expected locations (optional fallback)
    if [ -d "data/deployment" ]; then
        echo "📋 Using pre-built deployment files..."
        # The API is already configured to use deployment files
    fi
else
    echo "✅ Essential data files found"
fi

# Build the React frontend fresh every deploy.
# ui/dist is gitignored and never committed, so the served bundle always matches the
# committed source — no stale-dist blank page. A build failure fails the whole deploy
# (set -e) on purpose: better to keep the last good version than ship a broken page.
echo "🎨 Building React frontend (fresh)..."
if ! command -v npm >/dev/null 2>&1; then
    echo "❌ npm/Node not available in the build environment."
    echo "   build-on-deploy needs Node 20. On Render's Python runtime this may be absent —"
    echo "   add a Node toolchain to the build env (M7 hosting task)."
    exit 1
fi
export RENDER=true   # tells vite.config.js to drop console/debugger in the deployed bundle
cd ui
npm ci
npm run build
cd ..
echo "✅ Frontend build succeeded"

# Create a simple health check endpoint test
echo "🔍 Testing API configuration..."
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
echo "🌟 App ready to serve from data/deployment/ files"