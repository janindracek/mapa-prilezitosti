// Canonical label access — reads the generated view of data/ref/labels.csv
// (the single source of truth). Replaces hardcoded Czech strings scattered
// across the components, and fixes the section-header-vs-badge vocab clash.
import REGISTRY from "./labels.generated.json";

export { REGISTRY };

// Live (non-retired) signal types, in display order. opportunity is retired (M3).
export const SIGNAL_TYPE_ORDER = [
  "Peer_gap_matching",
  "Peer_gap_human",
  "YoY_export_change",
  "YoY_partner_share_change",
].filter((id) => REGISTRY[id] && REGISTRY[id].status !== "retired");

// signal_type id -> peer methodology id (for descriptor popups). null = no method.
export const SIGNAL_METHOD = {
  Peer_gap_matching: "trade_structure",
  Peer_gap_human: "human",
};

export function isRetired(id) {
  return REGISTRY[id]?.status === "retired";
}

// One canonical string per (concept, surface). Falls back across surfaces, then id.
export function label(id, surface = "badge") {
  const row = REGISTRY[id];
  if (!row) return id;
  return row[surface] || row.short_label || row.badge || row.card_title || id;
}

// Convenience wrappers
export const signalBadge = (id) => label(id, "badge");
export const signalSection = (id) => label(id, "section_header");
export const signalShort = (id) => label(id, "short_label");

// Text shown in a "?" help popup for any concept: prefer full prose, else tooltip.
export function helpText(id) {
  const row = REGISTRY[id];
  if (!row) return "";
  return row.full_description && row.full_description !== "TBD"
    ? row.full_description
    : row.tooltip || "";
}

// Title for the help popup
export function helpTitle(id) {
  const row = REGISTRY[id];
  if (!row) return id;
  return row.card_title || row.section_header || row.badge || row.short_label || id;
}

// The methodology descriptor (Czech prose) for a peer-gap signal type, if any.
export function methodologyForSignal(signalType) {
  const m = SIGNAL_METHOD[signalType];
  return m ? helpText(m) : "";
}
