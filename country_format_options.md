# Country Code Standardization Options

## Current State Summary

**Core Trade Data**: Alpha-3 codes (BEL, DEU, etc.) ✅ **GOOD**
- `fact_base.parquet`: Uses alpha-3 codes
- `metrics.parquet`: Uses alpha-3 codes

**Peer Groups**: **3 DIFFERENT FORMATS** ❌ **PROBLEMATIC**
- `peer_groups_human.parquet`: Alpha-3 codes (BEL, DEU)
- `peer_groups_hs2.parquet`: Country names (Belgium, Germany)  
- `peer_groups_opportunity.parquet`: Unpadded numeric (56, 276)

## Option 1: **Alpha-3 Standard** (RECOMMENDED)

### Target State:
- **ALL systems use alpha-3 codes**: CZE, DEU, BEL, USA, etc.
- **Single conversion service** for boundary cases (UI display, external APIs)

### Changes Required:

#### ETL Pipeline:
1. **`create_peer_groups_hs2.py`**: 
   - Add country name → alpha-3 conversion
   - Output `iso3` column instead of `country_name`

2. **`create_peer_groups_opportunity.py`**: 
   - Add numeric → alpha-3 conversion using pycountry
   - Output `iso3` column instead of `iso`

#### API Layer:
3. **`api/data/loaders.py`**:
   - Simplify to expect `iso3` column in all peer group files
   - Remove format conversion logic
   - Standardize column name handling

4. **`api/peer_group_registry.py`**:
   - Remove numeric code conversion logic
   - Expect alpha-3 codes throughout

#### UI Layer:
5. **No changes needed** - UI already uses alpha-3 codes

### Benefits:
- **Eliminates Belgium-type bugs** caused by numeric padding issues
- **Simplifies codebase** - removes conversion logic
- **Human-readable** - easier debugging
- **Standard format** - consistent with international practices
- **Future-proof** - easy to extend and maintain

### Effort: **Medium** (1-2 days)
- Modify 2 ETL scripts
- Update API loaders
- Regenerate 2 parquet files
- Test all peer group endpoints

## Option 2: **Padded Numeric Standard**

### Target State:
- ALL systems use padded numeric codes: 203, 276, 056, 840

### Changes Required:
- Convert core trade data from alpha-3 → numeric
- Update UI to work with numeric codes
- Extensive pycountry padding handling

### Benefits:
- Matches original BACI data format
- Potentially smaller storage

### Drawbacks:
- **Major UI overhaul required**
- **Not human-readable**
- **Padding issues remain**
- **More complex error debugging**

### Effort: **High** (3-4 days)

## Option 3: **Keep Mixed Formats + Better Conversion**

### Target State:
- Keep current formats but improve conversion logic

### Benefits:
- Minimal ETL changes

### Drawbacks:
- **Conversion bugs remain**
- **Complex maintenance**
- **Technical debt accumulates**

### Effort: **Low** (few hours) but **high ongoing maintenance cost**

## Recommendation: **Option 1 (Alpha-3 Standard)**

### Implementation Plan:

#### Phase 1: ETL Updates (4-6 hours)
1. Update `etl/create_peer_groups_hs2.py` to output alpha-3 codes
2. Update `etl/create_peer_groups_opportunity.py` to convert numeric → alpha-3  
3. Regenerate peer group parquet files

#### Phase 2: API Simplification (2-3 hours)
4. Simplify `api/data/loaders.py` to expect consistent `iso3` columns
5. Remove conversion logic from `api/peer_group_registry.py`
6. Test all peer group methodologies

#### Phase 3: Validation (1 hour)
7. Run comprehensive peer group validation
8. Test Belgium and other affected countries
9. Verify UI functionality

#### Total Effort: **7-10 hours**

### Result:
- **Clean, consistent system** with single country code format
- **Eliminates current bugs** (Belgium opportunity peer groups, etc.)
- **Reduces complexity** and maintenance overhead
- **Improves developer experience** with readable country codes