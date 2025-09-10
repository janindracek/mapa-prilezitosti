# Mapa Příležitostí - UI

React + Vite frontend for the Czech trade opportunities analysis platform.

## 🏗️ **Architecture**

The UI is built with React 18 and Vite, consuming data from a FastAPI backend.

### Key Components

#### 📊 **Main Dashboard Components**
- **`App.jsx`**: Main application container with modular architecture
- **`Controls.jsx`**: Country selection and HS6 manual input interface
- **`SignalsList.jsx`**: Displays trade opportunity signals with filtering
- **`WorldMap.jsx`**: ECharts world map visualization
- **`ProductBarChart.jsx`**: Top trading partners bar chart
- **`KeyData.jsx`**: Key metrics display with 3x2 mini-tiles layout

#### 🏗️ **Modular Architecture (September 2024 Refactor)**

**Custom Hooks:**
- **`hooks/useAppData.js`**: Data fetching and reference data management
- **`hooks/useSignalHandling.js`**: Signal selection, HS6 codes, synthetic signals
- **`hooks/useInsights.js`**: Debounced insights loading with error handling

**Utility Libraries:**
- **`lib/chartCalculations.js`**: Business logic for chart data transformations
- **`lib/chartHelpers.js`**: Chart title/subtitle generation functions  
- **`lib/constants.js`**: Application constants and configuration
- **`lib/api.js`**: API client functions (existing)

#### 🔍 **Analysis Components**
- **`SignalInfo.jsx`**: Signal information and methodology explanations
- **`KeyData.jsx`**: Key metrics display with trade statistics
- **Modular architecture**: Separated concerns with custom hooks

### 📡 **API Integration**

#### Core Data Endpoints
- `/controls` - Countries, years, metrics for dropdowns
- `/map_v2` - World map choropleth data
- `/products` - Top trading partners
- `/signals` - Trade opportunity signals
- `/peer_groups/complete` - **Complete peer group information**

#### Data Flow
1. **Signal Selection**: User selects trade signal or manual HS6 code
2. **Data Fetching**: Parallel API calls for map, chart, and peer group data  
3. **Visual Updates**: Components update with Czech localization and formatting
4. **Signal Information**: SignalInfo provides methodology context and explanations

### 🌍 **Localization**

- **Czech Interface**: All UI elements in Czech language
- **Number Formatting**: Czech locale (`cs-CZ`) with decimal commas
- **Currency**: USD values formatted as "mil. USD", "mld. USD", "tis. USD"
- **Country Names**: Czech country names from `/ref/country_names_cz.json`
- **Product Names**: Czech HS6 labels from `/ref/hs6_labels.json`

### 🎨 **Data Visualization**

The UI provides comprehensive trade data visualization:

- **WorldMap**: Interactive choropleth with country-level trade metrics
- **ProductBarChart**: Top trading partners with value comparisons
- **SignalInfo**: Contextual information about trade opportunities
- **KeyData**: Summary statistics in tile format

## 🚀 **Development**

```bash
npm install
npm run dev
```

## 🧪 **Key Features**

### **Enhanced Peer Group Integration (September 2024)**
- **Human-Readable Explanations**: 2-3 sentence methodology descriptions for each peer group type
- **Complete Country Lists**: Shows all peer countries with clear methodology context
- **Multiple Analysis Frameworks**: Geographic, export-structure matching, and opportunity-based groupings
- **API-Driven Explanations**: New `/peer_groups/explanation` endpoint provides rich methodology context

### **Core Features**
- **Complete Peer Group Visibility**: Shows all countries in benchmark groups, not just active traders
- **Visual Trade Distinction**: Clear indication of which peer countries actually trade specific products  
- **Czech Localization**: Fully localized interface with proper number formatting
- **HS6 Manual Input**: Users can analyze custom product codes beyond suggested signals
- **Responsive Design**: Flexible layout that adapts to different screen sizes
- **Modular Architecture**: Clean separation of concerns with custom hooks and utility libraries
- **Maintainable Codebase**: 76% reduction in main App component complexity after cleanups

## 🔧 **Architecture Benefits**

### **Single Responsibility**
- Each module handles one clear domain (data fetching, signal handling, calculations)
- Easier to locate and modify specific functionality

### **Testability** 
- Individual functions and hooks can be unit tested independently
- Business logic separated from UI rendering

### **Reusability**
- Custom hooks can be reused across components
- Utility functions centralized for consistent behavior

### **Maintainability**
- Main App.jsx focuses on layout and coordination with modular structure
- Changes localized to specific modules

## 📝 **Component Props**

### SignalInfo
```javascript
<SignalInfo
  signal={selectedSignal}          // Current signal object
  country={selectedCountry}        // Target country ISO3  
  year={selectedYear}              // Year for context
/>
```

### KeyData  
```javascript
<KeyData
  data={keyMetricsData}            // Trade metrics object
  signal={selectedSignal}          // For HS6/country context
  country={selectedCountry}        // Country ISO3
  year={selectedYear}              // Year for context
/>
```
