// Signal handling hook extracted from App.jsx
import { useState, useEffect, useCallback } from 'react';
import { fetchBars, fetchTopSignals } from '../lib/api.js';
import { API_BASE } from '../lib/constants.js';

async function tryFetchTopSignals(country) {
  try {
    const data = await fetchTopSignals({ country });
    if (!Array.isArray(data)) return null;
    console.debug("[top_signals] rows:", data.length, data.slice(0, 2));
    return data;
  } catch (e) {
    console.warn("[top_signals] fetch failed:", e);
    return null;
  }
}

export function useSignalHandling(adaptSignals) {
  const [signals, setSignals] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [hs6, setHs6] = useState("");
  
  // HS6 manual selection state
  const [savedHS6Codes, setSavedHS6Codes] = useState([]);
  const [selectedHS6, setSelectedHS6] = useState(null);

  const [panelVM, setPanelVM] = useState({
    keyData: null,
    barData: [],
    mapData: [],
    meta: {},
    partnerCounts: {}
  });

  // Load saved HS6 codes from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem('mapa_prilezitosti_hs6_codes');
      if (saved) {
        const codes = JSON.parse(saved);
        if (Array.isArray(codes)) {
          setSavedHS6Codes(codes);
        }
      }
    } catch (e) {
      console.warn('Failed to load saved HS6 codes:', e);
    }
  }, []);

  // Save HS6 codes to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem('mapa_prilezitosti_hs6_codes', JSON.stringify(savedHS6Codes));
    } catch (e) {
      console.warn('Failed to save HS6 codes:', e);
    }
  }, [savedHS6Codes]);

  // HS6 change handler
  function handleHS6Change(action, data) {
    if (action === 'add') {
      const { code, label } = data;
      const newCode = {
        code,
        label,
        id: `hs6_${code}_${Date.now()}`,
        timestamp: Date.now()
      };
      setSavedHS6Codes(prev => [...prev, newCode]);
      
      // Immediately select and analyze the new code
      setSelectedHS6(code);
      handleHS6Selection(code, label);
      
    } else if (action === 'select') {
      setSelectedHS6(data);
      const codeItem = savedHS6Codes.find(c => c.code === data);
      if (codeItem) {
        handleHS6Selection(data, codeItem.label);
      }
      
    } else if (action === 'delete') {
      setSavedHS6Codes(prev => prev.filter(c => c.code !== data));
      if (selectedHS6 === data) {
        setSelectedHS6(null);
      }
    }
  }

  // Handle HS6 selection - create synthetic YoY_export_change signal
  function handleHS6Selection(hs6Code, hs6Label, state) {
    // Clear signal selection when HS6 is selected
    setSelectedId(null);
    
    // Create synthetic signal that behaves like YoY_export_change
    const syntheticSignal = {
      id: `hs6_synthetic_${hs6Code}`,
      type: 'YoY_export_change',
      hs6: hs6Code,
      hs6_name: hs6Label,
      partner_iso3: state.country,
      partner_name: state.country,
      value: 0, // Will be populated by API
      yoy: 0,   // Will be populated by API
      intensity: 0,
      year: state.year,
      label: `${hs6Code} - ${hs6Label} → ${state.country}`
    };
    
    // Use existing signal handling logic
    handleRealSignalClick(syntheticSignal, state);
  }

  const loadSignals = useCallback(async (country) => {
    if (!country) return;
    
    // Load signals first (but don't auto-select anything) - Use only precomputed signals for consistency
    let rows = await tryFetchTopSignals(country);
    if (!rows) {
      console.warn(`[signals] No precomputed signals for ${country}, using empty array`);
      rows = [];
    }
    console.debug("[signals] before adapt:", rows?.length, rows?.map(r => r?.type));
    const adapted = adaptSignals(rows);
    console.debug('[signals] adapted:', adapted?.length, adapted?.slice(0, 2));
    setSignals(adapted);
  }, [adaptSignals]);

  const handleRealSignalClick = useCallback(async (signal, state) => {
    console.group('[handleRealSignalClick] Processing signal:', signal);
    
    const curHs6 = signal.hs6;
    const curPartner = signal.partner_iso3;
    const curYear = signal.year || state.year;
    
    if (!curHs6 || !curPartner || !curYear) {
      console.warn('Missing required fields:', { curHs6, curPartner, curYear });
      console.groupEnd();
      return;
    }

    try {
      // Fetch complete insights data for KeyData component
      const base = API_BASE || 'http://127.0.0.1:8000';
      const url = `${base}/insights_data?importer=${encodeURIComponent(curPartner)}&hs6=${encodeURIComponent(curHs6)}&year=${encodeURIComponent(curYear)}`;
      
      console.log('Fetching insights data from:', url);
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const insightsData = await response.json();
      
      console.log('Received insights data:', insightsData);
      
      // Create comprehensive keyData with all required fields
      const keyData = {
        // Basic bilateral data from insights_data endpoint  
        cz_to_c: insightsData.cz_to_c || null,
        cz_world_total: insightsData.cz_world_total || null,
        
        // Missing fields now populated from insights_data endpoint
        c_import_total: insightsData.c_import_total,
        cz_share_in_c: insightsData.cz_share_in_c, 
        median_peer_share: insightsData.median_peer_share,
        
        // YoY percentage from signal (only if it's a valid number)
        cz_delta_pct: (typeof (signal.yoy || signal.intensity) === 'number' && !isNaN(signal.yoy || signal.intensity)) ? (signal.yoy || signal.intensity) : null
      };
      
      console.log('Constructed keyData:', keyData);
      
      // Fetch bar data for the signal type only
      let barData = [];
      let partnerCounts = {};
      
      if (signal.type?.includes('Peer_gap')) {
        // For benchmark signals: show all countries in the peer group with correct peer group type
        let peerGroupType = 'default';
        if (signal.type === 'Peer_gap_human') {
          peerGroupType = 'human';
        } else if (signal.type === 'Peer_gap_opportunity') {
          peerGroupType = 'opportunity'; 
        } else if (signal.type === 'Peer_gap_matching') {
          peerGroupType = 'matching';
        }
        barData = await fetchBars({ mode: 'peer_compare', hs6: curHs6, year: curYear, country: curPartner, peer_group: peerGroupType, top: 50 });
        
        // Calculate partner counts
        const allPartners = await fetchBars({ mode: 'partners', hs6: curHs6, year: curYear, country: curPartner, peer_group: null, top: 200 });
        partnerCounts = {
          totalPartners: allPartners?.length || 0,
          peerGroupPartners: barData?.length || 0
        };
      } else if (signal.type === 'YoY_export_change') {
        // For YoY export change: show top 10 CZ export partners + selected country (no peer group filtering)
        barData = await fetchBars({ mode: 'partners', hs6: curHs6, year: curYear, country: curPartner, peer_group: null, top: 10 });
        
        const allPartners = await fetchBars({ mode: 'partners', hs6: curHs6, year: curYear, country: curPartner, peer_group: null, top: 200 });
        partnerCounts = {
          totalPartners: allPartners?.length || 0,
          peerGroupPartners: barData?.length || 0
        };
      } else if (signal.type === 'YoY_partner_share_change') {
        // For YoY partner share change: show top 10 CZ export partners + selected country (no peer group filtering)
        barData = await fetchBars({ mode: 'partners', hs6: curHs6, year: curYear, country: curPartner, peer_group: null, top: 10 });
        
        const allPartners = await fetchBars({ mode: 'partners', hs6: curHs6, year: curYear, country: curPartner, peer_group: null, top: 200 });
        partnerCounts = {
          totalPartners: allPartners?.length || 0,
          peerGroupPartners: barData?.length || 0
        };
      }

      // Update the hs6 state so the main useEffect can fetch map data for this HS6
      setHs6(curHs6);
      
      setPanelVM({
        mapData: [], // Map data is now handled independently by radio buttons
        barData: barData || [],
        keyData,
        meta: { hs6: curHs6, year: curYear, signalType: signal.type },
        partnerCounts
      });
      
      console.log('Updated panelVM with new keyData and set hs6 to:', curHs6);
      
    } catch (error) {
      console.error('Failed to handle signal click:', error);
      
      // Fallback: create basic keyData with no fake numbers
      const keyData = {
        cz_to_c: null,
        cz_world_total: null,
        c_import_total: null,
        cz_share_in_c: null, 
        median_peer_share: null,
        cz_delta_pct: null
      };
      
      setPanelVM(prev => ({
        ...prev,
        keyData,
        meta: { hs6: curHs6, year: curYear, metric: 'unknown', signalType: signal.type },
        partnerCounts: {}
      }));
    }
    
    console.groupEnd();
  }, []);

  // Handle country click from WorldMap - create synthetic signal
  const handleCountryClick = useCallback((countryIso3, countryName, savedHS6Codes, referenceData, state) => {
    const currentHs6 = selectedHS6 || hs6;
    if (!currentHs6) {
      console.warn('[Country Click] No HS6 available to create signal');
      return;
    }

    // Get HS6 label for display
    const hs6Item = selectedHS6 ? savedHS6Codes.find(c => c.code === selectedHS6) : null;
    const hs6Label = hs6Item?.label || referenceData.hs6Labels?.[currentHs6] || currentHs6;

    // Create synthetic signal combining clicked country + current HS6
    const syntheticSignal = {
      id: `country_click_${countryIso3}_${currentHs6}_${Date.now()}`,
      type: 'YoY_export_change', // Default signal type for country+HS6 combinations
      hs6: currentHs6,
      hs6_name: hs6Label,
      partner_iso3: countryIso3,
      partner_name: countryName,
      value: 0, // Will be populated by API
      yoy: 0,   // Will be populated by API
      intensity: 0,
      year: state.year,
      label: `${currentHs6} - ${hs6Label} → ${countryName}`
    };

    console.log('[Country Click] Creating synthetic signal:', syntheticSignal);

    // Add the synthetic signal to the signals list so it shows as selected
    setSignals(prevSignals => {
      // Remove any existing synthetic signals and add the new one at the top
      const filteredSignals = prevSignals.filter(s => !s.id.startsWith('country_click_') && !s.id.startsWith('hs6_synthetic_'));
      return [syntheticSignal, ...filteredSignals];
    });

    // Set this as the selected signal
    setSelectedId(syntheticSignal.id);
    setSelectedHS6(null); // Clear manual HS6 selection since we're now using a signal

    // Process the synthetic signal like any other signal
    handleRealSignalClick(syntheticSignal, state);
  }, [selectedHS6, hs6, handleRealSignalClick]);

  return {
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
  };
}