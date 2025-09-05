const BASE =
  (typeof import.meta !== "undefined" && import.meta.env && import.meta.env.VITE_API_BASE && import.meta.env.VITE_API_BASE.trim()) ||
  (typeof process !== "undefined" && process.env && process.env.NEXT_PUBLIC_API_BASE && process.env.NEXT_PUBLIC_API_BASE.trim()) ||
  "http://127.0.0.1:8000";

function qs(p = {}) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(p)) {
    if (v !== undefined && v !== null) q.set(k, String(v));
  }
  return q.toString();
}

async function get(path, p) {
  const url = p ? `${BASE}${path}?${qs(p)}` : `${BASE}${path}`;
  const res = await fetch(url, { credentials: "omit" });
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json();
}

// Real endpoints returning real shapes
export const fetchControls = () => get("/controls");
export const fetchMap      = (p = {}) => get("/map_v2", p);        // [{ iso3,name,value,value_fmt,unit }] - Consolidated to map_v2
export const fetchProducts = (p = {}) => get("/products", p);      // [{ id,name,value,value_fmt,unit }] - Top HS6 products (legacy compatibility)
export const fetchTrend    = (p = {}) => { if (!p.hs6) throw new Error("fetchTrend requires { hs6 }"); return get("/trend", p); };
// Unified bars endpoint: products, partners, or peer comparisons
export const fetchBars     = (p = {}) => get("/bars", p);          // [{ id,name,value,value_fmt,unit }] - Unified bar data
export const fetchBarsV2   = (p = {}) => get("/bars_v2", p);       // Legacy endpoint - redirects to unified service
export const fetchSignals  = (p = {}) => get("/signals", p);       // enriched list
export const fetchTopSignals = (p = {}) => get("/top_signals", p);   // legacy endpoint for country signals

export async function fetchInsights(country, hs6, year) {
  return get("/insights", { importer: country, hs6, year });
}