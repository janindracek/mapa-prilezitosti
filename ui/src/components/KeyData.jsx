import React, { useState } from "react";
import KeyDataOverlay from './KeyDataOverlay.jsx';

// Czech number formatting function
function formatCzechUSD(x) {
  if (x == null || Number.isNaN(x)) return "—";
  try {
    // API returns values already properly scaled 
    const actualValue = x;
    const millions = actualValue / 1e6;
    if (millions >= 1000) {
      const billions = millions / 1000;
      const formatted = billions.toLocaleString("cs-CZ", { 
        minimumFractionDigits: 1, 
        maximumFractionDigits: 1 
      });
      return `${formatted} mld. USD`;
    } else if (millions >= 1) {
      const formatted = millions.toLocaleString("cs-CZ", { 
        minimumFractionDigits: 1, 
        maximumFractionDigits: 1 
      });
      return `${formatted} mil. USD`;
    } else if (millions >= 0.01) {
      const formatted = millions.toLocaleString("cs-CZ", { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
      });
      return `${formatted} mil. USD`;
    } else {
      const thousands = x / 1000;
      const formatted = thousands.toLocaleString("cs-CZ", { 
        minimumFractionDigits: 0, 
        maximumFractionDigits: 0 
      });
      return `${formatted} tis. USD`;
    }
  } catch {
    return String(x) + " USD";
  }
}

function formatPercentage(value) {
  if (value == null || Number.isNaN(value)) return "—";
  return `${(value * 100).toLocaleString("cs-CZ", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;
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
    cz_world_total = null, // Total CZ export for this HS6
    c_import_total = null, // Country's total imports for this HS6
    cz_share_in_c = null,  // CZ's share of country's imports
    median_peer_share = null, // Median peer share for comparison
    cz_delta_pct = null    // YoY change percentage
  } = data;

  // Prepare metrics in logical order for 3x2 grid
  const metrics = [
    {
      label: "Export ČR → země",
      value: formatCzechUSD(cz_to_c),
      shortLabel: "Bilateral export"
    },
    {
      label: "Celkový export ČR",
      value: formatCzechUSD(cz_world_total),
      shortLabel: "Total CZ export"
    },
    {
      label: "Import země celkem",
      value: formatCzechUSD(c_import_total),
      shortLabel: "Country imports"
    },
    {
      label: "Podíl ČR v importu",
      value: formatPercentage(cz_share_in_c),
      shortLabel: "CZ market share"
    },
    // Add median peer share if available
    ...(median_peer_share > 0 ? [{
      label: "Medián peer group",
      value: formatPercentage(median_peer_share),
      shortLabel: "Peer median"
    }] : [{
      label: "Medián peer group",
      value: "—",
      shortLabel: "Peer median"
    }]),
    // Add YoY change if available
    ...(cz_delta_pct !== 0 ? [{
      label: "Meziroční změna",
      value: `${cz_delta_pct > 0 ? '+' : ''}${cz_delta_pct.toLocaleString("cs-CZ", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`,
      shortLabel: "YoY change"
    }] : [{
      label: "Meziroční změna", 
      value: "—",
      shortLabel: "YoY change"
    }])
  ];

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
      
      {/* 3x2 grid of mini-tiles */}
      <div style={{ 
        display: "grid", 
        gridTemplateColumns: "1fr 1fr 1fr",
        gap: 8
      }}>
        {metrics.slice(0, 6).map((metric, index) => (
          <div key={index} style={{ 
            padding: "8px", 
            backgroundColor: "#f8f9fa", 
            borderRadius: 4,
            textAlign: "center",
            minHeight: 60
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
              fontSize: 14, 
              fontWeight: "bold", 
              color: "#008C00",
              lineHeight: 1.2
            }}>
              {metric.value}
            </div>
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