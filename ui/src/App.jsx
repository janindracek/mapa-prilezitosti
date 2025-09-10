import React, { useState, useEffect } from "react";
import Controls from "./components/Controls.jsx";
import SignalsList from "./components/SignalsList.jsx";
import WorldMap from "./components/WorldMap.jsx";
import ProductBarChart from "./components/ProductBarChart.jsx";
import KeyData from "./components/KeyData.jsx";
import SignalInfo from "./components/SignalInfo.jsx";

// Hooks and utilities
import { useAppData } from "./hooks/useAppData.js";
import { useSignalHandling } from "./hooks/useSignalHandling.js";
import { useInsights } from "./hooks/useInsights.js";
import { barChartTitle, barChartSubtitle } from "./lib/chartHelpers.js";
import { ISO3_TO_NAME, SHOW_SKELETON } from "./lib/constants.js";



export default function App() {
  console.log("[UI] App mounted");
  
  // Use custom hooks
  const { controls, referenceData, state, setState, worldData, productData, adaptSignals, loadMapData, loadProductData } = useAppData();
  
  const {
    signals,
    selectedId,
    setSelectedId, 
    hs6,
    setHs6,
    savedHS6Codes,
    selectedHS6,
    setSelectedHS6,
    panelVM,
    handleHS6Change,
    handleHS6Selection,
    loadSignals,
    handleRealSignalClick,
    handleCountryClick
  } = useSignalHandling(adaptSignals);
  
  const [mapMetric, setMapMetric] = useState('cz_share_in_partner_import');
  
  const insights = useInsights(selectedId, selectedHS6, panelVM, state, signals);
  
  if (import.meta?.env?.DEV) {
    // Sanity: insights should not start loading before any signal is selected.
    console.assert(!selectedId, 'On initial mount, no signal should be selected automatically.');
  }




  // Load data when selection changes
  useEffect(() => {
    const { year, country } = state;
    if (!year || !country) return;

    (async () => {
      try {
        // Load signals
        await loadSignals(country);
        
        // Ensure we have an HS6: pick top product for the country/year if needed
        let currentHs6 = hs6;
        if (!currentHs6 && !selectedHS6) {
          // Fallback to smartphones if no HS6 available
          currentHs6 = "851713";
          // Only set if it would actually change the value to prevent loops
          if (hs6 !== currentHs6) {
            setHs6(currentHs6);
          }
        }

        // Use selectedHS6 if available, otherwise use currentHs6
        const effectiveHs6 = selectedHS6 || currentHs6;
        if (effectiveHs6) {
          // Always fetch map data for the current HS6 and selected metric
          await loadMapData(year, effectiveHs6, mapMetric);
        }

        // Top 10 products for the selected country/year
        await loadProductData(year, country);

      } catch (e) {
        console.error("[data load] failed", e);
      }
    })();
  }, [state.country, state.year, selectedId, selectedHS6, hs6, mapMetric, loadSignals, loadMapData, loadProductData]);

  // Handle country change - create synthetic signal when country changes and we have a selected HS6
  const [previousCountry, setPreviousCountry] = useState(null);
  useEffect(() => {
    if (previousCountry && state.country && previousCountry !== state.country) {
      // Country changed - check if we have a selected HS6 to create synthetic signal
      const effectiveHs6 = selectedHS6 || hs6;
      if (effectiveHs6) {
        console.log('[Country Change] Creating synthetic signal for new country:', state.country, 'with HS6:', effectiveHs6);
        const countryName = referenceData.countryNames?.[state.country] || state.country;
        handleCountryClick(state.country, countryName, savedHS6Codes, referenceData, state);
      }
    }
    setPreviousCountry(state.country);
  }, [state.country, selectedHS6, hs6, handleCountryClick, savedHS6Codes, referenceData, state, previousCountry]);

  // Options for the Controls component (fallbacks if controls not loaded yet)
  const countries = (controls.countries && controls.countries.length) ? controls.countries : ["BEL"];
  const selectedCountry = state.country || null;

  // Get selected signal - either from signals list or create synthetic for HS6 selection
  let selectedSignal = signals.find((x) => x.id === selectedId) || null;
  
  // If no signal selected but HS6 is selected, create synthetic signal for display
  if (!selectedSignal && selectedHS6) {
    const hs6Item = savedHS6Codes.find(c => c.code === selectedHS6);
    if (hs6Item) {
      selectedSignal = {
        id: `hs6_synthetic_${selectedHS6}`,
        type: 'YoY_export_change',
        hs6: selectedHS6,
        hs6_name: hs6Item.label,
        partner_iso3: state.country,
        partner_name: state.country,
        year: state.year,
        label: `${selectedHS6} - ${hs6Item.label}`
      };
    }
  }



  return (
    <div style={{ padding: 20, display: "grid", gap: 16 }}>
      
      {/* Main Title */}
      <h1 style={{ 
        fontFamily: "Montserrat", 
        fontSize: 32, 
        fontWeight: "bold", 
        color: "#008C00", 
        margin: "0 0 24px 0",
        textAlign: "center"
      }}>
        Obchodní příležitosti Česka
      </h1>

      {/* STEP 1: Empty layout skeleton for the new design (no behavior change) */}
      {SHOW_SKELETON && (
        <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 0, marginBottom: 16 }}>
          {/* Left column skeleton */}
          <div style={{ display: "grid", gap: 12, gridTemplateRows: "auto 1fr auto", paddingRight: 8 }}>
            <div>
              <Controls
                countries={countries}
                country={state.country}
                year={state.year}
                onChange={(next) =>
                  setState((prev) => ({ ...prev, ...next, year: Number(next.year || prev.year || 2023) }))
                }
                savedHS6Codes={savedHS6Codes}
                selectedHS6={selectedHS6}
                onHS6Change={(action, data) => {
                  if (action === 'add' || action === 'select') {
                    const codeItem = action === 'add' ? data : savedHS6Codes.find(c => c.code === data);
                    if (codeItem) {
                      handleHS6Selection(codeItem.code, codeItem.label, state);
                    }
                  }
                  handleHS6Change(action, data);
                }}
                referenceData={referenceData}
              />
            </div>
            <div style={{ wordWrap: "break-word", overflowWrap: "anywhere" }}>
              <SignalsList
                signals={signals}
                selectedId={selectedId}
                onSelect={(item) => { 
                  setSelectedId(item.id); 
                  setSelectedHS6(null); // Clear HS6 selection when signal is selected
                  handleRealSignalClick(item, state); 
                }}
                referenceData={referenceData}
              />
              <div style={{ marginTop: 12 }}>
                <SignalInfo
                  signal={selectedSignal}
                  country={state.country}
                  year={state.year}
                  referenceData={referenceData}
                />
              </div>
            </div>
          </div>
          {/* Right column skeleton */}
          <div style={{ display: "grid", gap: 12, gridTemplateRows: "auto auto 1fr", paddingLeft: 8 }}>
            <KeyData
              data={panelVM.keyData}
              signal={selectedSignal}
              country={state.country}
              year={state.year}
              referenceData={referenceData}
              onSaveCode={handleHS6Change}
              savedHS6Codes={savedHS6Codes}
            />
            {/* TODO: Re-enable BenchmarkGroup component later */}
            {/* <BenchmarkGroup
              signal={selectedSignal}
              productData={(panelVM.barData && panelVM.barData.length) ? panelVM.barData : productData}
              country={state.country}
              referenceData={referenceData}
            /> */}
            <div>
              <ProductBarChart
                data={(panelVM.barData && panelVM.barData.length) ? panelVM.barData : productData}
                title={barChartTitle((panelVM.mapData && panelVM.mapData.length) ? (panelVM.meta || {}) : { hs6, year: state.year, metric: 'delta_export_abs' }, panelVM.meta?.signalType)}
                subtitle={barChartSubtitle(panelVM.meta?.signalType, panelVM.partnerCounts)}
                selectedId={(panelVM.barData && panelVM.barData.length) ? selectedCountry : null}
                onSelect={(id) => setHs6(id)}
                referenceData={referenceData}
              />
            </div>
            <div>
              {/* Map metric selection radio buttons */}
              <div style={{ 
                marginBottom: 12, 
                padding: 8, 
                background: "#f8f9fa", 
                borderRadius: 4, 
                border: "1px solid #e9ecef" 
              }}>
                <div style={{ fontWeight: "bold", marginBottom: 6, fontSize: 14 }}>
                  Zobrazit na mapě:
                </div>
                <div style={{ display: "flex", gap: 16 }}>
                  <label style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 14 }}>
                    <input
                      type="radio"
                      value="cz_share_in_partner_import"
                      checked={mapMetric === 'cz_share_in_partner_import'}
                      onChange={(e) => setMapMetric(e.target.value)}
                    />
                    Český podíl na importu země (%)
                  </label>
                  <label style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 14 }}>
                    <input
                      type="radio"
                      value="export_value_usd"
                      checked={mapMetric === 'export_value_usd'}
                      onChange={(e) => setMapMetric(e.target.value)}
                    />
                    Celková hodnota českého exportu do země (USD, 2023)
                  </label>
                </div>
              </div>
              
              {import.meta?.env?.DEV && console.debug('[WorldMap data sample]', worldData?.[0])}
              <WorldMap
                data={worldData}
                metric={mapMetric}
                nameMap={ISO3_TO_NAME}
                nameField='name'
                meta={{ hs6: selectedHS6 || hs6, year: state.year }}
                onCountryClick={(countryIso3, countryName) => handleCountryClick(countryIso3, countryName, savedHS6Codes, referenceData, state)}
              />
              
            </div>
          </div>
        </div>
      )}

      {/* Bottom insights section with title and warning */}
      <div style={{ border: "1px solid #eee", borderRadius: 6, padding: 12, background: "#fff", minHeight: 220 }}>
        <div style={{ fontFamily: "Montserrat", fontWeight: "bold", marginBottom: 8, fontSize: 18, color: "#008C00" }}>Kontext země a produktu</div>
        <div style={{ marginBottom: 12, color: "red", fontSize: 14, fontWeight: "bold" }}>VAROVÁNÍ: obsah vygenerovaný automaticky skrz LLM; správnost není zaručena</div>
        <div style={{ textAlign: "left", whiteSpace: "pre-wrap", fontSize: 16, lineHeight: 1.5 }}>
          {insights.loading ? "Načítání kontextu…" : (insights.text || "Žádný kontext není k dispozici pro tento výběr.")}
        </div>
        {insights.error && (
          <div style={{ marginTop: 8, color: "#a00", fontSize: 12 }}>Error: {String(insights.error)}</div>
        )}
      </div>
    </div>
  );
}