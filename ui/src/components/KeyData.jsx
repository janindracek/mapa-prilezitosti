import React, { useState } from "react";
import KeyDataOverlay from './KeyDataOverlay.jsx';
import { formatCzechUSD, formatPct1, formatSignedPct, formatUsdPair } from "../lib/format.js";

function formatPercentage(value) {
  if (value == null || Number.isNaN(value)) return "—";
  return `${(value * 100).toLocaleString("cs-CZ", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;
}

// YoY delta is already a percentage value (not a 0..1 ratio); format defensively
function formatYoYDelta(value) {
  if (value == null || Number.isNaN(value)) return "—";
  return formatSignedPct(value);
}

export default function KeyData({ 
  data = {}, 
  signal = null, 
  country = null, 
  year = null,
  referenceData = { countryNames: {}, hs6Labels: {}, continents: {}, loading: false },
  onSaveCode = null,
  savedHS6Codes = []
}) {
  const [showKeyDataOverlay, setShowKeyDataOverlay] = useState(false);
  // Use centralized reference data instead of loading independently
  const czechNames = referenceData.countryNames;
  const hs6Labels = referenceData.hs6Labels;
  if (!data || Object.keys(data).length === 0) {
    return (
      <div style={{ border: "1px solid #eee", borderRadius: 6, padding: 12, background: "#fff" }}>
        <h2 style={{ fontFamily: "Montserrat", fontWeight: "bold", marginBottom: 6, fontSize: 18, color: "#008C00" }}>
          Klíčová data
        </h2>
        <div style={{ padding: "6px 8px", color: "#666" }}>
          Vyberte signál pro zobrazení detailů.
        </div>
      </div>
    );
  }

  // Extract HS6 and country info for subtitle
  const hs6Code = signal?.hs6 || '';
  const hs6Name = hs6Labels[hs6Code] || signal?.hs6_name || ''; // Prefer Czech HS6 label
  
  // Get Czech country name
  const countryIso3 = signal?.partner_iso3 || country;
  const countryName = czechNames[countryIso3] || signal?.partner_name || country || '';
  
  // Check if current HS6 code is already saved
  const isCodeSaved = hs6Code && savedHS6Codes.some(item => item.code === hs6Code);
  const canSave = hs6Code && hs6Name && onSaveCode && !isCodeSaved && savedHS6Codes.length < 5;
  
  // Handler for saving the current HS6 code
  const handleSaveCode = () => {
    if (canSave && onSaveCode) {
      onSaveCode('add', { code: hs6Code, label: hs6Name });
    }
  };
  
  // Format HS6 with dot notation
  function formatHs6Dot(code) {
    const raw = String(code ?? '').trim();
    const digits = raw.replace(/\D/g, '');
    if (!digits || digits.length < 6) return code;
    const s = digits.padStart(6, '0');
    return `${s.slice(0,4)}.${s.slice(4)}`;
  }

  const {
    cz_to_c = null,        // Bilateral export to partner
    cz_to_c_prev = null,   // Previous-year bilateral export (may be absent on older API)
    cz_world_total = null, // Total CZ export for this HS6
    c_import_total = null, // Country's total imports for this HS6
    cz_share_in_c = null,  // CZ's share of country's imports
    median_peer_share = null, // Median peer share for comparison
    cz_delta_pct = null    // YoY change percentage
  } = data;

  // Per-signal tile semantics: peer-gap signals get a "share vs median" hero
  // tile, YoY/own-product signals get a "prev → current" hero tile.
  const signalType = signal?.type || '';
  const isSynthetic = !!signal?.synthetic
    || String(signal?.id || '').startsWith('hs6_synthetic_')
    || String(signal?.id || '').startsWith('country_click_');
  const isPeerSignal = !isSynthetic && signalType.includes('Peer_gap');
  const isYoYSignal = isSynthetic
    || signalType === 'YoY_export_change'
    || signalType === 'YoY_partner_share_change';

  // Tile descriptors: { label, value, sub?, subStyle?, hero? }
  let metrics;

  if (isPeerSignal) {
    const hasPair = Number.isFinite(Number(cz_share_in_c)) && Number.isFinite(Number(median_peer_share));
    const gapPb = hasPair ? (Number(cz_share_in_c) - Number(median_peer_share)) * 100 : null;
    const gapTxt = gapPb == null ? null
      : `${gapPb > 0 ? '+' : gapPb < 0 ? '−' : ''}${Math.abs(gapPb).toLocaleString("cs-CZ", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} p. b.`;
    metrics = [
      {
        hero: true,
        label: "Podíl ČR vs medián srovnatelných trhů",
        value: `${formatPct1(cz_share_in_c)} vs ${formatPct1(median_peer_share)}`,
        sub: gapTxt,
        subStyle: { color: gapPb != null && gapPb < 0 ? "#dc2626" : "#008C00", fontWeight: "bold", fontSize: 13 }
      },
      { label: "Export ČR → země", value: formatCzechUSD(cz_to_c) },
      { label: "Celkový export ČR (produkt, svět)", value: formatCzechUSD(cz_world_total) },
      { label: "Import země celkem", value: formatCzechUSD(c_import_total) },
      { label: "Meziroční změna", value: formatYoYDelta(cz_delta_pct) }
    ];
  } else if (isYoYSignal) {
    const cur = Number.isFinite(Number(cz_to_c)) ? Number(cz_to_c) : null;
    const yoy = Number.isFinite(Number(cz_delta_pct)) ? Number(cz_delta_pct) : null;
    // Prefer the real previous-year value from /insights_data; derive it from
    // the YoY % when the field is absent (older API), never when yoy = -100.
    let prev = Number.isFinite(Number(cz_to_c_prev)) ? Number(cz_to_c_prev) : null;
    if (prev == null && cur != null && yoy != null && yoy !== -100) {
      prev = cur / (1 + yoy / 100);
    }
    const sigYear = Number(signal?.year || year) || null;
    const heroLabel = isSynthetic
      ? `Vývoj exportu ČR do země${sigYear ? ` (${sigYear - 1}→${sigYear})` : ''}`
      : "Meziroční změna exportu ČR do země";
    const hasPair = prev != null && cur != null;
    metrics = [
      {
        hero: true,
        label: heroLabel,
        value: hasPair ? formatUsdPair(prev, cur) : formatYoYDelta(cz_delta_pct),
        sub: hasPair && yoy != null ? `(${formatSignedPct(yoy)})` : null,
        subStyle: { color: yoy != null && yoy < 0 ? "#dc2626" : "#008C00", fontWeight: "bold", fontSize: 13 }
      },
      { label: "Export ČR → země", value: formatCzechUSD(cz_to_c) },
      { label: "Celkový export ČR (produkt, svět)", value: formatCzechUSD(cz_world_total) },
      { label: "Import země celkem", value: formatCzechUSD(c_import_total) },
      { label: "Podíl ČR v importu", value: formatPercentage(cz_share_in_c) },
      // Geographic peer median only when it carries signal (>= 0.1 %)
      ...(Number.isFinite(Number(median_peer_share)) && Number(median_peer_share) >= 0.001 ? [{
        label: "Medián srovnatelných trhů",
        value: formatPercentage(median_peer_share),
        sub: "(medián geograficky srovnatelných trhů)",
        subStyle: { color: "#666", fontSize: 10 }
      }] : [])
    ];
  } else {
    // No recognized signal type — legacy 3x2 grid
    metrics = [
      { label: "Export ČR → země", value: formatCzechUSD(cz_to_c) },
      { label: "Celkový export ČR (produkt, svět)", value: formatCzechUSD(cz_world_total) },
      { label: "Import země celkem", value: formatCzechUSD(c_import_total) },
      { label: "Podíl ČR v importu", value: formatPercentage(cz_share_in_c) },
      // Median peer share: 0 is a real value ("peers also export nothing"),
      // only null/NaN means unknown
      { label: "Medián peer group", value: formatPercentage(median_peer_share) },
      // YoY change: only rendered when a real YoY number exists (the hook
      // passes null for non-YoY signals and placeholder zeros)
      { label: "Meziroční změna", value: formatYoYDelta(cz_delta_pct) }
    ];
  }

  return (
    <div style={{ border: "1px solid #eee", borderRadius: 6, padding: 12, background: "#fff" }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        marginBottom: 6 
      }}>
        <h2 style={{ 
          fontFamily: "Montserrat", 
          fontWeight: "bold", 
          fontSize: 18, 
          color: "#008C00",
          margin: 0,
          marginRight: 8
        }}>
          Klíčová data
        </h2>
        <button
          onClick={() => setShowKeyDataOverlay(true)}
          style={{
            width: 20,
            height: 20,
            borderRadius: '50%',
            border: '1px solid #008C00',
            backgroundColor: 'transparent',
            color: '#008C00',
            fontSize: 12,
            fontWeight: 'bold',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 0
          }}
          onMouseOver={(e) => e.target.style.backgroundColor = '#f0f7ff'}
          onMouseOut={(e) => e.target.style.backgroundColor = 'transparent'}
          title="Zobrazit vysvětlení klíčových dat"
          aria-label="Zobrazit vysvětlení klíčových dat"
        >
          ?
        </button>
      </div>
      
      {/* Subtitle with HS6 code/name and country */}
      {(hs6Code || countryName) && (
        <div style={{ 
          marginBottom: 16, 
          fontSize: 14, 
          color: "#000", 
          fontWeight: "normal",
          lineHeight: 1.4
        }}>
          {hs6Code && (
            <div>
              <strong>HS6 {formatHs6Dot(hs6Code)}</strong>
              {hs6Name && ` — ${hs6Name}`}
              {/* Save button */}
              {(canSave || isCodeSaved) && (
                <div style={{ marginTop: 8 }}>
                  <button
                    onClick={handleSaveCode}
                    disabled={!canSave}
                    style={{
                      padding: "4px 12px",
                      fontSize: 12,
                      border: "1px solid #008C00",
                      borderRadius: 4,
                      backgroundColor: canSave ? "#008C00" : "#f8f9fa",
                      color: canSave ? "#fff" : "#666",
                      cursor: canSave ? "pointer" : "not-allowed",
                      fontFamily: "inherit"
                    }}
                  >
                    {isCodeSaved ? "✓ Uloženo" : "Uložit produkt do vybraných kódů"}
                  </button>
                </div>
              )}
            </div>
          )}
          {countryName && (
            <div style={{ marginTop: 4 }}>
              <strong>{countryName}</strong>
            </div>
          )}
        </div>
      )}
      
      {/* Grid of mini-tiles; hero tiles span two columns */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr 1fr",
        gap: 8
      }}>
        {metrics.map((metric, index) => (
          <div key={index} style={{
            padding: "8px",
            backgroundColor: "#f8f9fa",
            borderRadius: 4,
            textAlign: "center",
            minHeight: 60,
            ...(metric.hero ? { gridColumn: "span 2", border: "1px solid #e9ecef" } : {})
          }}>
            <div style={{
              fontSize: 11,
              color: "#666",
              marginBottom: 4,
              lineHeight: 1.2
            }}>
              {metric.label}
            </div>
            <div style={{
              fontSize: metric.hero ? 17 : 14,
              fontWeight: "bold",
              color: "#008C00",
              lineHeight: 1.2
            }}>
              {metric.value}
            </div>
            {metric.sub && (
              <div style={{ marginTop: 3, lineHeight: 1.2, fontSize: 11, color: "#666", ...(metric.subStyle || {}) }}>
                {metric.sub}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Key Data Overlay */}
      <KeyDataOverlay
        isOpen={showKeyDataOverlay}
        onClose={() => setShowKeyDataOverlay(false)}
      />
    </div>
  );
}