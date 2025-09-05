import React, { useEffect } from 'react';

// Detailed methodology explanations in Czech
const METHODOLOGY_DETAILS = {
  'YoY_export_change': {
    title: 'Meziroční změna exportu',
    peerGroupMethod: 'Nepoužívá peer group - analyzuje pouze bilateral data.',
    calculation: 'Porovnává hodnotu exportu mezi aktuálním a předchozím rokem.',
    formula: 'YoY_Change = ((Export_t - Export_t-1) / Export_t-1) × 100',
    detailedCalculation: 'Pro každý pár země-produkt se vypočítá: 1) Export_t = bilaterální export v aktuálním roce, 2) Export_t-1 = bilaterální export v předchozím roce, 3) Relativní změna jako procento, 4) Filtrování: pouze změny > configurable threshold (např. 50%)',
    ordering: 'Signály jsou seřazeny podle absolutní velikosti změny - největší nárůsty i poklesy mají nejvyšší prioritu.',
    peerGroupGeneration: 'N/A - nepoužívá peer groups'
  },
  'YoY_partner_share_change': {
    title: 'Meziroční změna podílu partnera',
    peerGroupMethod: 'Nepoužívá peer group - analyzuje změny v exportním portfoliu.',
    calculation: 'Měří změnu podílu konkrétní země na celkovém českém exportu produktu.',
    formula: 'Share_Change = (Export_c_t / Total_CZ_Export_t) - (Export_c_t-1 / Total_CZ_Export_t-1)',
    detailedCalculation: 'Pro každý pár země-produkt: 1) Share_t = Export_do_země_c / Celkový_CZ_export_HS6 v roce t, 2) Share_t-1 = totéž pro předchozí rok, 3) Rozdíl v procentních bodech, 4) Filtrování: pouze změny > threshold (např. 2 p.b.)',
    ordering: 'Seřazeno podle absolutní velikosti změny - největší posuny v exportním portfoliu jsou prioritní.',
    peerGroupGeneration: 'N/A - nepoužívá peer groups'
  },
  'Peer_gap_below_median': {
    title: 'Mezera pod peer mediánem - geografické skupiny',
    peerGroupMethod: 'Geograficko-ekonomické peer groups - expertně definované na základě regionální blízkosti a ekonomické podobnosti.',
    calculation: 'Porovnává český tržní podíl s mediánem peer group.',
    formula: 'Gap = Median(Market_Share_peer_i) - Market_Share_CZ',
    detailedCalculation: 'Pro každý pár země-produkt: 1) Market_Share_CZ = Export_CZ_to_country / Total_Import_country, 2) Pro každou peer zemi i: Market_Share_peer_i = Export_peer_i_to_country / Total_Import_country, 3) Median všech peer podílů, 4) Gap = Median - CZ_share, 5) Filtrování: pouze negativní gaps (ČR pod mediánem)',
    ordering: 'Seřazeno podle velikosti gap - největší rozdíl pod mediánem má nejvyšší prioritu.',
    peerGroupGeneration: 'Expertní klasifikace do 23 skupin: EU Core West (DEU, FRA, NLD, BEL), Central Europe (POL, HUN, SVK + ČR), GCC (SAU, ARE, QAT), atd. Založeno na geografii, ekonomické úrovni a obchodních vztazích.'
  },
  'Peer_gap_matching': {
    title: 'Mezera - strukturálně podobné země',
    peerGroupMethod: 'K-means clustering zemí podle podobnosti importních portfolií (HS2 kategorie) s kosinovou vzdáleností.',
    calculation: 'Porovnává český podíl s mediánem strukturálně podobných zemí.',
    formula: 'Gap = Median(Market_Share_peer_i) - Market_Share_CZ',
    detailedCalculation: 'Identické s geografickými groups, ale peer země jsou definované clustering algoritmem: 1) Pro každou zemi: Import_vector = [import_HS2_01, import_HS2_02, ..., import_HS2_99], 2) K-means s kosinovou podobností → clustery, 3) ČR peer group = země ve stejném clusteru, 4) Gap kalkulace identická jako u geografických',
    ordering: 'Seřazeno podle velikosti strukturální mezery - největší nevyužité potenciály mají přednost.',
    peerGroupGeneration: 'K-means clustering (k=10): 1) Import portfolio každé země jako HS2 vektor, 2) Kosinová podobnost mezi vektory, 3) Clustering algoritmus seskupí země s podobnými obchodními strukturami, 4) Výsledek: 10 clusterů zemí s podobnými importními profily'
  },
  'Peer_gap_opportunity': {
    title: 'Mezera - země s podobnými příležitostmi',
    peerGroupMethod: 'K-means clustering založený na exportních příležitostech s kombinovanými metrikami.',
    calculation: 'Porovnává český výkon s mediánem zemí s podobnými exportními příležitostmi.',
    formula: 'Gap = Median(Market_Share_peer_i) - Market_Share_CZ',
    detailedCalculation: 'Gap kalkulace identická, ale peer definice založená na PCA: 1) Pro každou zemi: Opportunity_vector = [40 PCs HS6 shares + 20 PCs HS6 growth + HHI + top_share + partner_diversity], 2) Kombinovaný 63-dimenzionální vektor, 3) K-means clustering (k=10), 4) Standard gap kalkulace pro země ve stejném opportunity clusteru',
    ordering: 'Seřazeno podle opportunity gap - největší zaostávání za podobně vybavenými zeměmi má prioritu.',
    peerGroupGeneration: 'Robustní PCA + clustering: 1) Vstupní data: 5,487 HS6 kódů (96/99 HS2 kategorií) z reálných CZ obchodních dat, 2) PCA dimenzionální redukce: 40 PCs pro HS6 exportní podíly + 20 PCs pro HS6 růstové trendy, 3) Strukturální metriky: HHI koncentrace + podíl top produktů + diverzita partnerů, 4) K-means (k=10) na 63-dimenzionálním prostoru → 10 opportunity clusterů'
  },
  'Peer_gap_human': {
    title: 'Mezera - expertně kurátorované skupiny',
    peerGroupMethod: 'Expertně kurátorované peer groups založené na ekonomické a geografické analýze reálných vztahů.',
    calculation: 'Standardní gap kalkulace proti mediánu expertně definovaných skupin.',
    formula: 'Gap = Median(Market_Share_peer_i) - Market_Share_CZ',
    detailedCalculation: 'Identická gap kalkulace jako u ostatních peer methods: 1) Tržní podíly všech peer zemí v cílové zemi pro daný HS6, 2) Medián peer podílů, 3) Gap = Median - CZ_share, 4) Filtrování negativních gaps. Rozdíl je v definici peer groups - expertní vs. algoritmická.',
    ordering: 'Seřazeno podle gap velikosti v kontextu reálných ekonomických vztahů.',
    peerGroupGeneration: 'Expertní kurátování do 23 skupin založené na: 1) Geografická blízkost, 2) Ekonomická úroveň (GDP per capita), 3) Obchodní vztahy a vazby, 4) Politické a institucionální podobnosti, 5) Historické ekonomické vztahy. Např.: EU Core West, Central Europe V4+, GCC, North America, East Asia Advanced.'
  }
};

