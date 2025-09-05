# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ Dummy Data Policy

**IMPORTANT**: Any dummy data created during development MUST be documented immediately in this file to facilitate easy removal. Dummy data can mislead users and should never reach production.

**Dummy data cleanup completed**: All placeholder data has been removed from the application.

## Recent UI/UX Improvements (September 2024)

The following user experience improvements were implemented:

**🔧 Chart & Map Precision Fixes:**
- **Tooltip Decimals**: Values below 1 million now show 2 decimal places in chart tooltips (e.g., "0.12 mil. USD" instead of "0 mil. USD")
- **Map Decimal Precision**: Very small market shares (< 0.1%) now show 3 decimal places (e.g., "0.023%" instead of "0.0%")

**🌍 Country Selection Improvements:**
- **Czech Republic Filtering**: Removed Czech Republic from country dropdown - this tool is designed for Czech administration to analyze export opportunities to other countries
- **Dynamic Country-Product Combinations**: Country changes now automatically trigger new signal display combining previously selected HS6 codes with the newly selected country

**📊 Signal Information Enhancement:**
- **New Signal Info Component**: Added `SignalInfo.jsx` component below "Klíčová data" section displaying:
  - Signal type in Czech (e.g., "Nárůst exportu", "Mezera - strukturálně podobné země") 
  - Signal explanation describing what the signal indicates
  - Peer group information: "není relevantní" for non-peer signals, or detailed peer group explanation with country lists for peer-based signals
- **API Integration**: Component uses `/peer_groups/explanation` endpoint for dynamic peer group information

**🔧 Signal Duplication Fix:**
- **Deduplication Logic**: Enhanced `/top_signals` endpoint with proper deduplication based on (partner_iso3, hs6, type) combinations
- **Balanced Signal Distribution**: Maintains fair representation across all methodologies while eliminating duplicate signals

**📚 Enhanced Peer Group Explanations:**
- **Rich Cluster Descriptions**: Updated `api/peer_group_registry.py` with detailed Czech explanations for all peer group clusters
- **Human Methodology**: 23 clusters with expert-curated regional groupings (e.g., "Central Europe (V4+AT+SI)" - "Průmyslové jádro střední Evropy, vysoký podíl strojírenství a automobilového dodavatelského řetězce")
- **Trade Structure Methodology**: 10 clusters based on import portfolio similarity (e.g., "European core & advanced Asia" - "Pokročilá výroba, silná poptávka po strojírenství, vozidlech, meziproduktách")
- **Source Data**: Explanations restored from backup CSV files (`peer_groups_human_explained.csv`, `peer_groups_hs2_explained.csv`) with original economic analysis
- **API Integration**: Enhanced `/peer_groups/explanation` endpoint provides full cluster context in Czech for SignalInfo component

**🔧 Critical Logic Fix - Czech Republic Self-Trading Issue:**
- **Problem Identified**: UI was treating Czech Republic as signal country instead of selected country, and Czech Republic appeared in its own peer groups (impossible since countries cannot trade with themselves)
- **UI Fix**: Modified `SignalInfo.jsx` to always fetch peer group explanations for Czech Republic ("CZE") regardless of selected country, since signals are about Czech export opportunities
- **Data Layer Fix**: Enhanced `api/data/loaders.py` to exclude Czech Republic from peer countries lists - peer groups now show trading partners only
- **ETL Consistency**: Updated ETL scripts (`create_peer_groups_*.py`) to maintain Czech Republic in cluster data (needed for cluster identification) but exclude it from trading partner results
- **Result**: 
  - Human peer group: 5 countries (was 7 with CZE included)
  - Trade structure peer group: 29 countries (was 32 with CZE included)  
  - Peer group explanations now show accurate trading partners only

**🎯 Major Logic Correction - Signal Information Context Fix:**
- **Problem Identified**: SignalInfo component was incorrectly showing Czech Republic's peer groups instead of the selected country's peer groups
- **Fundamental Error**: When user selects Guatemala, should show Guatemala's peer group information, not Czech Republic's
- **Signal Info Fix**: 
  - Modified `SignalInfo.jsx` to use selected country for peer group explanations
  - Updated `api/peer_group_registry.py` to dynamically determine any country's cluster membership (not hardcoded to CZE)
  - Updated explanation templates from "Česká republika je zařazena..." to "Země je zařazena..." (generic for any country)
