# Complete Country Code Analysis

## 🔍 Current System Overview

After comprehensive analysis of **135 files** across ETL, API, and UI layers, here's the complete picture:

## 📊 Country Code Usage by Component

### 1. **UI Layer** (React/JavaScript)

#### **Input/Selection**:
- **Controls.jsx**: Uses **mixed formats** for filtering
  - Filters out Czech Republic using **both '203' and 'CZE'**
  - Country selection dropdown expects **alpha-3 codes** (BEL, DEU, etc.)

#### **Display Components**:
- **WorldMap.jsx**: Handles **ISO3 codes** from API but converts for display
- **ProductBarChart.jsx**: Expects **alpha-3 codes** for country name lookup
- **KeyData.jsx**: Receives **alpha-3 codes** from selected country state
- **SignalInfo.jsx**: Passes **alpha-3 codes** to API endpoints

#### **API Communication**:
- **All API calls** send **alpha-3 codes** (BEL, DEU, USA)
- **Selected country state** in App.jsx stores **alpha-3 codes**

### 2. **API Layer** (Python/FastAPI)

#### **Endpoint Parameters**:
- **`/insights`** and **`/insights_data`**: Accept `importer: str` (expects **alpha-3**)
- **`/peer_groups/explanation`**: Accept `country: str` (expects **alpha-3**)
- **`/bars`**: Accept `country: str` (expects **alpha-3**)
- **`/map_v2`**: All endpoints expect **alpha-3 codes**

#### **Internal Processing**:
- **Core trade data** (`fact_base.parquet`, `metrics.parquet`): Uses **alpha-3 codes**
- **API routers** expect and process **alpha-3 codes**
- **Business logic** works with **alpha-3 codes**

#### **Data Conversion Layer**:
- **`api/data/loaders.py`**: Contains **complex conversion logic** for different data sources
- **`api/utils/country_codes.py`**: Provides conversion utilities (underutilized)

### 3. **ETL Pipeline** (Python)

#### **Core Trade Data**:
- **`fact_base.parquet`**: Uses **alpha-3 codes** ✅
- **`metrics.parquet`**: Uses **alpha-3 codes** ✅

#### **Peer Group Data** (THE PROBLEM AREA):
- **`peer_groups_human.parquet`**: Uses **alpha-3 codes** ✅
- **`peer_groups_hs2.parquet`**: Uses **country names** ❌
- **`peer_groups_opportunity.parquet`**: Uses **unpadded numeric codes** ❌

### 4. **LLM Insights System**

#### **Insights Generation** (`api/insights_text.py`):
- **Input**: Receives **alpha-3 codes** from API endpoints
- **Processing**: Works with **alpha-3 codes** from core trade data
- **Country Name Lookup**: Hardcoded references to "Czech Republic"
- **Output**: Generates text using **alpha-3 codes** internally

#### **Peer Group Median Calculation**:
- **Critical Bug**: Currently fails for some countries due to format mismatches
- **Root Cause**: Inconsistent country code formats in peer group data

## 🚨 **Critical Problems Identified**

### 1. **Belgium Opportunity Bug** (and similar countries):
- UI sends "BEL" → API converts to "056" → Data has "56" → **Lookup fails**

### 2. **Mixed Format Complexity**:
- 3 different formats in peer group data require complex conversion logic
- Conversion failures cause empty peer groups and broken functionality

### 3. **Inconsistent Czech Republic Filtering**:
- UI filters both '203' and 'CZE' formats
- Different data sources store Czech Republic in different formats

### 4. **LLM Context Issues**:
- Peer group median calculations fail due to country code mismatches
- Affects quality of insights and KeyData display

## ✅ **What Works Well**

### **Consistent Alpha-3 Usage**:
- **Core trade data**: Already standardized on alpha-3 codes
- **UI components**: Expect and work with alpha-3 codes  
- **API endpoints**: Designed for alpha-3 codes
- **Main data flow**: UI → API → Core data (all alpha-3)

## 🎯 **Recommended Solution: Alpha-3 Standardization**

### **Why Alpha-3 is the Right Choice**:

1. **Minimal Changes**: 80% of system already uses alpha-3 codes
2. **UI Compatibility**: No UI changes needed
3. **Human Readable**: Easier debugging and development
4. **Standard Format**: International standard (ISO 3166-1 alpha-3)
5. **No Padding Issues**: Eliminates Belgium-type bugs

### **What Needs to Change**:

#### **ETL Layer** (2 files):
- **`create_peer_groups_hs2.py`**: Convert country names → alpha-3 codes
- **`create_peer_groups_opportunity.py`**: Convert numeric → alpha-3 codes

#### **API Layer** (2 files):
- **`api/data/loaders.py`**: Simplify to expect consistent `iso3` columns
- **`api/peer_group_registry.py`**: Remove complex conversion logic

#### **Generated Data** (2 parquet files):
- **`peer_groups_hs2.parquet`**: Regenerate with alpha-3 codes
- **`peer_groups_opportunity.parquet`**: Regenerate with alpha-3 codes

### **Benefits**:
- **Fixes Belgium bug** and all similar issues
- **Eliminates complex conversion logic**
- **Reduces maintenance overhead**
- **Improves system reliability**
- **Makes debugging easier**

### **Estimated Effort**: **6-8 hours**
- ETL updates: 3-4 hours
- API simplification: 2-3 hours  
- Testing and validation: 1 hour

## 📋 **Alternative Options Considered**

### **Option B: Padded Numeric Standard**
- **Pros**: Matches BACI source format
- **Cons**: Major UI overhaul, not human-readable, padding complexity
- **Effort**: 15-20 hours

### **Option C: Keep Mixed + Better Conversion**
- **Pros**: Minimal ETL changes
- **Cons**: Technical debt remains, ongoing maintenance burden
- **Effort**: 2-3 hours initially, high ongoing cost

## 🏁 **Conclusion**

**Alpha-3 standardization is the clear winner**:
- Leverages existing system architecture
- Eliminates root cause of current bugs
- Reduces complexity
- Future-proof solution
- Reasonable effort for major improvement

**Ready to implement once you approve the approach!**