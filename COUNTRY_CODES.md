# Country Code Usage Documentation

## Current State Analysis (December 2024)

### **📊 DATA LAYER - Consistent ISO3 Usage**
- **Signals Data**: `data/out/signals_comprehensive.parquet` uses `partner_iso3` (ISO3)
- **Metrics Data**: `data/out/metrics_all_peers.parquet` uses `partner_iso3` (ISO3)  
- **Reference Data**: `data/ref/country_codes.csv` has full ISO2/ISO3 mappings

✅ **STANDARDIZED**: All data files consistently use ISO3 codes

### **🔧 API LAYER - Normalization at Entry Point**
- **Normalization Function**: `api.normalizers.normalize_iso()` converts input → ISO3
- **API Endpoints**: All accept country parameters and normalize via `normalize_iso()`
- **Internal Processing**: Everything uses ISO3 after normalization

✅ **STANDARDIZED**: Single normalization point at API entry

**Current normalize_iso() behavior**:
```
BEL → BEL    (ISO3 pass-through)
DEU → DEU    (ISO3 pass-through)  
GER → None   (invalid, needs fixing)
FRA → FRA    (ISO3 pass-through)
USA → USA    (ISO3 pass-through)
UK  → None   (invalid, needs fixing)
GB  → GBR    (ISO2 → ISO3 conversion)
GBR → GBR    (ISO3 pass-through)
```

### **🎨 FRONTEND LAYER - Uses API Normalization**  
- **Country Selection**: Users select from country list (likely ISO3)
- **API Calls**: Frontend passes country codes directly to API  
- **Display**: Uses reference data for country names

✅ **STANDARDIZED**: Relies on API normalization

## **🎯 STANDARDIZATION RULES**

### **Rule 1: ISO3 Everywhere**
- **Data files**: Always use ISO3 codes (`partner_iso3`, `country_iso3`, etc.)
- **Internal APIs**: Always work with ISO3 after normalization
- **Database storage**: Always store ISO3

### **Rule 2: Single Normalization Point**
- **Entry Point Only**: Normalize user input at API entry via `normalize_iso()`
- **No Random Normalization**: Never normalize in middle of processing pipeline
- **Pass-Through**: Internal functions assume they receive valid ISO3

### **Rule 3: Reference Data as Source of Truth**
- **Mapping**: Use `data/ref/country_codes.csv` for all ISO2↔ISO3 conversions
- **Display Names**: Use `data/ref/countries.csv` for human-readable names
- **Validation**: Only accept countries present in reference data

## **🚨 CURRENT ISSUES & FIXES NEEDED**

### **Issue 1: Missing Common Code Mappings**
```
GER → None  ❌ Should be: GER → DEU
UK  → None  ❌ Should be: UK → GBR  
```

**Fix**: Enhance `normalize_iso()` with common aliases:
```python
COUNTRY_ALIASES = {
    'GER': 'DEU',  # Germany common alias
    'UK': 'GBR',   # United Kingdom alias
    # Add more as needed
}
```

### **Issue 2: Error Handling**
- **Current**: `normalize_iso('INVALID')` returns `None`
- **Result**: API returns empty results instead of clear error
- **Fix**: Return 400 error for invalid country codes

## **✅ RECOMMENDED IMPLEMENTATION**

### **Enhanced normalize_iso() Function**
```python
def normalize_iso(country_input: str) -> Optional[str]:
    \"\"\"
    Normalize country input to ISO3 code.
    
    Accepts:
    - ISO3 codes (pass-through): USA, DEU, GBR
    - ISO2 codes (convert): US → USA, DE → DEU  
    - Common aliases: GER → DEU, UK → GBR
    
    Returns ISO3 or None if invalid.
    \"\"\"
    # Implementation with alias support
```

### **API Error Handling**
```python
# In API endpoints:
iso3 = normalize_iso(country)
if not iso3:
    raise HTTPException(400, f"Invalid country code: {country}")
```

### **Frontend Country Selection**
- Load countries from `/ref/countries.json` API endpoint
- Display human names, send ISO3 to API
- Handle normalization errors gracefully

## **📋 MIGRATION CHECKLIST**

- [ ] **Fix normalize_iso()** - Add GER→DEU, UK→GBR aliases
- [ ] **Add API validation** - Return 400 for invalid countries  
- [ ] **Test coverage** - Verify all common country codes work
- [ ] **Frontend error handling** - Show clear errors for invalid countries
- [ ] **Documentation** - Update API docs with supported country formats

## **🔍 FILES TO MODIFY**

1. `api/normalizers.py` - Enhance normalize_iso() function
2. `api/routers/signals.py` - Add validation error handling  
3. `ui/src/components/Controls.jsx` - Improve error handling
4. `data/ref/country_codes.csv` - Ensure complete coverage

---
**Key Principle**: Country code normalization happens ONCE at the API entry point. Everything else uses ISO3.