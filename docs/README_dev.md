


⸻

Trade Engine — Dev Quickstart

0) Prereqs
	•	Python venv activated, deps installed
	•	Data ETL already produced parquet files in data/out/…

## USD Units Pipeline

⚠️ **CRITICAL**: Only `etl/01_build_base_facts.py` handles unit conversion.

| Stage | Input Units | Output Units | Notes |
|-------|------------|--------------|--------|
| BACI Raw Data | kUSD | kUSD | `value_usd=402` = 402,000 USD |
| ETL Stage 1 | kUSD | USD | `TRADE_UNITS_SCALE=1000` conversion |
| ETL Stages 2-8 | USD | USD | Pass-through only |
| API/UI | USD | USD | Formatted display only |

**Expected**: Czech exports ~250B USD after proper scaling.

1) Refresh data (optional, clean slate)

# Core ETL pipeline (if rebuilding from scratch)
export TRADE_UNITS_SCALE=1000  # CRITICAL: Converts BACI kUSD→USD in Stage 1 only
python etl/01_build_base_facts.py          # kUSD→USD conversion happens here
python etl/02_compute_trade_metrics.py     # Inherits USD values 
python etl/03_compute_peer_medians.py      # Inherits USD values
python etl/04_enrich_metrics_with_peers.py # Inherits USD values
python etl/05_build_map_data.py            # Inherits USD values

# Optional: Signal generation
python etl/06_generate_signals.py
python etl/07_build_ui_signals.py
python etl/08_enrich_ui_signals.py

2) Run the API (CORS enabled)

uvicorn api.server_full:APP --reload
# http://127.0.0.1:8000

Health:

curl -s 'http://127.0.0.1:8000/health' | jq

3) Endpoints (shapes)

/controls

curl -s 'http://127.0.0.1:8000/controls' | jq
# { countries: string[], years: number[], metrics: string[], metric_labels: Record<string,string> }

/map?year=&hs6=&metric=&country=&hs2=
	•	Returns world data or a single row when country is set.

curl -s 'http://127.0.0.1:8000/map?year=2023&hs6=851713&metric=delta_vs_peer' | jq '.[0]'
# [{ iso3, name, value, value_fmt, unit }]

/products?year=&top=&country=&hs2=

curl -s 'http://127.0.0.1:8000/products?year=2023&top=5' | jq
# [{ id, name, value, value_fmt, unit }]

/trend?hs6=&years=

curl -s 'http://127.0.0.1:8000/trend?hs6=851713' | jq
# [{ year, value, value_fmt, unit }]

/signals?country=&hs6=&type=&limit=

curl -s 'http://127.0.0.1:8000/signals?limit=5' | jq
# [{ type, year, hs6, partner_iso3, intensity, value_fmt, unit, ... }]

/meta
	•	Labels + thresholds from data/config.yaml

curl -s 'http://127.0.0.1:8000/meta' | jq

4) UI integration (Vite React example)

Create ui/.env.local:

VITE_API_BASE=http://127.0.0.1:8000

Temporary browser smoke test (drop at end of ui/src/main.tsx or main.jsx):

(async () => {
  const BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";
  console.log("[API BASE]", BASE);
  const res = await fetch(`${BASE}/controls`);
  console.log("[/controls]", await res.json());
})();

Then the real fetchers:

const BASE = import.meta.env.VITE_API_BASE || process.env.NEXT_PUBLIC_API_BASE;

export async function fetchControls() {
  const r = await fetch(`${BASE}/controls`); if (!r.ok) throw new Error("controls");
  return r.json();
}
export async function fetchMap(params = {}) {
  const q = new URLSearchParams();
  for (const [k,v] of Object.entries(params)) if (v != null) q.set(k, String(v));
  const r = await fetch(`${BASE}/map?${q}`); if (!r.ok) throw new Error("map");
  return r.json();
}
export async function fetchProducts(params = {}) {
  const q = new URLSearchParams();
  for (const [k,v] of Object.entries(params)) if (v != null) q.set(k, String(v));
  const r = await fetch(`${BASE}/products?${q}`); if (!r.ok) throw new Error("products");
  return r.json();
}
export async function fetchTrend({ hs6, years=10 }) {
  const q = new URLSearchParams({ hs6, years: String(years) });
  const r = await fetch(`${BASE}/trend?${q}`); if (!r.ok) throw new Error("trend");
  return r.json();
}
export async function fetchSignals(params = {}) {
  const q = new URLSearchParams();
  for (const [k,v] of Object.entries(params)) if (v != null) q.set(k, String(v));
  const r = await fetch(`${BASE}/signals?${q}`); if (!r.ok) throw new Error("signals");
  return r.json();
}

Happy‑path UI flow:
	1.	const { countries, years, metrics, metric_labels } = await fetchControls()
	2.	const year = Math.max(...years); const metric = "delta_vs_peer";
	3.	const bars = await fetchProducts({ year, top: 10 });
	4.	const hs6 = bars?.[0]?.id ?? "851713";
	5.	const map = await fetchMap({ year, hs6, metric });
	6.	const trend = await fetchTrend({ hs6 });
	7.	const signals = await fetchSignals({ limit: 10 });

5) Sharing externally
	•	Cloudflare Tunnel:

brew install cloudflared
cloudflared tunnel --url http://127.0.0.1:8000


	•	Or ngrok:

brew install ngrok/ngrok/ngrok
ngrok http 8000



Set your UI env to the public URL.

6) Troubleshooting
	•	404 /controls: ensure api/server_full.py has the /controls override and restart Uvicorn.
	•	CORS: your curl must send an Origin header to see Access-Control-Allow-Origin. Browsers are fine.
	•	Stale data: ETL rerun → cache invalidates automatically (mtime key).
	•	Country code: both ISO2 and ISO3 accepted; uses pycountry.
	•	HS6 string: always zero‑pad to 6 ("851713") if passing explicitly.

⸻
