# Mapa příležitostí — Czech trade-opportunity dashboard

**Source of truth.** This README is the canonical description of the system. When code and this document disagree, one of them is a bug. The visual companion is `_finalization/architecture.html` (keep it in sync with this file). Prose-level working notes live in `_finalization/`.

> ## ⚠️ Status — rebuild in progress (2026-06)
> This document describes the **target** system (the contract we build to). It is being finalized through the modules in `_finalization/` (see `00_INDEX.md`). Where today's running code differs, it is flagged inline as **[current]** vs **[target]**, and the live baseline is in `_finalization/current-state.md`. The full list of doc↔code drifts and their adjudications is in `_finalization/DRIFT_REGISTER.md`.

---

## 1. What it is

For Czech exporters (and the Ministry of Industry), surface the highest-value **under-served foreign markets per product**. For a given product (HS6 6-digit code) and target market, the tool compares Czechia's share of that market's imports against a **peer benchmark** — the share comparable countries achieve — and flags large negative gaps as opportunities, alongside year-on-year movement signals.

Data source: BACI bilateral trade (HS22, years **2022–2023**). The dataset is refreshed roughly **once a year** (or when the statistical logic changes), so the heavy computation is a rare batch job and the served data is essentially static between refreshes.

> **Known methodology limitation (v2 backlog).** The peer-median benchmark is a useful but imperfect primitive — it benchmarks a *bilateral* quantity with a *unilateral* grouping and is blind to tariffs, distance, FTAs, and supply capacity. The v1 tool makes the existing concept honest and working; the deeper re-foundation (ITC supply × demand × ease-of-trade) is logged in `_finalization/V2_BACKLOG.md`, to revisit after the officials discussion. See `_finalization/trade-economics-challenge.md`.

---

## 2. Architecture at a glance

```
LOCAL ETL (heavy, ~once a year)        SERVING LAYER            HOSTED
BACI raw ─► core facts ─► peer        data/serving/*.parquet   one loader ─► FastAPI ─► React UI
            medians ─► signals  ──►   (~60–150 MB)        ──►   (parquet at startup)
```

- **[target]** The ETL's final stage emits a compact **serving layer** (`data/serving/*.parquet`, ~60–150 MB). The API reads **only** that, through a single loader. The ~1.5 GB raw/derived matrix never leaves the ETL stage. The serving artifact ships as a GitHub Release asset that the deploy downloads.
- **[current]** The API auto-switches to a hand-built `data/deployment/` CSV subset when present, via a parallel loader; there are also two other inconsistent serving paths. This is being collapsed to the single serving layer in module **M4b**.

Full annotated lineage (where dollars are scaled, where country codes convert, where signals are filtered): see `_finalization/architecture.html`.

---

## 3. Peer-group methodologies

**Two** independent definitions of "comparable market" (v1 — M3 ✓). Each produces (a) a **membership** map (which countries are peers) and (b) a **descriptor** (a Czech name + explanation). Membership and descriptor come from one shared source (the `*_explained.csv` files), and that same descriptor is what the app shows.

| Method (`id`) | Signal type | How groups are formed | Inputs | Clusters | Czechia's group |
|---|---|---|---|---|---|
| **Trade-structure** (`trade_structure`) | `Peer_gap_matching` | k-means cosine clustering | HS2 import-share profiles | 10 | #4 "Evropské jádro a vyspělá Asie" |
| **Geographic / human** (`human`) | `Peer_gap_human` | expert hand-curation | geography + development level | 23 | #3 "Střední a východní Evropa" |

**How the benchmark is computed — the honest median (M3 ✓).** The peer group is the **target market's** cluster (not Czechia's). For a product `hs6` and target market `t`, under method `m`:

> `peer_median_share(hs6, t) = median over { p ∈ cluster_m(t), p ≠ t, p ≠ CZE } of podil_cz_na_importu(hs6, p)`
> `delta_vs_peer = podil_cz_na_importu(hs6, t) − peer_median_share`  (negative ⇒ CZ under-penetrates `t` relative to its peers)

