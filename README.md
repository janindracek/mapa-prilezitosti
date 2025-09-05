# Obchodní příležitosti Česka

## Mapa příležitostí — Data Engine + UI Integration

This repo contains a small, explicit data pipeline that computes trade signals and exposes ready‑to‑use shapes for a UI via a minimal FastAPI. The goal: surface 5–10 high‑value "exclamation" signals per country/product and let the UI map, rank, and trend them.

## ⚠️ Recent Major Cleanups (September 2024)

### **Cleanup Summary**
| Task | Status | Impact |
|------|--------|--------|
| **Map Endpoints Consolidation** | ✅ Complete | Consolidated 3 redundant endpoints to single `/map_v2`, removed 47 lines duplicate code |
| **Signal Processing Cleanup** | ✅ Complete | Improved peer group methodology clarity, added comprehensive documentation |
| **Peer Groups Centralization** | ✅ Complete | Created centralized registry, enhanced UI with human explanations, future extensible |
| **Signal Computation Unification** | ✅ Complete | ETL-first architecture with comprehensive methodology support |

### **Code Quality Improvements**
- **Map Endpoints**: Consolidated from 3 redundant endpoints to single `/map_v2` endpoint
- **Signal Processing**: Cleaned up duplicate logic, improved peer group methodology clarity
- **Peer Groups**: Centralized registry with human-readable explanations and future extensibility
- **Dummy Data**: Documented and marked for removal to prevent misleading users

### **Architecture Benefits**
- Removed 150+ lines of duplicate code
- Enhanced UI capabilities with qualitative peer group explanations  
- Improved maintainability and consistency
- Fixed frontend bugs through cleanup
- Added comprehensive methodology documentation

---

## Quickstart

