import React from "react";

// --- Minimal helpers (no numbers, no debug) ---
function getSignalMeta(label = "") {
  const raw = String(label || "");
  const [typeRaw, ...restParts] = raw.split(":");
  const type = (typeRaw || "").trim();
  const rest = restParts.join(":").trim();

  let icon = "🔎";
  let badge = "Signál";
  let colors = { bg: "#eef6ff", border: "#d3e7ff", text: "#0b61d7" };
  let title = "Signál";

  if (type === "YoY_export_change") {
    icon = "📈"; badge = "Export roste"; title = "Nárůst exportu (YoY)";

  } else if (type === "YoY_partner_share_change") {
    icon = "🔁"; badge = "Podíl roste"; title = "Roste podíl partnera (YoY)";
    colors = { bg: "#f3eefe", border: "#e1d6fb", text: "#6b2bd9" };

  } else if (type === "Peer_gap_opportunity") {
    icon = "🧭"; badge = "Benchmark (příležitostní)"; title = "Pod mediánem peers (opportunity)";
    colors = { bg: "#fff4e5", border: "#ffe3bf", text: "#9a5b00" };

  } else if (type === "Peer_gap_matching") {
    icon = "🧩"; badge = "Benchmark (strukturální)"; title = "Pod mediánem peers (matching)";
    colors = { bg: "#fff4e5", border: "#ffe3bf", text: "#9a5b00" };

  } else if (type === "Peer_gap_human") {
    icon = "🧑‍🏫"; badge = "Benchmark (geografický)"; title = "Pod mediánem peers (human)";
    colors = { bg: "#fff4e5", border: "#ffe3bf", text: "#9a5b00" };

  } else if (type === "YoY_import_change") {
    icon = "📈"; badge = "Import roste"; title = "Nárůst importu (YoY)";

  } else if (type === "Peer_gap_below_median" || type === "Peer_gap_below_mediana") {
    icon = "⚠️"; badge = "Pod peers"; title = "Pod mediánem peers";
    colors = { bg: "#fff4e5", border: "#ffe3bf", text: "#9a5b00" };
  }

  const cleaned = rest.replace(/\s*->\s*/g, " → ").replace(/\s/g, " ").trim();
  return { icon, badge, colors, title, type, text: cleaned || raw };
}

function formatHs6(code) {
  const s = String(code || "").replace(/\D/g, "");
  return s.length === 6 ? `${s.slice(0, 4)}.${s.slice(4)}` : null;
}

function parseHs6AndPartner(cleaned = "") {
  const m = cleaned.match(/\b(\d{6})\b\s*(?:→|->)\s*(.)$/);
  if (m) return { hs6: m[1], partner: m[2].trim() };
  const code = (cleaned.match(/\b(\d{6})\b/) || [])[1];
  const parts = cleaned.split(/(?:→|->)/);
  const partner = parts.length > 1 ? parts[parts.length - 1].trim() : "";
  return { hs6: code || "", partner };
}

function chooseZorZe(partnerName = "") {
  const first = (partnerName.trim()[0] || "").toLowerCase();
  return ["s", "z", "š", "ž", "ř"].includes(first) ? "ze" : "z";
}


function sentence(type, cleanedText, hs6Map) {
  const { hs6 } = parseHs6AndPartner(cleanedText);
  const pretty = formatHs6(hs6) || hs6;
  const name = hs6 && hs6Map && hs6Map[hs6] ? hs6Map[hs6] : (pretty ? `HS6 ${pretty}` : "");

  // Return just the product name without arrow and country
  if (name) {
    return name;
  }
  return cleanedText;
}

export default function SignalsList({ 
  signals = [], 
  selectedId, 
  onSelect,
  referenceData = { countryNames: {}, hs6Labels: {}, continents: {}, loading: false }
}) {
  // Use centralized reference data instead of loading independently
  const hs6Map = referenceData.hs6Labels;

  const items = Array.isArray(signals) ? signals : [];

  // --- group by the 5 canonical types; keep top 3 per type ---
  const TYPE_ORDER = [
    "Peer_gap_opportunity",
    "Peer_gap_matching", 
    "Peer_gap_human",
    "YoY_export_change",
    "YoY_partner_share_change",
  ];
  const sectionTitle = (t) =>
    t === "YoY_export_change" ? "Nárůst exportu" :
    t === "YoY_partner_share_change" ? "Navýšení podílu na importu" :
    t === "Peer_gap_opportunity" ? "Benchmark (statistický, pohled vpřed)" :
    t === "Peer_gap_matching" ? "Benchmark (statistický, pohled současný)" :
    t === "Peer_gap_human" ? "Benchmark (geografický)" : "Jiné";

  const byType = Object.fromEntries(TYPE_ORDER.map(t => [t, []]));
  for (const s of items) {
    const typeFromData = s?.type || getSignalMeta(s?.label || "").type || "Other";
    if (!TYPE_ORDER.includes(typeFromData)) continue;
    byType[typeFromData].push(s);
  }
  for (const t of TYPE_ORDER) {
    const arr = byType[t];
    arr.sort((a, b) => (b?.score ?? b?.intensity ?? 0) - (a?.score ?? a?.intensity ?? 0));
    byType[t] = arr.slice(0, 3);
  }

  return (
    <div style={{ border: "1px solid #eee", borderRadius: 6, padding: 12, background: "#fff" }}>
      <h2 style={{ fontFamily: "Montserrat", fontWeight: "bold", marginBottom: 6, fontSize: 18, color: "#008C00" }}>Signály</h2>
      {TYPE_ORDER.map((t) => (
        <div key={`sec-${t}`} style={{ marginBottom: 14 }}>
          <div style={{ fontWeight: 600, margin: "6px 0 4px 6px", color: "#333" }}>
            {sectionTitle(t)}
          </div>
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {(byType[t] || []).map((s) => {
              const typeFromData = s?.type || t;
              const partnerDisplay = s?.partner_name || s?.partner_iso3 || "";
              const labelStr = s?.label || `${typeFromData}: ${s?.hs6 || ""} -> ${partnerDisplay}`;
              const meta = getSignalMeta(labelStr);
              const text = sentence(typeFromData, meta.text, hs6Map);
              return (
                <li
                  key={s?.id ?? s?.label ?? Math.random().toString(36).slice(2)}
                  onClick={() => onSelect && onSelect(s)}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "auto 1fr",
                    alignItems: "center",
                    gap: 8,
                    padding: "6px 8px",
                    borderBottom: "1px solid #eee",
                    cursor: onSelect ? "pointer" : "default",
                    background: s?.id === selectedId ? "#f0f7ff" : "transparent",
                    borderLeft: s?.id === selectedId ? "3px solid #1677ff" : "3px solid transparent",
                  }}
                  title={`${meta.title} · ${text}`}
                >
                  <span style={{
                    background: meta.colors.bg,
                    border: `1px solid ${meta.colors.border}`,
                    color: meta.colors.text,
                    padding: "2px 6px",
                    borderRadius: 10,
                    fontSize: 12,
                    whiteSpace: "nowrap",
                  }}>
                    {meta.badge}
                  </span>
                  <span style={{ display: "flex", alignItems: "center", gap: 6, overflow: "hidden" }}>
                    <span aria-hidden>{meta.icon}</span>
                    <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {text}
                    </span>
                  </span>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
      {TYPE_ORDER.every((t) => !byType[t] || byType[t].length === 0) && (
        <div style={{ padding: "6px 8px", color: "#666" }}>Žádné signály</div>
      )}
    </div>
  );
}
