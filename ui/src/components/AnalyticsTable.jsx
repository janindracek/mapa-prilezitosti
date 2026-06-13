import React, { useEffect, useState } from "react";
import { API_BASE } from "../lib/constants.js";
import HelpButton from "./HelpButton.jsx";
import { SIGNAL_TYPE_ORDER, signalBadge } from "../lib/labels.js";

const PAGE_SIZE = 50;
const METHODS = [
  { v: "", label: "Všechny metody" },
  { v: "trade_structure", label: "Strukturální" },
  { v: "human", label: "Geografická" },
  { v: "yoy_export", label: "YoY export" },
  { v: "yoy_share", label: "YoY podíl" },
];

function fmtNum(x, share = false) {
  if (x == null || Number.isNaN(x)) return "—";
  if (share) return `${(x * 100).toFixed(2)} %`;
  const a = Math.abs(x);
  if (a >= 1e9) return `${(x / 1e9).toFixed(1)} mld`;
  if (a >= 1e6) return `${(x / 1e6).toFixed(1)} mil`;
  return Number(x).toLocaleString("cs-CZ", { maximumFractionDigits: 2 });
}

export default function AnalyticsTable({ referenceData = { countryNames: {}, hs6Labels: {} } }) {
  const [filters, setFilters] = useState({ type: "", method: "", band: "", country: "", hs6: "" });
  const [minValue, setMinValue] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ total: 0, rows: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const set = (k, v) => { setFilters((f) => ({ ...f, [k]: v })); setPage(1); };

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true); setError(null);
      try {
        const base = API_BASE || "";  // prod: same-origin (API_BASE='' from constants.js)
        const qs = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) });
        for (const [k, v] of Object.entries(filters)) if (v) qs.set(k, v);
        const r = await fetch(`${base}/signals/all?${qs.toString()}`);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const j = await r.json();
        if (!cancelled) setData(j);
      } catch (e) {
        if (!cancelled) setError(e.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [filters, page]);

  const total = data.total || 0;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const start = total ? (page - 1) * PAGE_SIZE + 1 : 0;
  const end = Math.min(page * PAGE_SIZE, total);
  const cn = (iso) => referenceData.countryNames?.[iso] || iso;
  const pn = (hs6) => referenceData.hs6Labels?.[String(hs6)] || `HS6 ${hs6}`;

  const selStyle = { padding: "4px 6px", fontSize: 13, borderRadius: 4, border: "1px solid #ccc" };
  const th = { textAlign: "left", padding: "6px 8px", borderBottom: "2px solid #e9ecef", fontSize: 12, color: "#555", whiteSpace: "nowrap" };
  const td = { padding: "5px 8px", borderBottom: "1px solid #f0f0f0", fontSize: 13, whiteSpace: "nowrap" };

  return (
    <div style={{ border: "1px solid #eee", borderRadius: 6, padding: 16, background: "#fff" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
        <h2 style={{ fontFamily: "Montserrat", fontWeight: "bold", fontSize: 20, color: "#008C00", margin: 0 }}>
          Analytika signálů
        </h2>
        <HelpButton
          title="Analytická tabulka"
          text="Filtrovatelný a stránkovaný pohled na ÚPLNOU sadu signálů (~108 tisíc). Na rozdíl od přehledu, který ukazuje ~10 vybraných signálů na zemi, zde vidíte vše — pro analytiky a power-uživatele. Filtrujte podle typu, metody, pásma (silný/slabý), země a produktu (HS6)."
          size={18}
        />
      </div>

      {/* Filters */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
        <select style={selStyle} value={filters.type} onChange={(e) => set("type", e.target.value)}>
          <option value="">Všechny typy</option>
          {SIGNAL_TYPE_ORDER.map((t) => <option key={t} value={t}>{signalBadge(t)}</option>)}
        </select>
        <select style={selStyle} value={filters.method} onChange={(e) => set("method", e.target.value)}>
          {METHODS.map((m) => <option key={m.v} value={m.v}>{m.label}</option>)}
        </select>
        <select style={selStyle} value={filters.band} onChange={(e) => set("band", e.target.value)}>
          <option value="">Silné i slabé</option>
          <option value="strong">Silné</option>
          <option value="weak">Slabé (permisivní)</option>
        </select>
        <input style={{ ...selStyle, width: 90 }} placeholder="Země (ISO3)" value={filters.country}
          onChange={(e) => set("country", e.target.value.toUpperCase())} />
        <input style={{ ...selStyle, width: 110 }} placeholder="HS6" value={filters.hs6}
          onChange={(e) => set("hs6", e.target.value.replace(/\D/g, ""))} />
        <input
          style={{ ...selStyle, width: 150 }}
          type="number"
          min="0"
          placeholder="Min. hodnota (USD)"
          title="Skryje řádky signálů typu Nárůst exportu, jejichž exportní hodnota je pod limitem. Filtr velkých procent z malých základů; uplatňuje se na načtenou stránku."
          value={minValue}
          onChange={(e) => setMinValue(e.target.value)}
        />
      </div>

      <div style={{ fontSize: 13, color: "#666", marginBottom: 6 }}>
        {loading ? "Načítání…" : error ? <span style={{ color: "#d32f2f" }}>Chyba: {error}</span> :
          `${start}–${end} z ${total.toLocaleString("cs-CZ")} signálů`}
      </div>

      <div style={{ overflowX: "auto" }}>
        <table style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr>
              <th style={th}>Typ</th><th style={th}>Pásmo</th><th style={th}>Trh</th>
              <th style={th}>Produkt (HS6)</th><th style={th}>Síla</th>
              <th style={th}>Podíl ČR</th><th style={th}>Medián peers</th><th style={th}>Odstup</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.filter((r) => {
              // Min-USD filter: only meaningful for YoY export rows, whose
              // `value` IS the export amount in USD (share-type rows keep showing).
              const min = Number(minValue);
              if (!minValue || !Number.isFinite(min)) return true;
              if (r.type !== "YoY_export_change") return true;
              return Number(r.value) >= min;
            }).map((r, i) => (
              <tr key={i}>
                <td style={td}>{signalBadge(r.type)}</td>
                <td style={{ ...td, color: r.band === "weak" ? "#8a6d00" : "#2e7d32" }}>
                  {r.band === "weak" ? "slabý" : "silný"}
                </td>
                <td style={td}>{cn(r.partner_iso3)}</td>
                <td style={{ ...td, maxWidth: 280, overflow: "hidden", textOverflow: "ellipsis" }} title={pn(r.hs6)}>
                  {r.hs6} · {pn(r.hs6)}
                </td>
                <td style={td}>{fmtNum(r.intensity)}</td>
                <td style={td}>{r.value != null && r.peer_median != null ? fmtNum(r.value, true) : "—"}</td>
                <td style={td}>{r.peer_median != null ? fmtNum(r.peer_median, true) : "—"}</td>
                <td style={td}>{r.delta_vs_peer != null ? fmtNum(r.delta_vs_peer, true) : "—"}</td>
              </tr>
            ))}
            {!loading && data.rows.length === 0 && (
              <tr><td style={{ ...td, color: "#777" }} colSpan={8}>Žádné signály pro tento filtr.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 12 }}>
        <button disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}
          style={{ padding: "4px 10px", cursor: page <= 1 ? "default" : "pointer" }}>‹ Předchozí</button>
        <span style={{ fontSize: 13, color: "#555" }}>Strana {page} / {pages}</span>
        <button disabled={page >= pages} onClick={() => setPage((p) => Math.min(pages, p + 1))}
          style={{ padding: "4px 10px", cursor: page >= pages ? "default" : "pointer" }}>Další ›</button>
      </div>
    </div>
  );
}
