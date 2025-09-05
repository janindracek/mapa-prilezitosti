# Trade Opportunity Map - Application Flow

This document describes the complete user interaction flow and data dependencies in the trade opportunity mapping application.

## Overview

The application helps users identify trade opportunities by analyzing Czech trade data. Users select a country, view relevant trade signals, and explore detailed trade metrics when they click on specific signals.

## Application Flow

### 1. Initial Load & Country Selection

**User Action:** Opens the application
- App starts with Belgium (BEL) as the default country and 2023 as the year
- Controls component loads country list from `/ref/countries.json` with Czech translations
- Countries are grouped by continent and sorted using Czech locale

**User Action:** Selects a different country from dropdown
- `Controls.jsx` handles country selection via `onChange` prop
- Updates `state.country` in main App component

### 2. Signals Loading

**Triggered by:** Country selection or app initialization
- App fetches trade signals for the selected country via two mechanisms:
  1. **Primary:** `/top_signals?country={country}` - precomputed signals (faster)
  2. **Fallback:** `/signals?country={country}&limit=300&peer_group=all` - live computation

**Signal Processing:**
- Signals are filtered and grouped into 5 types (max 3 per type):
  - `YoY_export_change` - "Nárůst exportu" 
  - `YoY_partner_share_change` - "Navýšení podílu na exportu"
  - `Peer_gap_opportunity` - "Benchmark (statistický, pohled vpřed)"
  - `Peer_gap_matching` - "Benchmark (statistický, pohled současný)" 
  - `Peer_gap_human` - "Benchmark (geografický)"

- Each signal contains: `type`, `hs6`, `partner_iso3`, `intensity`, product/country names
- `SignalsList.jsx` displays signals grouped by type with Czech labels and icons

### 3. Signal Selection & UI Updates

**User Action:** Clicks on a signal in the signals list
- `selectedId` state is updated
- `demoFireSignal()` function transforms the signal into appropriate format
- `handleSignalClick()` is called with signal data

**Signal Click Processing:** Based on signal type, different data flows are triggered:

#### For Peer Gap Signals (Peer_gap_*)
- Converts to `Peer_import_gap` type internally
- Calculates supplier market share data using `calcSupplierShareByPartner()`
- Fetches additional data:
  - World map: `/map_v2?hs6={hs6}&year={year}&metric=cz_share_in_partner_import`
  - Bar chart: `/bars_v2?mode=peer_compare&hs6={hs6}&year={year}&country={country}`

#### For Export Growth Signals (YoY_export_change)
- Calculates year-over-year export changes using `calcDeltaExportByPartner()`
- Fetches additional data:
  - World map: `/map_v2?hs6={hs6}&year={year}&metric=delta_export_abs`  
  - Bar chart: `/bars_v2?mode=import_change&hs6={hs6}&year={year}&country={country}`

#### For Partner Share Signals (YoY_partner_share_change)
- Calculates partner share in CZ exports using `calcShareInCzExportsByPartner()`
- Fetches additional data:
  - World map: `/map_v2?hs6={hs6}&year={year}&metric=partner_share_in_cz_exports`
  - Bar chart: `/bars_v2?mode=import_change&hs6={hs6}&year={year}&country={country}`

### 4. UI Component Updates

**After signal selection, following components update:**

#### KeyData Component
- Shows basic facts about the selected signal:
  - HS6 code and product name (from `hs6_labels.json`)
  - Czech exports to world (USD)  
  - Country's total imports (USD)
  - Czech share of country's imports (%)

#### WorldMap Component  
- Updates with new geographic data based on signal type
- Shows color-coded world map with trade metrics
- Displays current country value at bottom

#### ProductBarChart Component
- Shows top 10 countries/partners for the selected product (HS6)
- Title changes based on metric type
- Highlights the selected country if present in top 10

#### Insights Panel
- **Triggered by:** Signal selection with 1-second debounce
- Fetches AI-generated insights: `/insights?importer={country}&hs6={hs6}&year={year}`
- Shows loading state, then displays trade insights text
- Only loads after explicit user signal selection (not on initial load)

### 5. Default Data Loading

**Parallel to signals loading:**
- World map loads with default HS6 and `delta_vs_peer` metric
- Product bar chart shows top 10 products for selected country/year
- Trend chart shows export trends for current HS6 over 10 years
- Focus row shows selected country's value for current metric

## Data Dependencies

### API Endpoints Used:
- `/controls` - Available countries, years, metrics
- `/signals` - Trade signals for country  
- `/top_signals` - Precomputed top signals (faster)
- `/map` - World map data for visualization
- `/map_v2` - Enhanced map data with specific metrics
- `/products` - Top products by exports 
- `/bars_v2` - Bar chart data with different modes
- `/trend` - Export trends over time
- `/insights` - AI-generated trade insights

### Reference Data:
- `/ref/countries.json` - Country list
- `/ref/country_names_cz.json` - Czech country names
- `/ref/country_continents.json` - Country-continent mapping  
- `/ref/hs6_labels.json` - Product code descriptions

## State Management

**Main App State:**
- `state` - { country, year }
- `signals` - Array of processed signals
- `selectedId` - ID of selected signal
- `panelVM` - { keyData, barData, mapData, meta } - Panel view model
- `worldData`, `productData`, `trendData` - Default visualization data
- `insights` - { text, loading, error } - AI insights state

**Key State Flows:**
1. Country change → signals reload → UI updates
2. Signal click → panelVM update → all visualization components update  
3. Signal selection → insights fetch (debounced)

## Error Handling

- API failures fall back to local calculations where possible
- Missing data shows "–" or placeholder text
- Network errors are logged to console in development mode
- Insights loading shows error messages to user

---

*This flow description is based on code analysis. Please review for accuracy and completeness.*