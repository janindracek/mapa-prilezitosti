import React, { useState, useEffect, useCallback, useRef } from "react";
import Controls from "./components/Controls.jsx";
import SignalsList from "./components/SignalsList.jsx";
import WorldMap from "./components/WorldMap.jsx";
import ProductBarChart from "./components/ProductBarChart.jsx";
import KeyData from "./components/KeyData.jsx";
import SignalInfo from "./components/SignalInfo.jsx";
import HelpButton from "./components/HelpButton.jsx";
import AnalyticsTable from "./components/AnalyticsTable.jsx";

// Hooks and utilities
import { useAppData } from "./hooks/useAppData.js";
import { useSignalHandling } from "./hooks/useSignalHandling.js";
import { useInsights } from "./hooks/useInsights.js";
import { barChartTitle, barChartSubtitle } from "./lib/chartHelpers.js";
import { ISO3_TO_NAME } from "./lib/constants.js";


export default function App() {
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
  const [view, setView] = useState('overview'); // 'overview' | 'analytics'
  
  const insights = useInsights(selectedId, selectedHS6, panelVM, state, signals);
  
  if (import.meta?.env?.DEV) {
    // Sanity: insights should not start loading before any signal is selected.
    console.assert(!selectedId, 'On initial mount, no signal should be selected automatically.');
  }




  // Each dataset reloads only when ITS inputs change. The previous single
  // effect re-ran on every selection change and refetched everything (8×
  // top_signals / 7× bars / 4× map_v2 per click), flooding the free-tier API
  // and re-rendering the charts continuously.
  useEffect(() => {
    if (!state.country) return;
    loadSignals(state.country).catch((e) => console.error("[signals load] failed", e));
  }, [state.country, loadSignals]);

  // Ensure we have an HS6 before any selection (smartphones as default).
  useEffect(() => {
    if (!hs6 && !selectedHS6) setHs6("851713");
  }, [hs6, selectedHS6, setHs6]);

  const effectiveHs6 = selectedHS6 || hs6;

  useEffect(() => {
    if (!state.year || !state.country || !effectiveHs6) return;
    loadMapData(state.year, effectiveHs6, mapMetric).catch((e) => console.error("[map load] failed", e));
  }, [state.year, state.country, effectiveHs6, mapMetric, loadMapData]);

  useEffect(() => {
    if (!state.year || !state.country) return;
    loadProductData(state.year, state.country).catch((e) => console.error("[products load] failed", e));
  }, [state.year, state.country, loadProductData]);

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

  // Stable handler identities: echarts-for-react deep-compares onEvents with
  // fast-deep-equal (functions by reference), so a fresh closure per render
  // forced a full chart dispose + re-init on EVERY re-render — the flicker.
  // "Latest ref" pattern: the identity passed down NEVER changes, while the
  // ref always points at a closure over current state (handleCountryClick
  // itself changes identity whenever hs6/selectedHS6 change).
  const countryClickRef = useRef(null);
  useEffect(() => {
    countryClickRef.current = (countryIso3, countryName) =>
      handleCountryClick(countryIso3, countryName, savedHS6Codes, referenceData, state);
  });
  const onMapCountryClick = useCallback(
    (countryIso3, countryName) => countryClickRef.current?.(countryIso3, countryName),
    []
  );
  const onBarSelect = useCallback((id) => setHs6(id), [setHs6]);

  // Options for the Controls component (fallbacks if controls not loaded yet)
  const countries = (controls.countries && controls.countries.length) ? controls.countries : ["BEL"];
  const selectedCountry = state.country || null;

  // Get selected signal - either from signals list or create synthetic for HS6 selection
  let selectedSignal = Array.isArray(signals) ? signals.find((x) => x.id === selectedId) || null : null;
  
  // If no signal selected but HS6 is selected, create synthetic signal for display
  if (!selectedSignal && selectedHS6) {
    const hs6Item = Array.isArray(savedHS6Codes) ? savedHS6Codes.find(c => c.code === selectedHS6) : null;
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

      {/* Tabs: overview dashboard vs the full-set analytics table (M5) */}
      <div style={{ display: "flex", gap: 8, borderBottom: "2px solid #e9ecef", marginBottom: 4 }}>
        {[["overview", "Přehled"], ["analytics", "Analytika"]].map(([v, lbl]) => (
          <button
            key={v}
            onClick={() => setView(v)}
            style={{
              padding: "8px 18px", fontSize: 15, fontWeight: 600, cursor: "pointer",
              border: "none", background: "transparent",
              color: view === v ? "#008C00" : "#666",
              borderBottom: view === v ? "3px solid #008C00" : "3px solid transparent",
            }}
          >
            {lbl}
          </button>
        ))}
      </div>

      {view === 'analytics' && (
        <AnalyticsTable referenceData={referenceData} />
      )}

      {view === 'overview' && (
      <>
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
                    const codeItem = action === 'add' ? data : (Array.isArray(savedHS6Codes) ? savedHS6Codes.find(c => c.code === data) : null);
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
            <div>
              <ProductBarChart
                data={(panelVM.barData && panelVM.barData.length) ? panelVM.barData : productData}
                title={(panelVM.barData && panelVM.barData.length)
                  ? barChartTitle(panelVM.meta || {}, panelVM.meta?.signalType)
                  : `Top 10 produktů českého exportu — ${referenceData.countryNames?.[state.country] || state.country}${state.year ? `, ${state.year}` : ''}`}
                subtitle={(panelVM.barData && panelVM.barData.length)
                  ? barChartSubtitle(panelVM.meta?.signalType, panelVM.partnerCounts)
                  : "Největší produkty (HS6) českého exportu do vybrané země\nHodnoty: objem exportu v USD"}
                selectedId={(panelVM.barData && panelVM.barData.length) ? selectedCountry : null}
                onSelect={onBarSelect}
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
                    Český podíl na importu produktu (%)
                    <HelpButton id="cz_share_in_partner_import" size={15} />
                  </label>
                  <label style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 14 }}>
                    <input
                      type="radio"
                      value="export_value_usd"
                      checked={mapMetric === 'export_value_usd'}
                      onChange={(e) => setMapMetric(e.target.value)}
                    />
                    Český export produktu do země (USD)
                    <HelpButton id="export_value_usd" size={15} />
                  </label>
                </div>
              </div>
              
              {/* Render from worldData's own metric/hs6 (what the rows were
                  fetched for), not the radio state — the radio flips instantly
                  while data lags, which used to format share decimals with the
                  USD formatter ("0 USD" on every country). */}
              <WorldMap
                data={worldData.rows}
                metric={worldData.metric || mapMetric}
                nameMap={ISO3_TO_NAME}
                czechNames={referenceData.countryNames}
                nameField='name'
                meta={{ hs6: worldData.hs6 || effectiveHs6, year: state.year }}
                onCountryClick={onMapCountryClick}
              />

            </div>
          </div>
        </div>

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
      </>
      )}
    </div>
  );
}