In words: "in markets like `t`, Czechia captures a median X% of this product's imports; in `t` it captures Y%; the gap is the flag." Leave-one-out on `t`; CZE excluded (CZ doesn't export to itself). Computed over the **full all-country BACI** (M4a coverage) for every year, in `etl/03b` — mirroring the recovered honest computation in `etl/archive/27_compute_peer_medians.py`. The two methods key on different clusters, so for the same country they flag **genuinely different products** (measured top-3 product overlap between methods ≈ 0.05 Jaccard).

- **Descriptors:** both methods carry a name + explanation in **Czech prose**, from the shared `*_explained.csv`, fed into the label registry `data/ref/labels.csv` (methodology rows, `status=ok`). Trade-structure was translated EN→CZ in M3; human was already Czech.
- **Membership is frozen.** The `*_explained.csv` is the source of truth (it co-locates membership + descriptor, per the project rule). Creation code is archived (`etl/archive/30_build_peer_groups.py` = trade-structure cosine k-means; human is hand-curated) — kept as **provenance**, not the happy path: re-clustering would renumber clusters and break the descriptor mapping.
- **Opportunity retired (v1).** The former third method (`opportunity` = k-means on HS6 shares + a **2-point CAGR** + openness) was **retired in M3**: a 2-year CAGR is noise, mixed-scale k-means is a preprocessing artifact, and it estimated the same flawed quantity as the others (see `_finalization/trade-economics-challenge.md`). Its membership parquet stays on disk unused; its label rows are `status=retired`. The proper **supply × demand × ease-of-trade** replacement is **v2** (`_finalization/V2_BACKLOG.md`).
- **Previously faked medians (now fixed):** `etl/03b` used to return `human = statistical × 0.85`, `opportunity = statistical × 1.15`, and an empty `geographic` stub — all gone; `03b` now computes the real per-cluster median above.
- Legacy `data/ref/peer_groups.json` (V4, Benelux, Nordics, ASEAN…) is a pre-existing hand-made set, slated to retire.

---

## 4. Signals

A signal = one (product, market, year) flagged as notable. **Four** types (v1):

| `type` | Canonical Czech label | Meaning |
|---|---|---|
| `Peer_gap_matching` | Benchmark (strukturální) | CZ below the trade-structure peer median |
| `Peer_gap_human` | Benchmark (geografický) | CZ below the geographic peer median |
| `YoY_export_change` | Nárůst exportu (YoY) | Large year-on-year change in CZ exports |
| `YoY_partner_share_change` | Navýšení podílu na importu | Large YoY change in the partner's share of CZ exports |

> `Peer_gap_opportunity` was **retired in M3** along with the opportunity methodology (§3); its `labels.csv` rows are `status=retired`. The supply×demand replacement is v2.

> **[current] Label inconsistency to fix (M5):** `SignalsList.jsx` uses *two different* Czech vocabularies for the same type — section headers say "Benchmark (statistický, pohled vpřed / současný)" while badges say "(příležitostní / strukturální)". `labels.csv` is the **canonical** set (M3 set the methodology + signal-type rows `ok`); M5 wires the UI to it. Dead label branches (`YoY_import_change`, `Peer_gap_below_median`) should be removed.

### Two-tier selection **[target]**
- **Strong** signals meet disciplined thresholds (peer-gap ≥ 20%, YoY ≥ 30%, etc. — §9). Surface at most ~10 per country.
- If a country has **fewer than 5** strong signals, backfill up to 10 with **permissive** weak signals (e.g. 10% ≤ gap < 20%), shown as a visually separate, flagged category — so a thin market (e.g. a trade-mission target) still gets actionable info.
- Selection happens **at request time** in the API; the ETL serves the full, un-capped signal set. **[current]** the ETL pre-filters signals three times (3/country/method, then top-3, then 2023-only), discarding the data the two-tier model and the analytics tab need.

### Analytics side-tab **[target]**
A filterable table over the **full** signal set, for power users / analysts. Requires the un-capped serving set above.

---

## 5. Data dictionary

The names below are carried from the fact-base through the API to the UI. This section is the contract for every field the app surfaces.

### Fact-base / core_trade — per (year, hs6, partner_iso3)
| Field | Meaning | Units |
|---|---|---|
| `export_cz_to_partner` | CZ exports to this partner of this HS6 | USD |
| `import_partner_total` | Partner's total imports of this HS6 (all sources) | USD |
| `export_cz_total_for_hs6` | CZ's total world exports of this HS6 | USD |
| `podil_cz_na_importu` | CZ share of partner's imports = `export_cz_to_partner / import_partner_total` | fraction |
| `partner_share_in_cz_exports` | Partner's share of CZ's exports of this HS6 | fraction |
| `YoY_export_change` | Relative YoY change of `export_cz_to_partner` | fraction |
| `YoY_partner_share_change` | Relative YoY change of `partner_share_in_cz_exports` | fraction |
| `delta_vs_peer` (×2 methods) | `podil_cz_na_importu − peer_median_share` (negative ⇒ under-penetration) | fraction |
| `peer_median_share` (×2 methods) | Peer-group median of CZ-import share (median over the target's cluster peers; §3) | fraction |

Dollars are scaled **kUSD → USD exactly once**, in `etl/01` (`TRADE_UNITS_SCALE`, default 1000) — the duplicate scale formerly in `etl/05` was removed in **M4a** (✓); `etl/05` now reshapes `metrics.parquet` instead of re-reading raw. Country codes are normalized through **one central module** (`country_ref`, backed by BACI's own committed code table `data/ref/baci_country_codes.csv`) — done in **M4a** (✓). The prior pycountry path silently dropped the ~6 BACI codes that deviate from ISO-3166 (**USA=842, France=251, Norway=579, Switzerland=757, India=699**, + the "Other Asia, nes" aggregate `S19`); now **zero dropped**.

That code table is the canonical **BACI ↔ ISO-3166 crosswalk** — it carries *both* numbering systems side by side: `country_code` (BACI numeric), `country_iso2`/`country_iso3`, and `iso_numeric` (ISO-3166-1 numeric). The BACI and ISO numerics **disagree** for USA (842/840), France (251/250), Norway (579/578), Switzerland (757/756), India (699/356), so a consumer can key on whichever system its library expects. `country_ref` exposes `num_to_iso3` / `iso3_to_num` (BACI), `iso3_to_iso_numeric` / `iso_numeric_to_iso3` (ISO-3166), and `baci_num_to_iso_numeric` (bridge); aggregates like `S19` have a blank `iso_numeric`. Regenerate the sheet with `etl/00_build_country_ref.py`.

### Signal record (e.g. `/top_signals`)
| Field | Meaning |
|---|---|
| `type` | one of the four signal types (§4) |
| `year`, `hs6`, `partner_iso3` | the (product, market, year) keys |
| `value` | the underlying metric value (for peer-gap: CZ's `podil_cz_na_importu`) |
| `intensity` | signal strength = `abs(delta_vs_peer)` for peer-gaps; ranking key |
| `delta_vs_peer`, `peer_median` | the gap and the benchmark it's measured against |
| `yoy` | YoY value (for YoY signal types; null otherwise) |
| `method` | peer methodology id (`human`/`trade_structure`) |
| `peer_countries`, `peer_count` | the peer group membership shown to the user |
| `methodology` | embedded descriptor object: `methodology_name`, `methodology_description`, `peer_countries`, `country_count` — the text the app displays |

> **Whose peer group? [current bug]** `/top_signals` and `/bars?mode=peer_compare` currently return *different* peer sets for the same country. The contract **[target]**: the peer group is the **target market's** group (the markets comparable to the selected country), consistent across every endpoint. Fix in M3.

### Map metrics (the two map logics)
| UI label | metric id | fact-base column | scale |
|---|---|---|---|
| Český podíl na importu | `cz_share_in_partner_import` | `podil_cz_na_importu` | % |
| Celková hodnota exportu | `export_value_usd` | `export_cz_to_partner` | USD |

### KeyData / `/insights_data` tiles — per (importer, hs6, year)
| Field | Meaning |
|---|---|
| `c_import_total` | partner's total imports of the HS6 (USD) |
| `cz_to_c` | CZ exports to the partner (USD) |
| `cz_share_in_c` | CZ share of the partner's imports (= `podil_cz_na_importu`) |
| `cz_world_total` | CZ total world exports of the HS6 (USD) |
| `median_peer_share` | peer benchmark share |
| `import_yoy_change` | YoY change in the partner's imports |
| `cz_delta_pct` | **[current bug]** duplicates `import_yoy_change`; should be CZ's own YoY delta |

> **[current bug]** `median_peer_share` from `/insights_data` (0.0 observed) disagrees with `peer_median` from `/top_signals` (0.108) for the same DEU/870323 — two different sources. Unify against the single serving layer (M4b).

### Label registry — one concept, many surfaces

The same concept is shown with **different strings depending on where it appears** (section header vs badge vs card title vs short/legend vs tooltip vs full-text panel vs map title). To stop these from drifting (today the section header and badge for the same signal type literally disagree), there is **one canonical registry**: `data/ref/labels.csv`.

- **One row per concept** (`id`), `kind` = `signal_type | methodology | map_metric | metric`, then **one column per display surface** (`section_header, badge, card_title, short_label, tooltip, full_description, map_title`), plus `status` (`ok|review|todo`) and `notes`.
- **Czech is primary** (the app is Czech). `{hs6}`/`{year}` are interpolation placeholders.
- **Source of truth:** Claude owns this CSV. **[target]** the UI imports from it (a generated JSON view per the `_finalization` generated-view convention) instead of hardcoding strings in `SignalsList.jsx` etc. (wired in **M5**). Methodology `full_description` cells are the peer-group **descriptors** produced in **M3** (all Czech).
- This generalizes the older `config.yaml: metric_labels` (id → one label) into id → {surface → label}.

---

## 6. API endpoints

`uvicorn api.server_full:app --host 0.0.0.0 --port 8000`

| Endpoint | Returns |
|---|---|
| `GET /health` | `{status, message}` |
| `GET /controls` | `{countries[], years[], metrics[]}` — dropdown data |
| `GET /meta` | `{metric_labels, thresholds}` (from `config.yaml`) |
| `GET /map_v2?hs6&year&metric` | `[{iso3, name, value, value_fmt, unit}]` — choropleth |
| `GET /top_signals?country&limit` | balanced signals across types (two-tier, §4) |
| `GET /signals?country&method&limit` | signals filtered by method |
| `GET /signals/methodologies` | methodology metadata + descriptions |
| `GET /signals/comprehensive?country&hs6` | full signal bundle for a (country, product) |
| `GET /bars?mode=products\|partners\|peer_compare&hs6&year&country&peer_group&top` | bar-chart data |
| `GET /products?year&top&country` · `GET /trend?hs6&years` | product bars · time series |
| `GET /insights?importer&hs6&year` · `GET /insights_data?importer&hs6&year` | narrative text · KeyData tiles |
| `GET /peer_groups/complete?country&peer_group&year` · `…/explanation?method&country&year` | peer membership · descriptor |

**[current] To delete (M4b):** the `data/deployment` CSV branch, the dead `api.shapes` map path, the `/signals_unified` second source, and the undocumented `/bars_v2`.

The AI insight text (`/insights`) runs on OpenAI in the non-deployment path and falls back to a deterministic Czech template otherwise; it carries a visible disclaimer banner. Moving to Claude (or precompute) is module **M6**.

---

## 7. UI blocks (what consumes what)

Czech UI. Blocks: **pre-selections** (`/controls`, defaults), **clicking/interactions** (signal click sets year+hs6+metric+country and refetches; map country-click synthesizes a signal; bar click sets hs6), **descriptors** (`/peer_groups/*`), **chart/bars** (3 modes), **map** (two logics, §5), **trend mini**, **KeyData tiles**, **insight text**. Full mapping in `_finalization/architecture.html` §③.

---

## 8. Pipeline & annual refresh

```bash
export TRADE_UNITS_SCALE=1000
python etl/01_build_base_facts.py            # raw BACI → fact_base — only $-scale point; OUTER-join → all 226 importers (M4a ✓)
python etl/02_compute_trade_metrics.py       # shares + YoY + prior-year/delta columns → metrics
python etl/05_build_map_data.py              # reshape metrics → ui_shapes/map_rows (no re-scale; M4a ✓)
python etl/03b_compute_all_peer_medians.py   # REAL peer medians ×2 methods (trade_structure + human; M3 ✓)
python etl/04b_enrich_metrics_with_all_peers.py
python etl/06b_generate_comprehensive_signals.py   # FULL set, no premature caps [target]
# [target] final stage: emit data/serving/*.parquet ; one rebuild-all.command runs the whole chain with assertions [M4b]
```
> **M4a verification:** double-click `_finalization/verify-M4a.command` — rebuilds 01→02→05 from raw and asserts all-country coverage (205→226), single dollar-scale point, zero dropped codes, and integrity (no bilateral exceeds the partner's import or CZ's world total).
> **M3 verification:** double-click `_finalization/verify-M3.command` — rebuilds 01→02→03b→04b→06b and asserts two real methods only (opportunity retired), medians match an independent recompute (not the old ×0.85/×1.15 fakes), the two methods recommend genuinely different products per country (top-3 Jaccard ≈ 0.05), and the Czech descriptors are set.
**[current]** there is no single orchestrator and several documented steps reference moved/archived scripts; `rebuild-all.command` (M4b) makes the chain reproducible. Refresh procedure: run the ETL locally → upload `data/serving/` as a Release asset → redeploy pulls it.

---

## 9. Config — `data/config.yaml`

`thresholds` define the **strong** signal tier (two-tier model, §4). **[current]** they were loosened to "VERY PERMISSIVE" during a deployment scramble; **[target]** restore disciplined values:

| key | current | target (strong tier) |
|---|---|---|
| `MIN_EXPORT_USD` | 10 000 | 100 000 |
| `MIN_IMPORT_USD` | 500 000 | 5 000 000 |
| `S1_REL_GAP_MIN` | 0.001 | 0.20 |
| `S2_YOY_THRESHOLD` | 0.05 | 0.30 |
| `S3_YOY_SHARE_THRESHOLD` | 0.05 | 0.20 |
| `MAX_TOTAL` / `MAX_PER_TYPE` | 5000 / 2000 | ~10 surfaced (full set still computed) |

`metric_labels` map field ids to UI tooltip text.

> **M3 observation (fix in M4b):** with the relative-only `S1_REL_GAP_MIN` and no absolute floor, some peer-gap signals pass on a **near-zero peer median** (e.g. a small `human` cluster where every peer has ~0% CZ share → a 100% relative gap on a trivial absolute base). The real medians are correct; restoring the disciplined thresholds above (an **absolute** gap/market-size floor) in M4b filters these out.

---

## 10. Local dev

Double-click **`run-local.command`** (boots API on :8000 + UI on :5173 and opens the browser), or:
```bash
.venv/bin/python -m uvicorn api.server_full:app --host 127.0.0.1 --port 8000   # API
cd ui && npm run dev                                                            # UI :5173
```
Use the repo `.venv` (Python 3.13; has the deps). `ui/.env.local`: `VITE_API_BASE=http://localhost:8000`.

To check the **production build** (not the dev server) end-to-end, double-click **`build-ui.command`**: it runs `npm ci && npm run build` and serves the built `ui/dist/` *through the API* on :8000 — same as the deploy — so you can confirm there's no blank page and data still loads.

### Frontend build & assets (M5 chrome)
- **Build-on-deploy.** `ui/dist/` is gitignored and never committed; `deploy/build.sh` rebuilds the UI fresh every deploy (`npm ci && npm run build`, with `RENDER=true` so console/debug are stripped). The API serves `ui/dist/` at `/`. This avoids the stale-`dist` blank-page that a committed build artifact caused. A build failure fails the whole deploy on purpose.
- **World map geometry is bundled** at `ui/public/world.json` (served at `/world.json`), not fetched from `raw.githubusercontent.com` — so the map works on restricted/offline (ministry) networks.
- **ECharts is tree-shaken** (`ui/src/lib/echarts.js` registers only the map/bar charts + needed components) — the echarts chunk dropped ~1.05 MB → ~562 kB.
- Map tooltips show **Czech** country names (from `/ref/country_names_cz.json`).

---

## 11. Where things are

| Path | What |
|---|---|
| `country_ref.py` | **single source of truth for country codes** — BACI numeric ↔ ISO-3166 (alpha-2/alpha-3/numeric) ↔ name, backed by the committed **crosswalk** `data/ref/baci_country_codes.csv` (regenerate via `etl/00_build_country_ref.py`). Used by `etl/01, 03b, 05`. (M4a) |
| `etl/` | the pipeline (current happy path: `01, 02, 03b, 04b, 05, 06b`; `archive/` = legacy) |
| `api/` | FastAPI: `server_full.py` (entry), `routers/`, `services/`, `data/`, `settings/` |
| `ui/` | React + Vite + ECharts (`ui/dist/` is gitignored — built on deploy; geometry bundled at `ui/public/world.json`) |
| `deploy/build.sh` | deploy build: installs deps, builds the UI fresh, validates the API |
| `run-local.command` · `build-ui.command` | double-click: boot dev (API+UI) · build prod UI and serve it through the API |
| `data/deployment/` | **[current]** hand-built serving subset (→ replaced by `data/serving/` in M4b) |
| `_finalization/` | the rebuild workspace: `00_INDEX.md`, `architecture.html`, module briefs, drift register, logs |
