// Insights hook extracted from App.jsx
import { useState, useEffect } from 'react';
import { API_BASE } from '../lib/constants.js';

export function useInsights(selectedId, selectedHS6, panelVM, state, signals) {
  const [insights, setInsights] = useState({ text: "", loading: false, error: null });

  // Insights: only after explicit signal click or HS6 selection + 1s debounce to avoid request bursts
  useEffect(() => {
    const selectedCountry = state?.country;
    const selectedYear = state?.year;
    const selSignal = signals.find(x => x.id === selectedId) || null;
    const hasSignalSelection = !!selectedId;
    const hasHS6Selection = !!selectedHS6;
    const hasUserSelection = hasSignalSelection || hasHS6Selection;

    // Prefer HS6 from manual selection, then panel meta, then selected signal
    let rawHs6 = "";
    if (selectedHS6) {
      rawHs6 = selectedHS6;
    } else {
      rawHs6 = (panelVM?.meta?.hs6 ?? selSignal?.hs6 ?? "").toString().trim();
    }
    const digits = rawHs6.replace(/\D/g, "");
    const finalHS6 = digits ? digits.padStart(6, "0") : "";

    if (!hasUserSelection || !selectedCountry || !selectedYear || !finalHS6) {
      if (import.meta?.env?.DEV) console.debug('[insights] skip (awaiting explicit selection/params)', { hasUserSelection, selectedCountry, selectedYear, finalHS6 });
      return;
    }

    const ctrl = new AbortController();
    const timerId = setTimeout(async () => {
      try {
        setInsights(prev => ({ ...prev, loading: true, error: null }));
        const base = (API_BASE && String(API_BASE).trim()) || 'http://127.0.0.1:8000';
        const url = `${base}/insights?importer=${encodeURIComponent(selectedCountry)}&hs6=${encodeURIComponent(finalHS6)}&year=${encodeURIComponent(selectedYear)}`;
        const res = await fetch(url, { signal: ctrl.signal });
        const ctype = res.headers.get('content-type') || '';
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        if (!ctype.includes('application/json')) {
          const txt = await res.text();
          throw new Error(`Unexpected response (content-type=${ctype}): ${txt.slice(0,120)}…`);
        }
        const data = await res.json();
        setInsights({ text: data.insight || "No insights available", loading: false, error: null });
      } catch (e) {
        if (e?.name === 'AbortError') return; // canceled due to rapid re-click
        setInsights({ text: "", loading: false, error: String(e?.message || e) });
      }
    }, 1000); // 1s debounce

    return () => {
      clearTimeout(timerId);
      ctrl.abort();
    };
  }, [selectedId, selectedHS6, panelVM.meta?.hs6, state.country, state.year, signals]);

  return insights;
}