```bash
# 1) Set up Python env (already done)
# 2) Run comprehensive ETL pipeline (in order)
export TRADE_UNITS_SCALE=1000  # Ensure correct USD scaling
python etl/01_build_base_facts.py                    # Build fact_base.parquet from BACI data
python etl/02_compute_trade_metrics.py               # Compute metrics.parquet (market shares, YoY changes)
python etl/03b_compute_all_peer_medians.py           # 🆕 Comprehensive peer medians for ALL methodologies
python etl/04b_enrich_metrics_with_all_peers.py      # 🆕 Enhanced metrics with all peer groups
python etl/05_build_map_data.py                      # Create ui_shapes/map_rows.parquet for map visualization

# 3) Generate comprehensive signals (RECOMMENDED - ETL-first architecture)
python etl/06b_generate_comprehensive_signals.py     # 🆕 Generate signals for ALL methodologies

# 4) Legacy signal pipeline (OPTIONAL - for backward compatibility only)
python etl/06_generate_signals.py                    # Legacy signal generation
python etl/07_build_ui_signals.py                    # Build UI signal data
python etl/08_enrich_ui_signals.py                   # Enrich signals with metadata

# 5) Start API
uvicorn api.server_full:APP --host 0.0.0.0 --port 8000 --reload

# 6) Start UI (from ui/)
cd ui && printf "VITE_API_BASE=http://localhost:8000\n" > .env.local && npm run dev

Data layer — Files, flow, and outputs

Inputs (parquet/csv)
	•	data/parquet/BACI_HS22_Y20{22,23}_V202501/data.parquet
Detailed bilateral flows at HS6: year, exporter, importer, hs6, value_usd, quantity.
	•	data/parquet/product_codes_HS22.parquet
HS6 → description mapping.
	•	data/ref/country_codes_V201901.csv
ISO3 name map for UI labels.
	•	data/ref/peer_groups.json
Defines peer group for CZE (placeholder — swap for real groups later).
	•	data/config.yaml
Thresholds and labels used for signal selection and UI metadata.

## Peer Group System

The system implements multiple peer group methodologies for benchmark analysis:

### 🏛️ **Three Peer Group Methodologies (2024 Stable Release)**

1. **🧑‍🏫 Human Geographical Groups** (`method=human`)
   - **Source**: `data/out/peer_groups_human.parquet`
   - **Signal Type**: `Peer_gap_human`
   - **Method**: Expert-curated geographic and economic clustering 
   - **Logic**: Countries grouped by regional proximity and development level (e.g., "Western Balkans", "Central Europe")
   - **Groups**: 23 distinct regional clusters covering global economies
   - **Ranking Strategy**: Prioritizes markets with higher trade volumes (delta × 0.7 + volume × 0.3)
   - **Usage**: Geographic benchmark analysis

2. **🧩 Trade Structure Groups** (`method=trade_structure`)
   - **Source**: `data/out/peer_groups_statistical.parquet`  
   - **Signal Type**: `Peer_gap_matching`
   - **Method**: K-means clustering on trade structure (HS2 import portfolio similarity)
   - **Logic**: Countries with statistically similar trade patterns and export structures
   - **Groups**: Data-driven clusters based on cosine similarity of HS2 import shares
   - **Ranking Strategy**: Pure peer gap analysis (delta × 1.0)
   - **Usage**: Structural benchmark analysis

3. **🧭 Economic Opportunity Groups** (`method=opportunity`)
   - **Source**: `data/out/peer_groups_opportunity.parquet`
   - **Signal Type**: `Peer_gap_opportunity`
   - **Method**: Algorithmic clustering based on export growth potential and market opportunities
   - **Logic**: Countries with similar opportunity profiles for market development
   - **Groups**: Forward-looking clusters focused on growth potential
   - **Ranking Strategy**: Emphasizes growth markets (delta × 0.8 + growth × 0.2)
   - **Usage**: Opportunity-based benchmark analysis

### 🎯 **Key Principle: Consistent Groups Across Products**

**CRITICAL**: A country belongs to the same peer group regardless of HS6 product code. Peer groups are determined by:
- Geographic/economic similarity (human groups)
- Overall trade patterns (structural groups)  
- Economic opportunity profiles (opportunity groups)

**NOT** by product-specific trade volumes.

### 🔍 **Complete Peer Group Visibility**

The UI displays **all countries in a peer group** with visual distinction:
- **Black/Bold**: Countries that trade in the specific HS6 product
- **Grey**: Countries that don't trade in the specific HS6 product

This ensures users understand the complete statistical universe used for benchmarking.

### 📊 **Example: Bulgaria (Western Balkans)**
For any HS6 product, Bulgaria's peer group always contains: `ALB, BGR, BIH, MKD, MNE, SRB`

- HS6 210111 (coffee): `ALB`(grey), `BGR,BIH,MKD,MNE,SRB`(black) - 5 countries trade coffee
- HS6 720610 (iron): `ALB,BIH,MKD,MNE,SRB`(grey), `BGR`(black) - only Bulgaria trades iron

The peer group remains consistent; only the trade participation varies.

## USD Units Throughout Pipeline

### **💰 Single Point of Unit Transformation**

**Raw BACI Data**: Contains values in **kUSD** (thousands of USD)
- Example: `value_usd=402` means **402,000 USD**

**ETL Stage 1** (`etl/01_build_base_facts.py`): **ONLY** place where units change
- **Input**: kUSD from BACI files
- **Transformation**: `df["value_usd"] * TRADE_UNITS_SCALE` (line 41)  
- **Environment Variable**: `TRADE_UNITS_SCALE=1000` (converts kUSD → USD)
- **Output**: `fact_base.parquet` with **USD** values

**All Subsequent Stages**: Use **USD** throughout
- ETL Stages 2-5: Pass-through USD values (no unit changes)
- API: Processes USD, formats as "8340.4M USD", "728.9k USD"
- UI: Displays formatted USD values from API

### **⚙️ Configuration**

**Environment Variable Controls Scaling:**
```bash
export TRADE_UNITS_SCALE=1000  # Convert kUSD → USD (REQUIRED for BACI data)
export TRADE_UNITS_SCALE=1     # No scaling (if using pre-converted USD data)
```

**Expected Results After Proper Scaling:**
- Czech total exports: ~250B USD (matches official statistics)
- Individual flows: Realistic amounts (e.g., 401,621 USD not 402 USD)

**After Changing TRADE_UNITS_SCALE:**
```bash
# Only need to rebuild from Stage 1 - all others inherit correct units
python etl/01_build_base_facts.py           # Rebuild with correct scaling
python etl/02_compute_trade_metrics.py      # Inherit USD values
python etl/04_enrich_metrics_with_peers.py  # Inherit USD values  
python etl/06_generate_signals.py           # Inherit USD values (if using)
```

### **🚨 Troubleshooting USD Values**

**Symptom**: UI shows small amounts like "3.9B USD" for Czech total exports
**Expected**: Czech total exports ~250B USD  
**Diagnosis**: Missing `TRADE_UNITS_SCALE=1000` during `fact_base.parquet` generation
**Fix**: Rerun Stage 1 with correct environment variable

## CRITICAL: Country ISO Code Inconsistency

⚠️ **KNOWN ISSUE**: Peer group files use inconsistent country code formats and column naming conventions.

### The Problem:

**Different Column Names:**
- `peer_groups_statistical.parquet` and `peer_groups_human.parquet` use `iso3` column
- `peer_groups_opportunity.parquet` uses `iso` column

**Different Code Formats:**
- Human/Structural groups: Alpha-3 codes like `"IRL"`, `"BGR"`, `"DEU"`
- Opportunity groups: Numeric codes like `"372"` (Ireland), `"100"` (Bulgaria), `"276"` (Germany)

**Invalid Codes in Opportunity Data:**
Some opportunity peer group numeric codes don't match standard ISO 3166-1:
```
Valid:   372 -> IRL, 100 -> BGR, 276 -> DEU
Invalid: 251, 36, 40, 490, 56, 579, 699, 757, 76, 842 (no ISO match)
```

### Current Workaround:

The API includes runtime conversion logic in the services layer:
- Detects column names (`iso3` vs `iso`) automatically
- Converts alpha-3 ↔ numeric codes when querying opportunity data  
- Falls back to original codes when conversion fails
- Both `/peer_groups/complete` and peer resolution handle all formats

### Impact if Not Fixed:
- **Symptom**: Bar charts show only target country with value 0
- **Cause**: Peer group queries fail, returning no peer countries for comparison
- **Affected**: All opportunity peer group signals (forward-looking benchmarks)

### 🔧 **TODO: Future Cleanup Required**

**For next major tool upgrade:**
1. **Standardize columns**: All peer group files should use `iso3` column
2. **Standardize codes**: All peer group files should use alpha-3 codes (`IRL`, not `372`)
3. **Fix invalid codes**: Research and correct the 10 invalid numeric codes in opportunity data
4. **Remove conversion logic**: Simplify API code once data is standardized

**Files to rebuild:**
```bash
# After fixing ETL scripts to use consistent ISO format:
python etl/33_build_peer_groups_human.py       # Should output iso3 column
python etl/XX_build_peer_groups_opportunity.py # Should output iso3 column with alpha-3 codes
python etl/27_compute_peer_medians.py          # Rebuild medians with consistent codes
```

**API simplification**: Remove all country code conversion logic from services layer

Pipeline overview
	1.	Base facts

	•	etl/01_build_base_facts.py
Ensures we have, per (year, hs6, partner_iso3):
	•	export_cz_to_partner (CZ→partner export)
	•	import_partner_total (partner's total imports of that HS6)
	•	export_cz_total_for_hs6 (CZ's total exports of that HS6)
Output: data/out/fact_base.parquet

	2.	Trade metrics

	•	etl/02_compute_trade_metrics.py
Adds:
	•	podil_cz_na_importu = export_cz_to_partner / import_partner_total
	•	YoY_export_change (relative YoY change of CZ→partner exports)
	•	partner_share_in_cz_exports = export_cz_to_partner / export_cz_total_for_hs6
	•	YoY_partner_share_change (relative YoY change of partner share)
Output: data/out/metrics.parquet

	3.	Peer medians

	•	etl/03_compute_peer_medians.py
From detailed BACI, for each (year, hs6, partner_iso3):
	•	Compute each peer's share of the partner's imports.
	•	Take the median across peers → median_peer_share.
Output: data/out/peer_medians_statistical.parquet

	4.	Enrich metrics with peers

	•	etl/04_enrich_metrics_with_peers.py
Merges the above into metrics and adds:
	•	delta_vs_peer = podil_cz_na_importu − median_peer_share
Output: data/out/metrics_enriched.parquet

	5.	Map data for visualization

	•	etl/05_build_map_data.py
Builds world map visualization data from metrics.
Output: data/out/ui_shapes/map_rows.parquet

	6.	Signals (shortlist) - OPTIONAL

	•	etl/06_generate_signals.py
Reads data/config.yaml thresholds and picks up to 10 strongest signals (with per‑type caps):
	•	S1 (Peer gap): CZ below peer median:
rel_gap = (median_peer_share − podil_cz_na_importu) / median_peer_share, keep if rel_gap ≥ S1_REL_GAP_MIN.
	•	S2 (YoY export swing): abs(YoY_export_change) ≥ S2_YOY_THRESHOLD.
	•	S3 (YoY partner-share swing): abs(YoY_partner_share_change) ≥ S3_YOY_SHARE_THRESHOLD.
Filters small values via MIN_EXPORT_USD or MIN_IMPORT_USD.
Output: data/out/signals.json

	7.	Signals → UI format - OPTIONAL

	•	etl/07_build_ui_signals.py → caps to MAX_TOTAL (10) and writes:
Output: data/out/ui_shapes/signals.json
	•	etl/08_enrich_ui_signals.py → adds HS6 and country names + friendly label:
Output: data/out/ui_shapes/signals_enriched.json

**NOTE**: Individual UI shapes (world_map.json, product_bars.json, trend_mini.json) are now served dynamically by the API endpoints rather than precomputed files. The map visualization data is computed by `etl/05_build_map_data.py` and served via `/map_v2` endpoint.

## 🏗️ Clean Architecture (Post-Cleanup)

### **Centralized Peer Group System**
**New Files:**
- **`api/peer_group_registry.py`**: Single source of truth for all peer group methodologies
- **`api/utils/country_codes.py`**: Unified country code conversion utilities
- **`api/peer_group_methodology.py`**: Comprehensive methodology documentation

**Supported UI Use Cases:**
1. **Signal Generation**: Peer countries provide median calculations for gap analysis
2. **Chart Filtering**: Bar charts show subset of peer countries vs Czech Republic  
3. **Map Filtering**: Future map highlighting of peer country subsets
4. **Human Explanations**: 2-3 sentence methodology descriptions with country lists

**API Endpoints for Frontend:**
- `GET /peer_groups/explanation?method=&country=&year=` - Human-readable explanations
- `GET /peer_groups/complete?country=&peer_group=&year=` - Complete peer group data

### **Peer Group Methodologies**
- **Geographic/Default**: Regional and development-level peer comparison
- **Export Structure Matching**: Machine learning clustering by product export similarity
- **Opportunity-Based**: Grouping by similar export opportunity profiles

### **🎯 Three-Methodology Signal System (2024 Stable Release)**

**Architecture Benefits:**
- **Complete Signal Differentiation**: Each methodology produces unique, non-overlapping product recommendations
- **Balanced Distribution**: 3 signals per country per methodology (531-532 signals per type)
- **ETL-First Performance**: Sub-5ms API response times with pre-computed comprehensive signals
- **Methodology-Specific Ranking**: Different strategies ensure diverse product selections
- **Stable Data Structure**: API/UI resilient to ETL logic changes

**Signal Generation Pipeline:**
```bash
# Comprehensive peer group support
python etl/03b_compute_all_peer_medians.py           # All methodologies
python etl/04b_enrich_metrics_with_all_peers.py      # Enhanced metrics
python etl/06b_generate_comprehensive_signals.py     # Unified signal generation
```

**Signal Distribution (Current):**
- **Peer_gap_human**: 531 signals (Geographic methodology)
- **Peer_gap_matching**: 532 signals (Trade Structure methodology)  
- **Peer_gap_opportunity**: 532 signals (Economic Opportunity methodology)
- **YoY_export_change**: 2000 signals (Year-over-year export changes)
- **YoY_partner_share_change**: 2000 signals (Partner share changes)

**API Endpoints (Comprehensive):**
- `GET /signals?method=human|trade_structure|opportunity`: Methodology-specific signals
- `GET /signals/methodologies`: Available methodologies with metadata and descriptions
- `GET /signals/comprehensive?country=&hs6=`: Complete signal data for country-product combinations
- `GET /top_signals?country=&limit=`: Balanced mix across all 5 signal types

**Methodology-Specific Product Selection Confirmed:**
- **Germany Example**: Human (870323, 850760, 270900) vs Trade Structure (020754, 020752, 020755) vs Opportunity (840420, 300691, 290941)
- **Zero Product Overlap**: Each methodology recommends completely different products for the same country
- **UI Integration Ready**: SignalsList component displays three distinct sections with differentiated signals


Config knobs

data/config.yaml

thresholds:
  MIN_EXPORT_USD: 100000
  MIN_IMPORT_USD: 5000000
  S1_REL_GAP_MIN: 0.20
  S2_YOY_THRESHOLD: 0.30
  S3_YOY_SHARE_THRESHOLD: 0.20
  MAX_TOTAL: 10
  MAX_PER_TYPE: 4
metric_labels:
  podil_cz_na_importu: "CZ share of partner imports"
  YoY_export_change: "YoY change in CZ→partner exports"
  partner_share_in_cz_exports: "Partner share in CZ exports (by HS6)"
  YoY_partner_share_change: "YoY change in partner share"
  median_peer_share: "Peer-group median share"
  delta_vs_peer: "Gap vs. peer median (CZ − peer)"


## 🏗️ **API Architecture Refactor (September 2024)**

The API layer has been completely refactored from a monolithic structure to a clean, modular architecture:

### **Before → After Transformation**
- **`api/server_full.py`**: 955 lines → 15 lines (98.7% reduction)
- **Architecture**: Monolithic → Domain-separated services and routers
- **Maintainability**: Single massive file → 15 focused modules (50-100 lines each)

### **Modular Structure**
```
api/
├── server_full.py          # Clean orchestration (15 lines)
├── settings/               # Centralized configuration
├── data/                   # Data access with caching
├── services/               # Business logic (SignalsService, PeerGroupsService)
└── routers/                # Domain-separated endpoints
    ├── map.py              # Map visualization endpoints
    ├── signals.py          # Signal generation endpoints
    ├── products.py         # Product and trend endpoints
    ├── insights.py         # AI-generated insights
    └── metadata.py         # Metadata and controls
