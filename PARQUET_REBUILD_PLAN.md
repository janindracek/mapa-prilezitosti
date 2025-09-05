# Clean Parquet Rebuild Plan

## Current Issues Found:
1. **ETL corruption**: World total ≠ sum of bilaterals in fact_base.parquet
2. **Signal corruption**: Signal values 9x higher than actual bilateral exports  
3. **Data inconsistency**: Multiple sources showing different values for same trade

## Required Parquets for App:

### Core Data Processing:
1. **`fact_base.parquet`** - Foundation bilateral trade data
   - Columns: year, hs6, partner_iso3, export_cz_to_partner, import_partner_total, export_cz_total_for_hs6
   - Source: Raw BACI parquet files
   - **MUST FIX**: Ensure export_cz_total_for_hs6 = sum(export_cz_to_partner) for each (year, hs6)

2. **`metrics_enriched.parquet`** - Base + calculated metrics + peer data
   - Source: fact_base.parquet + peer medians
   - Columns: All fact_base + podil_cz_na_importu, YoY_*, delta_vs_peer, etc.

### Signal Generation:
3. **`top_signals.parquet`** - Precomputed signals for UI
   - **MUST FIX**: Signal values must match bilateral exports from fact_base
   - Used by: `/top_signals` API endpoint

### UI Shape Data:
4. **`ui_shapes/map_rows.parquet`** - World map visualization data  
5. **`ui_shapes/signals_enriched.json`** - UI signal data with names

### Peer Analysis:
6. **`peer_groups.parquet`** - Country peer clustering
7. **`peer_medians.parquet`** - Peer median market shares
8. **`human_peer_medians.parquet`** - Geographic peer medians

## Clean Rebuild Strategy:

### Phase 1: Core Data Foundation
```bash
# 1. Clean rebuild from raw BACI
python etl/10_build_base.py  # FIXED VERSION
python etl/20_compute_metrics.py
python etl/26_merge_peer_into_metrics.py
```

### Phase 2: Signal Generation  
```bash
# 2. Generate signals from clean metrics
python etl/41_signals_with_peer.py  # FIXED VERSION
python etl/28_build_top_signals.py  # FIXED VERSION
```

### Phase 3: UI Data
```bash
# 3. Build UI shapes
python etl/30_map_rows.py
python etl/31_build_ui_signals.py
python etl/32_enrich_ui_signals.py
```

## Critical Fixes Needed:

### Fix 1: ETL Base Calculation
File: `etl/10_build_base.py`
- **Issue**: World total calculation inconsistent
- **Fix**: Ensure proper aggregation and verification

### Fix 2: Signal Value Mapping  
File: `etl/28_build_top_signals.py`
- **Issue**: Signal values don't match bilateral exports
- **Fix**: Use correct source fields for signal values

### Fix 3: Data Validation
Add validation at each step:
- World total >= any bilateral export
- Signal values match source data
- No duplicate or missing keys

## Recommended Action:
**FULL REBUILD** - The incremental approach led to data corruption.
Clean rebuild will take ~30 minutes but ensure data integrity.