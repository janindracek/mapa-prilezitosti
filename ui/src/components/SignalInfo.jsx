import React, { useState, useEffect } from 'react';
import { API_BASE } from '../lib/constants.js';
import HelpButton from './HelpButton.jsx';
import { REGISTRY, SIGNAL_METHOD, methodologyForSignal } from '../lib/labels.js';

export default function SignalInfo({
  signal = null,
  country = null,
  year = 2023,
  referenceData = { countryNames: {}, loading: false },
}) {
  const [peerGroupData, setPeerGroupData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const type = signal?.type;
  const isPeerGroupSignal = !!(type && type.startsWith('Peer_gap'));
  const method = type ? SIGNAL_METHOD[type] : null; // trade_structure | human | undefined

  // Fetch the selected market's peer-group explanation for peer-gap signals.
  useEffect(() => {
    if (!isPeerGroupSignal || !signal || !country || !method) {
      setPeerGroupData(null);
      return;
    }
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const base = API_BASE || 'http://127.0.0.1:8000';
        const url = `${base}/peer_groups/explanation?method=${encodeURIComponent(method)}&country=${encodeURIComponent(country)}&year=${encodeURIComponent(year)}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        const data = await response.json();
        if (!cancelled) setPeerGroupData(data);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [isPeerGroupSignal, type, country, year, method]);

  if (!signal) {
    return (
      <div style={{ border: "1px solid #eee", borderRadius: 6, padding: 12, background: "#fff", color: "#666" }}>
        Vyberte signál pro zobrazení informací
      </div>
    );
  }

  const row = REGISTRY[type] || {};
  const typeDisplay = row.card_title || row.badge || type;
  const explanation = row.tooltip || 'Popis signálu není k dispozici.';
  const methodProse = type ? methodologyForSignal(type) : '';

  return (
    <div style={{ border: "1px solid #eee", borderRadius: 6, padding: 12, background: "#fff" }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <h3 style={{ fontFamily: "Montserrat", fontWeight: "bold", fontSize: 18, color: "#008C00", margin: 0 }}>
          Informace o signálu
        </h3>
        <HelpButton
          id={type}
          title={typeDisplay}
          text={explanation}
          size={20}
          label="Zobrazit metodiku signálu"
          extra={methodProse ? (
            <p style={{ margin: "8px 0 0", color: "#555" }}>
              <strong>Metodika srovnávací skupiny:</strong> {methodProse}
            </p>
          ) : null}
        />
      </div>

      <div style={{ marginBottom: 8 }}>
        <strong style={{ color: "#333" }}>Typ signálu:</strong>
        <div style={{ marginTop: 4, fontSize: 14 }}>{typeDisplay}</div>
      </div>

      <div style={{ marginBottom: 12 }}>
        <strong style={{ color: "#333" }}>Vysvětlení signálu:</strong>
        <div style={{ marginTop: 4, fontSize: 14, lineHeight: 1.4 }}>{explanation}</div>
      </div>

      <div>
        <strong style={{ color: "#333" }}>Porovnávací skupina:</strong>
        {!isPeerGroupSignal ? (
          <div style={{ marginTop: 4, fontSize: 14, fontStyle: 'italic', color: '#666' }}>není relevantní</div>
        ) : (
          <div style={{ marginTop: 4 }}>
            {loading && <div style={{ fontSize: 14, color: '#666' }}>Načítání informací o skupině…</div>}
            {error && <div style={{ fontSize: 14, color: '#d32f2f' }}>Chyba při načítání: {error}</div>}
            {peerGroupData && !loading && (
              <>
                <div style={{ fontSize: 14, marginBottom: 8, lineHeight: 1.4 }}>
                  <strong>{peerGroupData.methodology_name || 'Neznámá metodika'}</strong>
                  {peerGroupData.cluster_name && <span> – {peerGroupData.cluster_name}</span>}
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
                      {peerGroupData.peer_countries.map((iso3) => referenceData.countryNames?.[iso3] || iso3).join(', ')}
                    </div>
                  </div>
                )}
              </>
            )}
            {!peerGroupData && !loading && !error && (
              <div style={{ fontSize: 14, color: '#666', fontStyle: 'italic' }}>Informace o skupině nejsou k dispozici</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