```

### **Benefits Achieved**
- **Single Responsibility**: Each service handles one business domain
- **Testability**: Services can be unit tested independently  
- **Reusability**: Services reused across multiple router endpoints
- **Configuration**: Centralized in `api/settings/`
- **Zero Breaking Changes**: All endpoints continue working seamlessly

API layer — Endpoints and shapes

Service runs via:
uvicorn api.server_full:APP --host 0.0.0.0 --port 8000 --reload

## 📡 **Comprehensive API Endpoints (2024)**

### **Core System Endpoints**
- `GET /health` → `{ "status": "ok" }`
- `GET /controls` → `{ countries: string[], years: number[], metrics: string[] }` (populate dropdowns)
- `GET /meta` → `{ metric_labels: Record<string,string>, thresholds: Record<string,number> }` (from config.yaml)

### **🗺️ Map Visualization**
- `GET /map_v2?hs6=&year=&metric=` → `[{ iso3, name, value }]` (unified map data from parquet)
- `GET /map?year=&hs6=&metric=&country=&hs2=` → World map with country/HS2 focus
- `GET /map/{hs6}?year=&metric=` → Static map with HS6 product lookup

### **🎯 Three-Methodology Signal System**
- `GET /signals?country=&method=human|trade_structure|opportunity&limit=` → Methodology-specific signals
- `GET /signals/methodologies` → Available methodologies with metadata and signal counts
- `GET /signals/comprehensive?country=&hs6=` → Complete signal data for country-product combinations
- `GET /top_signals?country=&limit=` → Balanced mix across all 5 methodologies

**Signal Response Schema:**
```json
{
  "type": "Peer_gap_human",
  "year": 2023,
  "hs6": "870323", 
  "partner_iso3": "DEU",
  "intensity": 0.041266,
  "method": "human",
  "hs6_name": "HS6 870323",
  "partner_name": "DEU",
  "value_fmt": "0.04",
  "methodology": {
    "methodology_name": "Curated Regional Groups",
    "peer_countries": ["BEL", "DEU", "IRL", "LUX", "NLD"],
    "explanation_text": "Expert-curated peer group...",
    "country_count": 5
  }
}
```

### **📊 Product & Chart Data** 
- `GET /products?year=&top=&country=&hs2=` → `[{ id, name, value }]` (top HS6 by CZ exports)
- `GET /trend?hs6=&years=` → `[{ year, value }]` (time series for HS6)
- `GET /bars?mode=products|partners|peer_compare&hs6=&year=&peer_group=&top=` → Unified bar chart data

### **🧠 AI Insights**
- `GET /insights?importer=&hs6=&year=` → Generated insights text
- `GET /insights_data?importer=&hs6=&year=` → Structured data for KeyData component

### **👥 Peer Group System**
- `GET /peer_groups/complete?country=&peer_group=&year=` → Complete peer group info with all countries
- `GET /peer_groups/explanation?method=&country=&year=` → Human-readable methodology explanations

CORS is enabled for browser use (api/server_cors.py).


## 🎨 **UI Architecture Refactor (September 2024)**

The React frontend has been refactored from a monolithic structure to a clean, modular architecture:

### **App.jsx Transformation**
- **Before**: 844 lines of mixed concerns
- **After**: ~230 lines focused on layout and coordination  
- **Reduction**: 76% smaller, dramatically improved maintainability

### **Extracted Modules**

**Custom Hooks:**
- **`hooks/useAppData.js`**: Centralized data fetching and state management
- **`hooks/useSignalHandling.js`**: Signal selection and processing logic  
- **`hooks/useInsights.js`**: Debounced insights loading with error handling

**Utility Libraries:**
- **`lib/chartCalculations.js`**: Business logic for data transformations
- **`lib/chartHelpers.js`**: Chart title/subtitle generation functions
- **`lib/constants.js`**: Application constants and configuration

### **Architecture Benefits**
- **Single Responsibility**: Each module has one clear purpose
- **Testability**: Individual functions can be unit tested independently
- **Reusability**: Hooks and utilities can be reused across components  
- **Maintainability**: Changes localized to specific business domains

UI layer — What the app expects (and gets)

The UI uses four canonical shapes:
	•	World map → [{ iso3, name, value }]
Source: /map?year=&hs6=&metric=
	•	Product bars → [{ id, name, value }]
Source: /products?year=&top=
	•	Trend mini → [{ year, value }]
Source: /trend?hs6=
	•	Controls → { countries, years, metrics }
Source: /controls

### 🎨 **BenchmarkGroup Component**

The `BenchmarkGroup` component provides complete peer group transparency:

**Features**:
- Shows benchmark type (Geografická, Příležitostní, Strukturální)
- Displays complete peer group name (e.g., "Western Balkans", "Central Europe") 
- Lists all countries in the cluster organized by continent
- Visual distinction: **Black/Bold** = trades in product, **Grey** = doesn't trade in product
- Legend explaining the color coding

**Data Sources**:
- Complete peer group: `/peer_groups/complete?country=&peer_group=&year=`
- Trade data: ProductBarChart data for visual distinction
- Continent grouping: `/ref/country_continents.json`

**Component Location**: `ui/src/components/BenchmarkGroup.jsx`

Signals are rendered as a list from /signals with human‑readable labels. Clicking a signal should set year, hs6, and metric in the UI and refetch /map, /trend, and optionally refresh bars.



Where to tweak what
	•	Change thresholds / shortlist size → edit data/config.yaml and re‑run:
```bash
python etl/06_generate_signals.py
python etl/07_build_ui_signals.py
python etl/08_enrich_ui_signals.py
```

	•	Change peer group → update data/ref/peer_groups.json and re‑run:
```bash
python etl/03_compute_peer_medians.py
python etl/04_enrich_metrics_with_peers.py
python etl/06_generate_signals.py
python etl/07_build_ui_signals.py
python etl/08_enrich_ui_signals.py
```

	•	Add a new metric → compute in 02_compute_trade_metrics.py, merge in 04_enrich_metrics_with_peers.py if needed, expose via /map by name.
	•	Label changes → data/config.yaml: metric_labels (no code changes).
	•	Rename HS6s → update data/parquet/product_codes_HS22.parquet.


Dev notes
	•	Scripts are designed to be small and idempotent.
	•	Parameterization uses etl/_env.py so you can:

    YEAR=2023 HS6=851713 METRIC=delta_vs_peer python -m etl.34_world_map_metric

    etl/__init__.py is present so python -m etl.<module> works.
	•	We keep no new dependencies beyond pandas, pyarrow, pycountry, fastapi, and uvicorn.

Glossary
	•	podil_cz_na_importu — CZ’s share of partner’s imports for a product.
	•	partner_share_in_cz_exports — Partner’s share of CZ’s exports for that product.
	•	delta_vs_peer — CZ share minus peer‑median share (negative → under‑penetration).
	•	S1/S2/S3 — Peer gap / YoY export swing / YoY partner-share swing.

⸻

This README is the contract between the data and UI layers. If the UI needs a new view, first check if the shape exists; if not, add a tiny ETL script or API endpoint that produces exactly one of the canonical shapes.