- **KeyData Median Fix**: 
  - **Critical Bug**: `insights_text.py` was calculating peer group median across ALL countries instead of selected country's peer group
  - **Corrected Logic**: Now calculates median Czech market share specifically within the selected country's peer group
  - **Impact**: Guatemala shows Central America & Caribbean median, Germany shows EU Core West median, etc.
- **Non-Peer Signal Types**: Confirmed YoY signals (export/import percentage) correctly show "není relevantní" for peer groups

## Architecture Overview

This is a trade data analysis platform with a Python ETL pipeline, FastAPI backend, and React frontend. The system processes bilateral trade data (BACI HS22 dataset) to compute trade metrics and identify export opportunities for Czech Republic.

**Key components:**
- **ETL pipeline** (`etl/`): Python scripts that process raw trade data through multiple stages
- **API layer** (`api/`): Modular FastAPI server with domain-separated architecture
- **UI layer** (`ui/`): React/Vite application with ECharts for data visualization
- **Data layer** (`data/`): Raw CSV/parquet files, processed outputs, and reference data

**Refactored API Architecture:**
- **`api/settings/`**: Centralized configuration management
- **`api/data/`**: Data access layer with caching (`cache.py`, `loaders.py`)
- **`api/services/`**: Business logic services (`SignalsService`, `PeerGroupsService`)
- **`api/routers/`**: Domain-separated API endpoints (map, signals, products, insights, metadata)
- **`api/server_full.py`**: Clean orchestration layer (15 lines, down from 955 lines)

**Data flow:**
1. Raw BACI trade data → parquet conversion
2. Metrics computation (market shares, YoY changes)  
3. Peer group analysis and median calculations
4. Signal generation (peer gaps, export swings)
5. UI shape generation (world map, product bars, trends)
6. API exposure for frontend consumption

**Signal types:**
- **Peer gap signals**: CZ below peer median market share (3 methodologies)
- **YoY export swing**: Significant year-over-year export changes
- **YoY share swing**: Changes in partner's share of CZ exports

**Peer Group Methodologies:**
- **`Peer_gap_below_median`** (`method="default"`): Geographic/regional peer comparison
- **`Peer_gap_matching`** (`method="kmeans_cosine_hs2_shares"`): Countries with similar export structures
- **`Peer_gap_opportunity`** (`method="opportunity"`): Countries with similar export opportunities

Each methodology answers a different economic question:
- Geographic: "How do I perform vs countries in my region?"
- Matching: "How do I perform vs structurally similar economies?"
- Opportunity: "How do I perform vs countries with similar opportunities?"

**Centralized Peer Group Architecture:**
- **`api/peer_group_registry.py`**: Centralized registry for all methodologies and explanations
- **`api/utils/country_codes.py`**: Unified country code conversion utilities
- **All UI Use Cases Supported**:
  - Signal generation (peer countries for median calculations)
  - Chart filtering (subset countries for bar charts)
  - Map filtering (future: subset countries for map display)
  - Human explanations (methodology descriptions + country lists)

**USD Unit Handling:**
- **Raw BACI Data**: Contains **kUSD** (thousands of USD). Example: `value_usd=402` = 402,000 USD
- **Single Transformation Point**: `etl/01_build_base_facts.py` converts kUSD → USD via `TRADE_UNITS_SCALE=1000`
- **All Other Stages**: Use USD values (no further unit conversions)
- **Expected Result**: Czech total exports ~250B USD (matches official statistics)

## Development Commands

