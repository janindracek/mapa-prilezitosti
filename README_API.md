Health check: GET /health

Refactored API Architecture (September 2024)
	•	api/server_full.py – clean orchestration layer (15 lines, down from 955)
	•	api/routers/ – domain-separated endpoints (map, signals, products, insights, metadata)
	•	api/services/ – business logic (SignalsService, PeerGroupsService)
	•	api/data/ – data access layer (cache.py, loaders.py)
	•	api/settings/ – configuration management
	•	api/config.py – legacy configuration and defaults (metric labels, thresholds)
	•	api/formatting.py – value formatting + JSON-safe conversions
	•	api/normalizers.py – ISO and HS code normalization
	•	api/data_access.py – parquet access + cache
	•	api/helpers.py – helper functions for map, products, trend

Endpoints

GET /meta

Popisky metrik a prahy z config.yaml.

GET /controls

Seznam zemí, let, metrik a jejich popisků pro UI.

GET /map

Mapa světa pro zvolenou metriku a HS6.
Parametry: metric, year, hs6, hs2, country

GET /products

Top HS6 produkty.
Parametry: year, top, country, hs2

GET /trend

Trend pro vybraný HS6.
Parametry: hs6, years

GET /signals

Dynamické signály pro zvolenou zemi, nebo předpočítané top-N.
Parametry: country, hs6, type, limit, peer_group

GET /map/{hs6}

Vrací world_map.json (kompatibilita s původní UI cestou).

GET /peer_groups/complete

Kompletní informace o peer group včetně všech zemí v clusteru, bez ohledu na obchodní data.
Parametry: country, peer_group (human/opportunity/matching/default), year
Vrací: { cluster_id, cluster_name, peer_countries[], method, year }

GET /debug/peer_groups

Diagnostika obsahu peer_groups.parquet pro danou zemi.
Parametry: country

Datové soubory
	•	data/out/metrics_enriched.parquet (hlavní zdroj)
	•	data/ref/hs_mapping.csv – názvy HS6
	•	data/out/ui_shapes/signals_enriched.json – precomputed top-N signálů
	•	data/out/peer_groups.parquet – peer skupiny (strukturální)
	•	data/out/peer_groups_human.parquet – peer skupiny (geografické)
	•	data/out/peer_groups_opportunity.parquet – peer skupiny (příležitostní)
	•	data/out/human_peer_medians.parquet – mediány pro geografické peer skupiny

Cache
	•	Používá _get_metrics_cached()
	•	Invalidace při změně souboru (mtime)

Příklady použití