export default function MethodologyOverlay({ 
  isOpen = false, 
  onClose = null, 
  signalType = null 
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

  if (!isOpen || !signalType) {
    return null;
  }

  const methodology = METHODOLOGY_DETAILS[signalType];
  if (!methodology) {
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
          maxHeight: '80vh',
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
          Metodika výpočtu: {methodology.title}
        </h2>

        {/* Calculation Method */}
        <div style={{ marginBottom: 20 }}>
          <h3 style={{
            fontWeight: 'bold',
            marginBottom: 8,
            fontSize: 16,
            color: '#333'
          }}>
            Výpočet síly signálu
          </h3>
          <p style={{
            fontSize: 14,
            lineHeight: 1.5,
            color: '#555',
            margin: 0,
            marginBottom: 10
          }}>
            {methodology.calculation}
          </p>
          
          {/* Formula */}
          {methodology.formula && (
            <div style={{ marginBottom: 10 }}>
              <strong style={{ fontSize: 13, color: '#555' }}>Vzorec:</strong>
              <div style={{
                fontSize: 13,
                fontFamily: 'monospace',
                backgroundColor: '#f8f9fa',
                border: '1px solid #ddd',
                padding: 8,
                borderRadius: 4,
                marginTop: 4
              }}>
                {methodology.formula}
              </div>
            </div>
          )}

          {/* Detailed Calculation */}
          {methodology.detailedCalculation && (
            <div>
              <strong style={{ fontSize: 13, color: '#555' }}>Detailní postup:</strong>
              <p style={{
                fontSize: 13,
                lineHeight: 1.4,
                color: '#555',
                margin: 0,
                marginTop: 4
              }}>
                {methodology.detailedCalculation}
              </p>
            </div>
          )}
        </div>

        {/* Ordering Method */}
        <div style={{ marginBottom: 20 }}>
          <h3 style={{
            fontWeight: 'bold',
            marginBottom: 8,
            fontSize: 16,
            color: '#333'
          }}>
            Řazení signálů podle priority
          </h3>
          <p style={{
            fontSize: 14,
            lineHeight: 1.5,
            color: '#555',
            margin: 0
          }}>
            {methodology.ordering}
          </p>
        </div>

        {/* Peer Group Generation */}
        <div style={{ marginBottom: 0 }}>
          <h3 style={{
            fontWeight: 'bold',
            marginBottom: 8,
            fontSize: 16,
            color: '#333'
          }}>
            Generování peer group
          </h3>
          <p style={{
            fontSize: 14,
            lineHeight: 1.5,
            color: '#555',
            margin: 0
          }}>
            {methodology.peerGroupGeneration}
          </p>
        </div>
      </div>
    </div>
  );
}