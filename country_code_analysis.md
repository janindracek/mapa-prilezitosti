# Country Code Format Analysis

## Current State: Multiple Inconsistent Formats

The application currently uses **at least 3 different country code formats** throughout the system, causing conversion issues and bugs.

## 1. ETL Layer & Data Files

### Raw Data Sources (input):
- **BACI Trade Data**: Uses **numeric ISO codes** (e.g., 203 for Czech Republic)
- **Reference Files**: Mixed formats

### Generated Parquet Files (output):
- **`fact_base.parquet`**: Uses **numeric ISO codes** (203, 276, 840, etc.)
- **`metrics.parquet`**: Uses **numeric ISO codes** 
- **`peer_groups_human.parquet`**: Uses **alpha-3 codes** (CZE, DEU, USA)
- **`peer_groups_hs2.parquet`**: Uses **country names** (Czech Republic, Germany, United States)
- **`peer_groups_opportunity.parquet`**: Uses **unpadded numeric codes** (203, 276, 840 → 56, 276, 840)

### ETL Scripts:
- Use mixed formats depending on data source
- Convert between formats ad-hoc during processing

## 2. API Layer

### Data Loaders (`api/data/loaders.py`):
- **`load_peer_groups()`**: Handles **3 different column formats**:
  - Human: `iso3` column (alpha-3 codes)  
  - Trade Structure: `country_name` column (full names)
  - Opportunity: `iso` column (unpadded numeric codes)

### Country Code Conversion (`api/utils/country_codes.py`):
- Provides conversion utilities between formats
- Used inconsistently across codebase

### API Endpoints:
- **Input**: Receive **alpha-3 codes** from UI (CZE, BEL, DEU)
- **Processing**: Convert to various formats depending on data source
- **Output**: Return mixed formats depending on endpoint

## 3. UI Layer

### Frontend (`ui/src/`):
- **Controls.jsx**: Filters countries, uses **mixed formats** (numeric for Czech exclusion)
- **API Calls**: Send **alpha-3 codes** to backend
- **Display**: Show **country names** to users
- **Country Selection**: Uses **alpha-3 codes** internally

### Reference Data:
- **Country lists**: Mixed formats in different JSON files

## 4. Current Issues Caused by Format Inconsistency

### Belgium Opportunity Peer Group Bug:
1. UI sends "BEL" to API
2. API converts "BEL" → "056" (padded numeric)  
3. Opportunity data has "56" (unpadded numeric)
4. Lookup fails, returns empty peer group

### Similar Issues Affecting:
- All countries with leading zeros in numeric codes (001-099)
- Cross-methodology peer group comparisons
- Data integrity validation

## 5. Country Code Format Options

### Option A: **Alpha-3 Codes (ISO 3166-1 alpha-3)**
- **Examples**: CZE, DEU, USA, BEL, FRA
- **Pros**: 
  - Human-readable
  - Standard international format
  - No leading zero issues
  - Consistent length (3 chars)
- **Cons**: 
  - Requires conversion from numeric BACI data
  - Larger storage space than numeric

### Option B: **Padded Numeric Codes (ISO 3166-1 numeric)**
- **Examples**: 203, 276, 840, 056, 250
- **Pros**: 
  - Matches BACI source data format
  - Smaller storage space
  - No conversion needed from source
- **Cons**: 
  - Not human-readable
  - Leading zero padding issues
  - Requires careful string handling

### Option C: **Unpadded Numeric Codes**
- **Examples**: 203, 276, 840, 56, 250
- **Pros**: 
  - Simpler integer handling
  - Matches some current data
- **Cons**: 
  - Inconsistent with ISO standard
  - Conversion issues with pycountry
  - Not human-readable

### Option D: **Country Names**
- **Examples**: Czech Republic, Germany, United States
- **Pros**: 
  - Human-readable
  - No encoding issues
- **Cons**: 
  - Inconsistent naming (official vs common names)
  - Larger storage space
  - Language/locale issues
  - Fuzzy matching required

## 6. Recommended Approach

**Standardize on Alpha-3 Codes (Option A)** throughout the entire system:

### Benefits:
1. **Human-readable** - easier debugging and development
2. **Standard format** - consistent with international practices
3. **No padding issues** - eliminates current Belgium-type bugs
4. **UI-friendly** - matches current UI usage patterns
5. **Consistent length** - easier validation and processing

### Implementation Strategy:
1. **Single Source of Truth**: Create unified country code translation service
2. **ETL Layer**: Convert numeric codes → alpha-3 at data ingestion
3. **API Layer**: Use alpha-3 codes internally, convert only at boundaries
4. **UI Layer**: Continue using alpha-3 codes (minimal changes needed)
5. **Data Files**: Migrate all parquet files to use alpha-3 codes

### Conversion Plan:
1. Create comprehensive country code mapping service
2. Update ETL pipeline to standardize on alpha-3
3. Migrate existing parquet files
4. Update API data loaders
5. Verify UI compatibility
6. Test all peer group methodologies

This would eliminate the current web of ad-hoc conversions and create a clean, consistent system.