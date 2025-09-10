import React, { useState, useEffect } from 'react';
import { API_BASE } from '../lib/constants.js';
import MethodologyOverlay from './MethodologyOverlay.jsx';

// Signal type translations to Czech
const SIGNAL_TYPE_TRANSLATIONS = {
  'YoY_export_change': 'Nárůst exportu',
  'YoY_partner_share_change': 'Změna českého podílu na importu', 
  'Peer_gap_below_median': 'Mezera pod peer mediánem',
  'Peer_gap_matching': 'Mezera - strukturálně podobné země',
  'Peer_gap_opportunity': 'Mezera - země s podobnými příležitostmi',
  'Peer_gap_human': 'Mezera - geograficky/politicky podobné země'
};

// Signal explanations in Czech
const SIGNAL_EXPLANATIONS = {
  'YoY_export_change': 'Významná změna hodnoty exportu mezi roky - indikuje rostoucí nebo klesající obchodní vztahy.',
  'YoY_partner_share_change': 'Významná změna podílu Česka na celkovém importu partnera - indikuje rostoucí nebo klesající konkurenceschopnost na daném trhu.',
  'Peer_gap_below_median': 'Český export je pod mediánem srovnatelných zemí - identifikuje potenciální příležitosti.',
  'Peer_gap_matching': 'Český export je pod mediánem zemí s podobnou exportní strukturou - ukazuje nevyužité možnosti.',
  'Peer_gap_opportunity': 'Český export je pod mediánem zemí s podobnými příležitostmi - signalizuje konkurenční nevýhody.',
  'Peer_gap_human': 'Český export je pod mediánem geograficky nebo politicky blízkých zemí - indikuje regionální zaostávání.'
};

export default function SignalInfo({ 
  signal = null, 
  country = null, 
  year = 2023, 
  referenceData = { countryNames: {}, loading: false } 
}) {
  const [peerGroupData, setPeerGroupData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showMethodologyOverlay, setShowMethodologyOverlay] = useState(false);

  // Determine if this signal type uses peer groups
  // Only peer gap signals use peer groups - YoY signals (export/import percentage) do not
  const isPeerGroupSignal = signal?.type && signal.type.startsWith('Peer_gap');
  
  // Map signal type to API method parameter
  const getMethodForSignalType = (signalType) => {
    switch(signalType) {
      case 'Peer_gap_human': return 'human';
      case 'Peer_gap_matching': return 'trade_structure';
      case 'Peer_gap_opportunity': return 'opportunity';
      case 'Peer_gap_below_median': return 'default';
      default: return null;
    }
  };

  // Fetch peer group explanation when signal changes
  useEffect(() => {
    if (!isPeerGroupSignal || !signal || !country) {
      setPeerGroupData(null);
      return;
    }

    const method = getMethodForSignalType(signal.type);
    if (!method) {
      setPeerGroupData(null);
      return;
    }

    const fetchPeerGroupData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const base = API_BASE || 'http://127.0.0.1:8000';
        // Use the SELECTED country for peer group explanations - we want to see which peer group the selected country belongs to
        const url = `${base}/peer_groups/explanation?method=${encodeURIComponent(method)}&country=${encodeURIComponent(country)}&year=${encodeURIComponent(year)}`;
        
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        setPeerGroupData(data);
        
      } catch (err) {
        console.error('[SignalInfo] Failed to fetch peer group data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPeerGroupData();
  }, [isPeerGroupSignal, signal?.type, country, year]);

  if (!signal) {
    return (
      <div style={{ 
        border: "1px solid #eee", 
        borderRadius: 6, 
        padding: 12, 
        background: "#fff",
        color: "#666"
      }}>
        Vyberte signál pro zobrazení informací
      </div>
    );
  }

  const signalTypeDisplay = SIGNAL_TYPE_TRANSLATIONS[signal.type] || signal.type;
  const signalExplanation = SIGNAL_EXPLANATIONS[signal.type] || 'Popis signálu není k dispozici.';

  return (
    <div style={{ 
      border: "1px solid #eee", 
      borderRadius: 6, 
      padding: 12, 
      background: "#fff" 
    }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        marginBottom: 12 
      }}>
        <h3 style={{ 
          fontFamily: "Montserrat", 
          fontWeight: "bold", 
          fontSize: 18, 
          color: "#008C00",
          margin: 0,
          marginRight: 8
        }}>
          Informace o signálu
        </h3>
        <button
          onClick={() => setShowMethodologyOverlay(true)}
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
          title="Zobrazit metodiku výpočtu signálu"
          aria-label="Zobrazit metodiku výpočtu signálu"
        >
          ?
        </button>
      </div>
      
      {/* Signal Type */}
      <div style={{ marginBottom: 8 }}>
        <strong style={{ color: "#333" }}>Typ signálu:</strong>
        <div style={{ marginTop: 4, fontSize: 14 }}>{signalTypeDisplay}</div>
      </div>

      {/* Signal Explanation */}
      <div style={{ marginBottom: 12 }}>
        <strong style={{ color: "#333" }}>Vysvětlení signálu:</strong>
        <div style={{ marginTop: 4, fontSize: 14, lineHeight: 1.4 }}>{signalExplanation}</div>
      </div>

      {/* Peer Group Information */}
      <div>
        <strong style={{ color: "#333" }}>Porovnávací skupina:</strong>
        {!isPeerGroupSignal ? (
          <div style={{ marginTop: 4, fontSize: 14, fontStyle: 'italic', color: '#666' }}>
            není relevantní
          </div>
        ) : (
          <div style={{ marginTop: 4 }}>
            {loading && (
              <div style={{ fontSize: 14, color: '#666' }}>Načítání informací o skupině...</div>
            )}
            
            {error && (
              <div style={{ fontSize: 14, color: '#d32f2f' }}>
                Chyba při načítání: {error}
              </div>
            )}
            
            {peerGroupData && !loading && (
              <>
                <div style={{ fontSize: 14, marginBottom: 8, lineHeight: 1.4 }}>
                  <strong>{peerGroupData.methodology_name || 'Neznámá metodika'}</strong>
                  {peerGroupData.cluster_name && (
                    <span> - {peerGroupData.cluster_name}</span>
                  )}
                </div>
                
                {peerGroupData.explanation_text && (
                  <div style={{ fontSize: 13, marginBottom: 8, color: '#555', lineHeight: 1.4 }}>
                    {peerGroupData.explanation_text}
                  </div>
                )}
                
                {peerGroupData.peer_countries && peerGroupData.peer_countries.length > 0 && (
                  <div style={{ fontSize: 13 }}>
                    <strong>Země ve skupině ({peerGroupData.country_count || peerGroupData.peer_countries.length}):</strong>
                    <div style={{ marginTop: 4, lineHeight: 1.4 }}>
                      {peerGroupData.peer_countries
                        .map(iso3 => referenceData.countryNames?.[iso3] || iso3)
                        .join(', ')}
                    </div>
                  </div>
                )}
              </>
            )}
            
            {!peerGroupData && !loading && !error && (
              <div style={{ fontSize: 14, color: '#666', fontStyle: 'italic' }}>
                Informace o skupině nejsou k dispozici
              </div>
            )}
          </div>
        )}
      </div>

      {/* Methodology Overlay */}
      <MethodologyOverlay
        isOpen={showMethodologyOverlay}
        onClose={() => setShowMethodologyOverlay(false)}
        signalType={signal?.type}
      />
    </div>
  );
}