### Python Backend/ETL
```bash
# Install dependencies
pip install -r requirements.txt

# Enhanced ETL pipeline (run in order) - Comprehensive Signal Support
export TRADE_UNITS_SCALE=1000  # Ensure consistent scaling
python etl/01_build_base_facts.py        # Build fact_base.parquet from BACI data
python etl/02_compute_trade_metrics.py   # Compute metrics.parquet (market shares, YoY changes)
python etl/03_compute_peer_medians.py    # Compute peer_medians_statistical.parquet (legacy)
python etl/03b_compute_all_peer_medians.py    # 🆕 Comprehensive peer medians for ALL methodologies
python etl/04b_enrich_metrics_with_all_peers.py  # 🆕 Enhanced metrics with all peer groups
python etl/05_build_map_data.py          # Create ui_shapes/map_rows.parquet for map visualization

# Comprehensive signal generation (replaces old pipeline)
python etl/06b_generate_comprehensive_signals.py  # 🆕 Generate signals for ALL methodologies
python etl/07_build_ui_signals.py        # Build UI signal data (optional)
python etl/08_enrich_ui_signals.py       # Enrich signals with metadata (optional)

# Regenerate map data for specific parameters
python etl/05_build_map_data.py --cz-id 203  # Regenerate map data with correct scaling

# Start API server
uvicorn api.server_full:APP --host 0.0.0.0 --port 8000 --reload
```

### React Frontend
```bash
cd ui

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Run tests
npm run test

# Lint code
npm run lint

# Type check (minimal TS setup)
npm run typecheck

# Run both lint and tests
npm run check

# Set up API connection
echo "VITE_API_BASE=http://localhost:8000" > .env.local
```

## Configuration

**Main config file:** `data/config.yaml`
- Signal thresholds (MIN_EXPORT_USD, S1_REL_GAP_MIN, etc.)
- Metric labels for UI display
- Max signal counts per type

**Environment variables for ETL:**
- `YEAR`: Target year for analysis (default: latest)
- `HS6`: Specific product code for analysis

## API Endpoints

The modular FastAPI server provides endpoints organized by domain:

**Map Router (`/map*`)**:
- `GET /map_v2?hs6=&year=&metric=` - Unified map data from parquet
- `GET /map?year=&hs6=&metric=&country=&hs2=` - World map with country/HS2 focus
- `GET /map/{hs6}?year=&metric=&includeName=` - Static map with HS6 name lookup

**Signals Router (`/signals*`) - 🆕 Unified ETL-First Architecture**:
- `GET /signals?country=&hs6=&type=&method=&limit=` - Comprehensive precomputed signals by methodology
- `GET /signals/methodologies` - Available peer group methodologies with metadata
- `GET /signals/comprehensive?country=&hs6=` - Complete signal data for country-product combo
- `GET /top_signals?country=&year=&limit=` - Legacy compatibility (redirects to unified service)

**Products Router (`/products`, `/trend`, `/bars`)**:
- `GET /products?year=&top=&country=&hs2=` - Top products with optional filters (legacy compatibility)
- `GET /trend?hs6=&years=` - Time series data for HS6
- `GET /bars?mode=&hs6=&year=&country=&peer_group=&top=&hs2=` - **NEW**: Unified bar chart endpoint
  - `mode=products`: Top HS6 products by export value
  - `mode=partners`: Top countries for specific HS6
  - `mode=peer_compare`: Partner bars filtered by peer group
- `GET /bars_v2?hs6=&year=&mode=&peer_group=&country=&top=` - Legacy endpoint (redirects to unified service)

**Insights Router (`/insights*`)**:
- `GET /insights?importer=&hs6=&year=` - Generated insights text
- `GET /insights_data?importer=&hs6=&year=` - Structured data for KeyData component

**Metadata Router (`/controls`, `/meta`, `/peer_groups/*`, `/debug/*`)**:
- `GET /controls` - UI controls with metric labels
- `GET /meta` - Configuration labels and thresholds  
- `GET /peer_groups/complete?country=&peer_group=&year=` - Complete peer group info
- `GET /peer_groups/explanation?method=&country=&year=` - **NEW**: Human-readable methodology explanations
- `GET /debug/peer_groups?country=` - Peer group diagnostics

**Legacy Endpoints (`/health` from `server_cors.py`)**:
- `GET /health` - Health check

## Key Files and Patterns

**ETL scripts:** Numbered sequentially (01_, 02_, etc.) and designed to be idempotent. Use `etl/_env.py` for environment parameter handling.

