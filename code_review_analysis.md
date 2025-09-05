# Code Review Analysis - Data Sources and Potential Inconsistencies

## 📂 **Available Parquet Files**

### Core Data Files
- `data/out/metrics_enriched.parquet` - Main metrics with peer analysis
- `data/out/metrics.parquet` - Basic metrics (fallback)
- `data/out/fact_base.parquet` - Base trade facts

### Peer Group Files
- `data/out/peer_groups.parquet` - Structural peer groups (k-means)
- `data/out/peer_groups_human.parquet` - Geographic peer groups
- `data/out/peer_groups_opportunity.parquet` - Opportunity-based peer groups

### Medians & Analysis
- `data/out/peer_medians.parquet` - Default peer medians
- `data/out/human_peer_medians.parquet` - Human peer group medians
- `data/out/metrics_peer_medians.parquet` - Combined metrics with medians

### UI & Signals
- `data/out/top_signals.parquet` - Precomputed top signals
- `data/out/ui_shapes/map_rows.parquet` - Map visualization data

### Raw Data
- `data/parquet/BACI_HS22_Y2022_V202501/data.parquet`
- `data/parquet/BACI_HS22_Y2023_V202501/data.parquet`
- `data/parquet/product_codes_HS22.parquet`

---

## 🌐 **API Endpoints**

### Currently Active Endpoints
- `/map_v2` - Advanced map data
- `/insights` - AI-generated insights
- `/insights_data` - Raw insights data
- `/meta` - Configuration metadata
- `/controls` - UI dropdowns data
- `/map` - Basic map data
- `/products` - Top products
- `/trend` - Time series trends
- `/signals` - Dynamic signals
- `/top_signals` - Precomputed signals
- `/map/{hs6}` - Legacy compatibility
- `/peer_groups/complete` - Complete peer group info
- `/debug/peer_groups` - Debug peer data
- `/bars_v2` - Advanced bar chart data

---

## 🎨 **UI Data Usage**

### Main Data Flows
1. **Controls**: `/controls` → dropdown populations
2. **Signals**: `/top_signals` + `/signals` → signal selection
3. **Map**: `/map` + `/map_v2` → world visualization
4. **Charts**: `/products` + `/bars_v2` → bar charts
5. **Trends**: `/trend` → time series
6. **Insights**: `/insights` → AI analysis
7. **Peer Groups**: `/peer_groups/complete` → benchmark analysis

---

## ⚠️ **IDENTIFIED INCONSISTENCIES & RISKS**

### 1. **Duplicate Map Endpoints**
**ISSUE**: UI uses both `/map` and `/map_v2` for different scenarios
- `/map`: Used in general data loading (App.jsx:556,699,718,728)
- `/map_v2`: Used in signal-specific scenarios (App.jsx:345,375,406,432)

**RISK**: Different map endpoints might return different data formats or values for the same parameters

**LOCATION**: 
```javascript
// App.jsx - Two different map calls
const world = await fetchMap({ year, hs6: effectiveHs6, metric: MAP_METRIC });    // Line 556
const remote = await fetchMapV2({ hs6: curHs6, year: curYear, metric: 'delta_vs_peer' }); // Line 699
```

### 2. **Multiple Signal Sources**
**ISSUE**: UI tries multiple signal sources with fallback logic
- Primary: `/top_signals?country=${country}` (App.jsx:48)
- Fallback: `/signals` with dynamic computation (App.jsx:524)

**RISK**: Different signal sources might return different signal types, intensities, or rankings

**LOCATION**:
```javascript
// App.jsx:520-525
let rows = await tryFetchTopSignals(country);
if (!rows) {
  const pool = await fetchSignals({ country, limit: 300, peer_group: "all" });
  rows = pickTopNByType(pool, 3);
}
```

### 3. **Peer Group Data Inconsistency**
**ISSUE**: Multiple peer group files with different methodologies
- `peer_groups.parquet` - Structural groups
- `peer_groups_human.parquet` - Geographic groups  
- `peer_groups_opportunity.parquet` - Opportunity groups

**RISK**: UI might request wrong peer group type or API might return inconsistent peer groups

**LOCATION**:
```python
# server_full.py:575-581 - Peer group selection logic
if pg_req == "human":
    pg_path = "data/out/peer_groups_human.parquet"
elif pg_req == "opportunity":
    pg_path = "data/out/peer_groups_opportunity.parquet"
else:
    pg_path = "data/out/peer_groups.parquet"
```

### 4. **Chart Data Source Confusion**
**ISSUE**: Charts use different data sources depending on signal type
- Default: `/products` (basic product data)
- Benchmark signals: `/bars_v2` with peer_group parameter
- Manual HS6: `/bars_v2` without peer_group parameter

**RISK**: Same chart showing different country sets for same product/country combination

**LOCATION**:
```javascript
// App.jsx:709,720,730 - Different bar data calls
barData = await fetchBarsV2({ hs6, year, mode: 'peer_compare', country, peer_group: peerGroupType, top: 50 });
barData = await fetchBarsV2({ hs6, year, mode: 'peer_compare', country, top: 10 }); // No peer_group!
```

### 5. **Metrics Source Inconsistency**
**ISSUE**: API has fallback from enriched to basic metrics
```python
# data_access.py:6-7
METRICS_ENR = Path("data/out/metrics_enriched.parquet")  
METRICS_FALLBACK = Path("data/out/metrics.parquet")
```

**RISK**: If enriched metrics are unavailable, basic metrics might miss peer analysis data

### 6. **Reference Data Loading**
**ISSUE**: Multiple components load same reference files independently
- Country names: `KeyData.jsx`, `ProductBarChart.jsx`, `Controls.jsx`
- HS6 labels: `KeyData.jsx`, `SignalsList.jsx`, `Controls.jsx`
- Continents: `Controls.jsx`, `BenchmarkGroup.jsx`

**RISK**: Race conditions, inconsistent data, unnecessary network requests

---

## 🔧 **RECOMMENDED FIXES**

### Priority 1: Critical Data Consistency
1. **Consolidate Map Endpoints**: Use only `/map_v2` or clearly document when to use each
2. **Standardize Chart Data**: Ensure `/bars_v2` always returns consistent country sets for same inputs
3. **Centralize Reference Data**: Load reference files once in App.jsx and pass down

### Priority 2: Signal Source Reliability  
1. **Fix Signal Fallback**: Ensure both `/top_signals` and `/signals` return same data format
2. **Validate Peer Groups**: Add validation that peer group requests return expected countries

### Priority 3: Performance & UX
1. **Cache Reference Data**: Implement proper caching for country names, HS6 labels, etc.
2. **Add Loading States**: Handle cases where different data sources have different loading times

---

## 🎯 **SPECIFIC ISSUES TO ADDRESS**

### Chart Inconsistency Example
**Scenario**: User selects Bulgaria + Peer_gap_human signal for HS6 720610
- **Map**: Uses peer group filtering, shows Western Balkans comparison
- **Chart**: Might use different peer group or no peer group filtering
- **Result**: Map and chart show different countries, confusing user

### Signal Source Mismatch
**Scenario**: `/top_signals` returns precomputed signals, `/signals` returns live computation
- **Precomputed**: Fixed set of signals with consistent rankings
- **Live**: Dynamic signals that might change based on current data
- **Result**: Signal list might change between page loads

### Reference Data Race Conditions  
**Scenario**: Multiple components load Czech country names simultaneously
- **Risk**: Some components might render before data loads
- **Result**: Inconsistent display of country names across UI components