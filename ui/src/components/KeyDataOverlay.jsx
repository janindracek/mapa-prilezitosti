import React, { useEffect } from 'react';

// Detailed explanations for each key data tile in Czech
const KEY_DATA_EXPLANATIONS = {
  'bilateral_export': {
    title: 'Export ČR → země',
    description: 'Hodnota bilaterálního exportu z České republiky do vybrané země pro konkrétní HS6 produkt.',
    formula: 'Bilateral_Export = Σ(Export_value_USD) pro dané HS6 + země + rok',
    calculation: 'Sečte se celková hodnota exportu daného produktu (HS6 kód) z ČR do cílové země v USD. Data pocházejí z BACI databáze bilaterálního obchodu.',
    interpretation: 'Ukazuje přímou obchodní vazbu - kolik ČR reálně exportuje daného produktu do konkrétní země. Vyšší hodnoty indikují silnější obchodní vztah.'
  },
  'total_cz_export': {
    title: 'Celkový export ČR',
    description: 'Celková hodnota exportu daného HS6 produktu z České republiky do všech zemí světa.',
    formula: 'Total_CZ_Export = Σ(Export_value_USD) pro dané HS6 + všechny země + rok',
    calculation: 'Agreguje export daného produktu ze všech českých exportních destinací. Poskytuje kontext pro relativní důležitost konkrétní země.',
    interpretation: 'Umožňuje porovnat bilaterální export s celkovým - pokud je bilaterální export malá část celkového, země má malý význam pro tento produkt.'
  },
  'country_total_import': {
    title: 'Import země celkem',
    description: 'Celková hodnota importu daného HS6 produktu do vybrané země ze všech zdrojů světa.',
    formula: 'Country_Total_Import = Σ(Import_value_USD) pro dané HS6 + země + všichni exportéři + rok',
    calculation: 'Sečte import daného produktu do cílové země od všech světových dodavatelů. Ukazuje celkovou velikost trhu pro daný produkt.',
    interpretation: 'Větší trh = větší příležitost. Velký import země signalizuje silnou poptávku po daném produktu.'
  },
  'cz_market_share': {
    title: 'Podíl ČR v importu',
    description: 'Procentuální podíl České republiky na celkovém importu daného produktu do vybrané země.',
    formula: 'CZ_Market_Share = (Bilateral_Export / Country_Total_Import) × 100',
    calculation: 'Vydělí se bilaterální export ČR celkovým importem země a vynásobí 100 pro získání procent. Klíčová metrika konkurenceschopnosti.',
    interpretation: 'Vyšší podíl = silnější pozice na trhu. Nízký podíl při velkém trhu = příležitost pro růst.'
  },
  'peer_median': {
    title: 'Medián peer group',
    description: 'Mediánový tržní podíl srovnatelných zemí (peer countries) na importu vybrané země pro daný produkt.',
    formula: 'Peer_Median = median(Market_Share_peer_i) pro všechny peer země i',
    calculation: 'Vypočítá se tržní podíl každé peer země na importu cílové země, hodnoty se seřadí a vezme se medián (prostřední hodnota).',
    interpretation: 'Benchmark pro porovnání - pokud je ČR pod mediánem, má potenciál k růstu. Nad mediánem = nadprůměrný výkon.'
  },
  'yoy_change': {
    title: 'Meziroční změna',
    description: 'Procentuální změna bilaterálního exportu mezi aktuálním a předchozím rokem.',
    formula: 'YoY_Change = ((Export_current_year - Export_previous_year) / Export_previous_year) × 100',
    calculation: 'Odečte se loňský export od letošního, vydělí loňským exportem a vynásobí 100. Pozitivní = růst, negativní = pokles.',
    interpretation: 'Ukazuje dynamiku obchodního vztahu. Vysoký růst = rostoucí příležitost, pokles = možné problémy nebo změny trhu.'
  }
};

export default function KeyDataOverlay({ 
  isOpen = false, 
  onClose = null 
}) {
  // Handle Escape key to close overlay
  useEffect(() => {
    if (!isOpen) return;
    
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && onClose) {
        onClose();
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) {
    return null;
  }

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: 20
      }}
      onClick={onClose}
    >
      <div 
        style={{
          backgroundColor: '#fff',
          borderRadius: 8,
          padding: 24,
          maxWidth: 700,
          maxHeight: '85vh',
          overflow: 'auto',
          position: 'relative',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: 12,
            right: 12,
            background: 'none',
            border: 'none',
            fontSize: 20,
            cursor: 'pointer',
            color: '#666',
            width: 30,
            height: 30,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 4
          }}
          onMouseOver={(e) => e.target.style.backgroundColor = '#f0f0f0'}
          onMouseOut={(e) => e.target.style.backgroundColor = 'transparent'}
        >
          ×
        </button>

        {/* Header */}
        <h2 style={{
          fontFamily: 'Montserrat',
          fontWeight: 'bold',
          marginBottom: 20,
          fontSize: 20,
          color: '#008C00',
          paddingRight: 40
        }}>
          Vysvětlení klíčových dat
        </h2>

        {/* Explanations for each metric */}
        <div style={{ display: 'grid', gap: 20 }}>
          {Object.values(KEY_DATA_EXPLANATIONS).map((metric, index) => (
            <div key={index} style={{ 
              padding: 16,
              backgroundColor: '#f8f9fa',
              borderRadius: 6,
              border: '1px solid #e9ecef'
            }}>
              {/* Title */}
              <h3 style={{
                fontWeight: 'bold',
                marginBottom: 8,
                fontSize: 16,
                color: '#008C00',
                margin: 0
              }}>
                {metric.title}
              </h3>

              {/* Description */}
              <p style={{
                fontSize: 14,
                lineHeight: 1.4,
                color: '#333',
                margin: 0,
                marginBottom: 10
              }}>
                {metric.description}
              </p>

              {/* Formula */}
              <div style={{ marginBottom: 10 }}>
                <strong style={{ fontSize: 13, color: '#555' }}>Vzorec:</strong>
                <div style={{
                  fontSize: 13,
                  fontFamily: 'monospace',
                  backgroundColor: '#fff',
                  border: '1px solid #ddd',
                  padding: 6,
                  borderRadius: 3,
                  marginTop: 4
                }}>
                  {metric.formula}
                </div>
              </div>

              {/* Calculation */}
              <div style={{ marginBottom: 10 }}>
                <strong style={{ fontSize: 13, color: '#555' }}>Výpočet:</strong>
                <p style={{
                  fontSize: 13,
                  lineHeight: 1.4,
                  color: '#555',
                  margin: 0,
                  marginTop: 4
                }}>
                  {metric.calculation}
                </p>
              </div>

              {/* Interpretation */}
              <div>
                <strong style={{ fontSize: 13, color: '#555' }}>Interpretace:</strong>
                <p style={{
                  fontSize: 13,
                  lineHeight: 1.4,
                  color: '#555',
                  margin: 0,
                  marginTop: 4
                }}>
                  {metric.interpretation}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Footer note */}
        <div style={{
          marginTop: 20,
          padding: 12,
          backgroundColor: '#f0f7ff',
          borderRadius: 4,
          border: '1px solid #d6e7ff'
        }}>
          <p style={{
            fontSize: 12,
            color: '#555',
            margin: 0,
            lineHeight: 1.4
          }}>
            <strong>Poznámka:</strong> Všechna data pocházejí z BACI databáze bilaterálního obchodu. 
            Hodnoty jsou uvedeny v USD a přepočítány z původních kUSD pomocí faktoru 1000.
          </p>
        </div>
      </div>
    </div>
  );
}