**Data outputs:** All processed data goes to `data/out/` in parquet format. UI shapes are in `data/out/ui_shapes/` as JSON.

**API Architecture Patterns:**
- **Routers**: Domain-separated endpoints in `api/routers/` (map, signals, products, insights, metadata)
- **Services**: Business logic in `api/services/` (`SignalsService`, `PeerGroupsService`)  
- **Data Layer**: Caching and loading in `api/data/` (`cache.py`, `loaders.py`)
- **Settings**: Configuration management in `api/settings/`
- **Legacy Modules**: Core utilities remain in root (`config.py`, `helpers.py`, `formatting.py`, etc.)

**Service Layer Benefits:**
- **Single Responsibility**: Each service handles one domain (signals, peer groups, bars)
- **Testability**: Services can be unit tested independently
- **Reusability**: Services are reused across multiple router endpoints
- **Maintainability**: Changes localized to specific business domains

**Bar Data Unification (September 2024)**:
- **`api/services/bars.py`**: Unified service for all bar chart queries
- **Consolidates**: `/products` and `/bars_v2` logic into clean, extensible service
- **Supports**: Product bars, partner bars, peer-filtered comparisons
- **Benefits**: Consistent country name resolution, value formatting, peer filtering

**UI components:** React components in `ui/src/components/` use ECharts for visualization. API calls handled via `ui/src/lib/api.js`.

**WorldMap behavior:** The WorldMap component displays one of two user-selected metrics via radio buttons:
- `cz_share_in_partner_import`: Czech market share percentages in each country's imports
- `export_value_usd`: Total value of Czech exports to each country in USD
The map data is fetched independently of signal selection and only responds to radio button changes.

**Testing:** Python has basic API tests in `api/tests/`. React uses Vitest with @testing-library for component tests.

## Common Issues & Troubleshooting

### USD Values Appear Too Small/Large
**Symptoms:** UI shows small amounts like "3.9B USD" for Czech total exports.

**Cause:** Missing `TRADE_UNITS_SCALE=1000` during fact_base.parquet generation.

**Solution:**
1. Set scaling: `export TRADE_UNITS_SCALE=1000` 
2. Rebuild base: `python etl/01_build_base_facts.py`
3. Rebuild metrics: `python etl/02_compute_trade_metrics.py && python etl/04_enrich_metrics_with_peers.py`
4. Verify: Czech total exports should be ~250B USD

**Validation command:**
```bash
python -c "
import pandas as pd
df = pd.read_parquet('data/out/metrics_enriched.parquet')
cz_total = df[df['year']==2023]['export_cz_total_for_hs6'].sum()/len(df[df['year']==2023]['hs6'].unique())
print(f'Czech total exports 2023: {cz_total/1_000_000_000:.1f}B USD (should be ~250B)')
"
```

### KeyData Bottom Rows Show "–"  
**Symptoms:** KeyData shows export values but import totals, shares, and potential export all show "–".

**Cause:** `handleRealSignalClick` not fetching complete data from `/insights_data` endpoint.

**Solution:** Check browser console for API errors and verify endpoint returns full data structure.

### API Refactoring (September 2024)
**Accomplished**: Successfully refactored monolithic `server_full.py` (955 lines) into clean modular architecture.

**Before → After**:
- **server_full.py**: 955 lines → 15 lines (98.7% reduction)
- **Architecture**: Monolithic → Domain-separated services and routers
- **Maintainability**: Single massive file → 15 focused modules averaging 50-100 lines each

**Legacy Cleanup**:
- ✅ **Removed**: `api/server.py` (208 lines of obsolete utility functions)
- ✅ **Updated**: `api/data_access.py` to remove dependency on deleted legacy module
- 📋 **Backup**: Original monolith preserved as `server_full.py.backup` (37KB)

**Benefits Achieved**:
- **Single Responsibility**: Each module has one clear purpose
- **Testability**: Services can be unit tested independently  
- **Reusability**: Services are reused across router endpoints
- **Configuration**: Centralized in `api/settings/`
- **Zero Breaking Changes**: All endpoints continue working seamlessly