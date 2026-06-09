import React from "react";
import HelpButton from "./HelpButton.jsx";
import {
  SIGNAL_TYPE_ORDER, signalBadge, signalSection, REGISTRY, methodologyForSignal,
} from "../lib/labels.js";

const ICON = {
  Peer_gap_matching: "🧩",
  Peer_gap_human: "🧑‍🏫",
  YoY_export_change: "📈",
  YoY_partner_share_change: "🔁",
};
const PEER_BG = { bg: "#fff4e5", border: "#ffe3bf", text: "#9a5b00" };
const COLORS = {
  Peer_gap_matching: PEER_BG,
  Peer_gap_human: PEER_BG,
  YoY_export_change: { bg: "#eef6ff", border: "#d3e7ff", text: "#0b61d7" },
  YoY_partner_share_change: { bg: "#f3eefe", border: "#e1d6fb", text: "#6b2bd9" },
};

function formatHs6(code) {
  const s = String(code || "").replace(/\D/g, "");
  return s.length === 6 ? `${s.slice(0, 4)}.${s.slice(4)}` : s || "";
}

function productText(s, hs6Map) {
  const hs6 = String(s?.hs6 || "").replace(/\D/g, "");
  if (hs6 && hs6Map && hs6Map[hs6]) return hs6Map[hs6];
  if (s?.hs6_name) return s.hs6_name;
  return hs6 ? `HS6 ${formatHs6(hs6)}` : (s?.label || "");
}

function signalTypeOf(s) {
  return s?.type || "";
}

function Row({ s, hs6Map, selected, onSelect }) {
  const type = signalTypeOf(s);
  const colors = COLORS[type] || COLORS.YoY_export_change;
  const text = productText(s, hs6Map);
  return (
    <li
      onClick={() => onSelect && onSelect(s)}
      title={`${signalBadge(type)} · ${text}`}
      style={{
        display: "grid", gridTemplateColumns: "auto 1fr", alignItems: "center", gap: 8,
        padding: "6px 8px", borderBottom: "1px solid #eee",
        cursor: onSelect ? "pointer" : "default",
        background: selected ? "#f0f7ff" : "transparent",
        borderLeft: selected ? "3px solid #1677ff" : "3px solid transparent",
      }}
    >
      <span style={{
        background: colors.bg, border: `1px solid ${colors.border}`, color: colors.text,
        padding: "2px 6px", borderRadius: 10, fontSize: 12, whiteSpace: "nowrap",
      }}>
        {signalBadge(type)}
      </span>
      <span style={{ display: "flex", alignItems: "center", gap: 6, overflow: "hidden" }}>
        <span aria-hidden>{ICON[type] || "🔎"}</span>
        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{text}</span>
      </span>
    </li>
  );
}

export default function SignalsList({
  signals = [],
  selectedId,
  onSelect,
  referenceData = { countryNames: {}, hs6Labels: {}, continents: {}, loading: false },
}) {
  const hs6Map = referenceData.hs6Labels;
  const items = (Array.isArray(signals) ? signals : []).filter((s) => SIGNAL_TYPE_ORDER.includes(signalTypeOf(s)));

  // Two-tier split (M5): strong shown grouped by type; weak shown as one flagged
  // "permissive" group (the band comes from the serving layer / API selection).
  const isWeak = (s) => String(s?.band || "strong") === "weak";
  const strong = items.filter((s) => !isWeak(s));
  const weak = items.filter(isWeak);

  const byType = Object.fromEntries(SIGNAL_TYPE_ORDER.map((t) => [t, []]));
  for (const s of strong) byType[signalTypeOf(s)].push(s);
  for (const t of SIGNAL_TYPE_ORDER) {
    byType[t].sort((a, b) => (b?.score ?? b?.intensity ?? 0) - (a?.score ?? a?.intensity ?? 0));
  }

  const sectionHelp = (t) => {
    const method = methodologyForSignal(t);
    return (
      <HelpButton
        id={t}
        title={signalSection(t)}
        text={REGISTRY[t]?.tooltip || ""}
        extra={method ? (
          <p style={{ margin: "8px 0 0", color: "#555" }}>
            <strong>Srovnávací skupina (peers):</strong> {method}
          </p>
        ) : (
          <p style={{ margin: "8px 0 0", fontStyle: "italic", color: "#777" }}>
            Tento signál nepoužívá srovnávací skupinu (jen meziroční změna).
          </p>
        )}
        size={16}
      />
    );
  };

  const empty = strong.length === 0 && weak.length === 0;

  return (
    <div style={{ border: "1px solid #eee", borderRadius: 6, padding: 12, background: "#fff" }}>
      <h2 style={{ fontFamily: "Montserrat", fontWeight: "bold", marginBottom: 6, fontSize: 18, color: "#008C00" }}>
        Signály
      </h2>

      {SIGNAL_TYPE_ORDER.map((t) =>
        byType[t].length ? (
          <div key={`sec-${t}`} style={{ marginBottom: 14 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, margin: "6px 0 4px 6px" }}>
              <span style={{ fontWeight: 600, color: "#333" }}>{signalSection(t)}</span>
              {sectionHelp(t)}
            </div>
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {byType[t].map((s) => (
                <Row key={s?.id ?? s?.label ?? Math.random().toString(36).slice(2)}
                  s={s} hs6Map={hs6Map} selected={s?.id === selectedId} onSelect={onSelect} />
              ))}
            </ul>
          </div>
        ) : null
      )}

      {weak.length > 0 && (
        <div style={{ marginTop: 8, paddingTop: 8, borderTop: "1px dashed #ddd", opacity: 0.92 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, margin: "2px 0 4px 6px" }}>
            <span style={{ fontWeight: 600, color: "#8a6d00" }}>Slabší signály (permisivní)</span>
            <HelpButton
              title="Slabší (permisivní) signály"
              text="Když má země méně než 5 silných signálů, doplníme seznam slabšími signály (menší odstup od mediánu peers, 10–20 %). Jsou méně naléhavé, ale u tenkých trhů (např. cíl obchodní mise) stále užitečné."
              size={16}
            />
          </div>
          <div style={{ fontSize: 12, color: "#8a6d00", margin: "0 0 4px 6px" }}>
            Méně naléhavé; doplněno, protože silných signálů je málo.
          </div>
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {weak.map((s) => (
              <Row key={s?.id ?? s?.label ?? Math.random().toString(36).slice(2)}
                s={s} hs6Map={hs6Map} selected={s?.id === selectedId} onSelect={onSelect} />
            ))}
          </ul>
        </div>
      )}

      {empty && <div style={{ padding: "6px 8px", color: "#666" }}>Žádné signály</div>}
    </div>
  );
}
