// Data management hook extracted from App.jsx
import { useState, useEffect, useCallback } from 'react';
import { fetchControls, fetchMap, fetchBars } from '../lib/api.js';

export function useAppData() {
  // Controls from backend
  const [controls, setControls] = useState({ countries: [], years: [], metrics: [], metric_labels: {} });

  // Reference data (loaded once centrally)
  const [referenceData, setReferenceData] = useState({
    countryNames: {},
    hs6Labels: {},
    continents: {},
    loading: true
  });

  // Current selection (defaults will be set after controls load)
  const [state, setState] = useState({ country: "", year: 2023 });

  // Data for widgets
  const [worldData, setWorldData] = useState([]);
  const [productData, setProductData] = useState([]);

  // Load controls and reference data centrally
  useEffect(() => {
    (async () => {
      try {
        // Load controls
        const c = await fetchControls();
        setControls(c);
        const country = "BEL"; // Start with Belgium
        const year = 2023;      // fixed latest year
        setState({ country, year });

        // Load reference data once centrally
        const loadRef = (path) =>
          fetch(path)
            .then(r => (r.ok ? r.json() : {}))
            .catch(e => {
              console.error(`[Reference Data] ${path} failed:`, e);
              return {};
            });
        const [countryNamesRes, hs6LabelsRes, continentsRes] = await Promise.all([
          loadRef('/ref/country_names_cz.json'),
          loadRef('/ref/hs6_labels.json'),
          loadRef('/ref/country_continents.json'),
        ]);

        setReferenceData({
          countryNames: countryNamesRes || {},
          hs6Labels: hs6LabelsRes || {},
          continents: continentsRes || {},
          loading: false
        });

      } catch (e) {
        console.error("[controls/reference] failed", e);
        // Still set reference data as loaded even if failed, with empty objects
        setReferenceData({
          countryNames: {},
          hs6Labels: {},
          continents: {},
          loading: false
        });
      }
    })();
  }, []);

  // Helper: adapt server signals to SignalsList shape
  const adaptSignals = useCallback((list) => {
    return (list || []).map((s, i) => ({
      id: `${s.type}_${s.hs6}_${s.partner_iso3}_${i}`,
      label: `${s.type}: ${(s.hs6_name || s.hs6)} → ${(s.partner_name || s.partner_iso3)}`,
      score: typeof s.intensity === "number" ? Number(s.intensity) : 0,
      // extra fields for KeyData
      type: s.type,
      hs6: s.hs6,
      hs6_name: s.hs6_name,
      partner_iso3: s.partner_iso3,
      partner_name: s.partner_name,
      // IMPORTANT: Copy the actual data fields we need!
      value: s.value,           // Trade value (USD)
      yoy: s.yoy,              // Year-over-year percentage change
      intensity: s.intensity,   // Signal intensity/strength
      year: s.year,            // Signal year
    }));
  }, []);

  const loadMapData = useCallback(async (year, hs6, mapMetric) => {
    if (!year || !hs6) return;
    const world = await fetchMap({ year, hs6, metric: mapMetric });
    setWorldData(world);
  }, []);

  const loadProductData = useCallback(async (year, country) => {
    if (!year || !country) return;
    const bars = await fetchBars({ mode: 'products', year, top: 10, country });
    setProductData(bars);
  }, []);

  return {
    controls,
    referenceData,
    state,
    setState,
    worldData,
    productData,
    adaptSignals,
    loadMapData,
    loadProductData
  };
}