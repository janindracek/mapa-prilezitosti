# LOG — decisions & session handoff

Newest first. One entry per working session: what changed, what was decided, what the next session should pick up.

---

## 2026-06-09 — M6 insights → Claude ✅ impl (branch `m6-insights`)

**Done** (implemented by the orchestrator session after the background subagent came back read-only — subagents can't Write/Edit/Bash-execute)
- `api/insights_text._llm_generate` rewritten from OpenAI → **Anthropic Messages API** via stdlib `urllib` (no SDK dependency → Render stays light): `POST https://api.anthropic.com/v1/messages`, headers `x-api-key` + `anthropic-version: 2023-06-01`, the Czech system prompt moved to the top-level `system` field, response parsed from `content[].text` blocks. Model via `INSIGHTS_MODEL` (default `claude-opus-4-8`). **No `temperature`** (rejected on Opus 4.7/4.8). Confirmed model id + API shape via the `claude-api` skill.
- Key handling: `ANTHROPIC_API_KEY` from env, **server-side only** (never shipped to the client). `INSIGHTS_USE_LLM` gating + the deterministic fallback unchanged in behavior.
- **Fallback rewritten in Czech** (was English) + None-guarded (`_pct` helper) so missing metrics don't crash.
- **Fixed the "USA (747%)" defect** in `extract_context`: the serving layer has no third-country bilateral flows, so "top suppliers to market X" is uncomputable — now lists the largest global import markets for the HS6 (no bogus % vs the selected market). Relabeled accordingly in the fallback + prompt.

**Decided** — **live Claude call per request + deterministic fallback** (the recommended approach; full ETL precompute impractical at ~1.3M HS6×market combos). Hybrid precompute-of-surfaced-signals left as an optional latency/cost optimization.

**Verified** — boots; no-key path returns clean **Czech** fallback text (and the M4b `_fmt_usd` USD fix holds: "12.7 mld. USD"). **The live Claude path needs an `ANTHROPIC_API_KEY` to verify end-to-end** — set it + `INSIGHTS_USE_LLM=1` and hit `/insights?importer=DEU&hs6=870323&year=2023`.

**Scope note** — the **disclaimer banner** lives in `ui/src/App.jsx:261` (already correct Czech: "VAROVÁNÍ: obsah vygenerovaný automaticky skrz LLM…"). It's an M5-owned `ui/` file, so M6 left it untouched (no change needed) to avoid an App.jsx collision with the parallel M5 track.

**To merge:** branch `m6-insights` → `main`. Touches only `api/insights_text.py` (+ this LOG + the M6 `00_INDEX` row). No `ui/` overlap with M5.

---

## 2026-06-09 — M4b serving layer + path unification ✅ (branch `m4b-serving`)

**Done** (isolated worktree off `main`)
- **One serving layer.** New `etl/07_build_serving.py` assembles `data/serving/` (~43 MB): `core_trade` (= metrics_all_peers: 226 importers, both years, real ×2 medians, **one** `import_partner_total`), `signals` (full banded set), `peer_groups` (membership + Czech descriptor per cluster, 2 methods), `hs6_names`, `countries` (EN + CZ). Built/refreshed by `rebuild-all.command`.
- **Full signal set + disciplined floors.** `06b` rewritten: restored §9 floors (MIN_EXPORT 100k, MIN_IMPORT 5M, YoY 0.30/0.20), peer-gap candidate floor `S1_REL_GAP_WEAK=0.10` with a `band` (strong ≥0.20 / weak 0.10–0.20); removed the per-country/global caps (request-time selection = M5). Added a material-export floor to the YoY signals (killed the near-zero-base noise). Full set = **108,140** signals (was 4,989 capped).
- **API → ONE loader.** New `api/data/serving.py` (map/products shaping + names). Settings collapsed to `data/serving/` only (no `DEPLOYMENT_AVAILABLE` branch). Repointed `data_access`, `signals_unified`, `loaders.load_peer_groups` (reads the combined serving peer_groups, filters by method). Rewrote routers map/signals/products/insights/metadata to the single source. **Deleted** `api/data/deployment_loader.py`, `api/shapes.py`, the `/signals_unified` endpoint, and `/bars_v2`. Deleted the committed `data/deployment/`.
- **Bugs fixed:** `import_partner_total_x/_y` collision (gone by construction); `cz_delta_pct` now CZ's own export YoY (was a dup of import YoY); `median_peer_share` in `/insights_data` is real & non-zero (was 0.0, different source); `insights_text._fmt_usd` no longer ×1000 (data is USD, not kUSD). Added a NaN/numpy-safe default `JSONResponse` (Starlette's `allow_nan=False` was 500-ing on the NaN cells in YoY signals).
- **Subtle catch:** `signals_unified` mapped `trade_structure → kmeans_cosine_hs2_shares` for filtering, but M3's `06b` emits `method='trade_structure'` → would have returned empty. Fixed the mapping.
- **Descriptor completion:** translated the trade_structure per-cluster descriptors EN→CZ in `peer_groups_hs2_explained.csv` and removed the stray numeric codes (490/579/251/699/842/757 → country names) from its `countries` lists — finishing two items the architecture flagged.
- **Verified by boot:** API boots on `data/serving/`, every endpoint returns 200. `/map_v2` = **226 countries**; `/top_signals DEU` balanced across the 4 live types (no opportunity); `/insights_data` tiles correct. `rebuild-all.command` green (9/9 integrity checks: serving==ETL, 226 coverage, single import col, full banded set, 2 methods, no opportunity, settings point only at data/serving, deployment gone).

**Decided**
- **`data/deployment/` deleted now; `data/serving/` gitignored** (Jan's call delegated). Reason: the deployment subset was a hand-built shortcut for the old deploy — keeping a stale committed copy invites the drift we're killing. The serving layer is machine-generated (rebuild-all) and ships as a Release asset in M7.
- **core_trade drops the `peer_countries_*` JSON columns** (map/bars/insights don't need them; signals + peer_groups already carry memberships).

**Flagged for M5** (Jan): **surface methodology notes/descriptors prominently in the dashboard** (the Czech descriptors now exist in `labels.csv` + serving `peer_groups`). Also pending M5: the strong/weak two-tier *display* + analytics tab (data is ready — `band` column), and wiring the UI to `labels.csv`. **Known duplication** (M5 cleanup): `api/peer_group_registry.py` carries its own hardcoded Czech cluster descriptions that don't perfectly match `*_explained.csv`/`labels.csv` — unify when the UI consumes the registry.

**Env/workspace:** worktree `/Users/janindracek/Documents/mapa-m4b`; symlinked the gitignored BACI input dirs + `.venv`. Rebuilt the whole chain. API smoke-tested with `INSIGHTS_USE_LLM=0`.

**To merge:** branch `m4b-serving` → `main`. Touches `etl/06b,07`, `data/config.yaml`, `data/out/peer_groups_hs2_explained.csv`, the `api/` serving rewrite, `rebuild-all.command`, `.gitignore`, deletes `data/deployment/` + `api/data/deployment_loader.py` + `api/shapes.py`, docs. **No `ui/` files** — but note `ui/` will consume the new shapes in M5.

**Next:** M5 (data features) — two-tier display, analytics tab, label-registry + methodology-notes wiring. Or M6 (insights OpenAI→Claude). Read `00_INDEX.md`.

---

## 2026-06-08 — M3 methodology rebuild ✅ (branch `m3-methodology`)

**Done** (isolated worktree off `main`, after M4a merged)
- **Two real, distinct peer methods** replace the fakes. `etl/03b` rewritten: it now computes the **honest median** — for (year, hs6, target market `t`) and method `m`, `peer_median_share = median of podil_cz_na_importu over { p ∈ cluster_m(t), p ≠ t, p ≠ CZE }`. Leave-one-out on the target, CZE excluded. Mirrors the recovered honest computation in `etl/archive/27_compute_peer_medians.py`, generalized to all years + CZE exclusion. The 0.85/1.15 scaling, the opportunity branch, and the empty `geographic` stub are all gone.
- **Verified real, not faked:** an independent median recompute matches the pipeline output on 300/300 sampled rows (DEU/870323: trade_structure 0.01539 over 28 peers, human 0.01573 over 4 peers — both reproduced exactly).
- **Genuinely different recommendations:** mean top-3 product overlap between the two methods = **0.05 Jaccard** over 149 countries (≈ fully different). E.g. DEU → trade_structure flags paper/steel (481320, 722220, 722820), human flags fuels/oils (270112, 270900, 271121). The old fakes (constant scaling) collapsed all methods to one ranking.
- **Opportunity retired (Jan's call):** the HS6-shares + **2-point CAGR** + openness method is the "most wrong" (CAGR over 2 years = noise; mixed-scale k-means is a preprocessing artifact). Removed from `03b`/`04b`/`06b` and the label registry (`status=retired`); membership parquet left on disk unused. Proper ITC-style supply×demand×ease-of-trade replacement = **v2**.
- **Descriptors → `data/ref/labels.csv`:** `trade_structure` translated EN→CZ, `human` already CZ, both methodology rows `status=ok`; `Peer_gap_*` signal rows for the 2 survivors `ok`, opportunity rows `retired`.
- **Pipeline cleanups:** removed the dead opportunity ranking branch from `06b` and the dead `geographic` backward-compat block from `04b`.
- **Acceptance:** `_finalization/verify-M3.command` (double-click) rebuilds 01→02→03b→04b→06b and asserts: 2 methods only / no opportunity, medians match an independent recompute, Jaccard < 0.30, Czech descriptors set. **Runs green.**
- **Docs:** README §3 rewritten (2 methods + exact median math + retirement), §4 (4 signal types), §5 (×2 methods), §8/§9 notes; `architecture.html` §②/§④/§⑤ updated. Thorough per Jan's "everything in README + the HTML map."

**Decided**
- **Membership stays frozen** (the `*_explained.csv` is the source of truth, co-locating membership + descriptor per Jan's rule). The archived clustering script (`etl/archive/30_build_peer_groups.py`, trade_structure cosine k-means) is kept as **provenance**, NOT wired into the happy path — re-clustering would renumber clusters and break the descriptor mapping. (human is hand-curated, no clustering.) Flagging in case Jan wants a verified re-cluster later.
- **Access filters (distance/FTA/market-size) deferred** — Jan wants a dedicated design conversation; none built this session. No distance/FTA/tariff data exists in the repo (only market-size is free from BACI). Logged as the open M3-follow-up.

**Flagged for M4b** (pre-existing, surfaced by M3): with relative-only `S1_REL_GAP_MIN` and no absolute floor, some peer-gap signals pass on a near-zero peer median (tiny `human` clusters where every peer has ~0% CZ share → 100% relative gap on a trivial base). Medians are correct; restoring disciplined/absolute thresholds (README §9) filters these — that's M4b.

**Env/workspace**
- Worktree `/Users/janindracek/Documents/mapa-m3`; symlinked only the gitignored inputs *inside* `data/parquet` (BACI dirs + `trade_by_hs2_imports.parquet`) — no tracked-file clobber this time. Rebuilt fact_base→metrics (M4a code) first. `.venv` symlinked (py3.13/pyarrow21).

**To merge:** branch `m3-methodology` → `main`. Touches `etl/03b,04b,06b`, `data/ref/labels.csv`, `_finalization/verify-M3.command`, README, architecture.html, LOG, 00_INDEX (M3 row only) — no `ui/` overlap.

**Next:** M4b — serving-layer collapse + path unification (now the data is real). Read `modules/M4b_serving.md`. Also pick up the deferred access-filters design conversation and the §9 threshold restoration there.

---

## 2026-06-07 — M5 frontend-chrome ✅ (Track B, parallel to M4a; branch `m5-frontend-chrome`)

Scope: **UI chrome only** — independent of the data track (M4a/M3/M4b). Touched only `ui/`, `deploy/build.sh`, and a new root `build-ui.command`. Data-dependent M5 features (two-tier signals, analytics tab, label-registry wiring) deliberately left for a later M5-data session (need M4b).

**Done**
- **World geometry bundled.** Saved the exact GeoJSON the app used (holtzy `world.geojson`, 177 features, 252 KB) to `ui/public/world.json` (the old `world.json` was a 65-byte error-string stub). `WorldMap.jsx` now fetches `/world.json`, not `raw.githubusercontent.com` → no blank map on a firewalled/offline ministry network. Same source = no name-matching regression.
- **Build ships correctly (build-on-deploy, Jan's pick).** `ui/dist/` was gitignored yet 9 stale files were tracked — incl. an `index.html` pointing at JS bundles that were **never committed** → Render's `build.sh` saw `dist/index.html`, *skipped the build*, and served a blank page. Fix: `git rm --cached ui/dist` (stays ignored); `deploy/build.sh` now **always** rebuilds (`npm ci && npm run build`, `RENDER=true` to strip console), fails the deploy on build error (no silent stub fallback), and errors clearly if Node/npm is absent. Added double-clickable **`build-ui.command`** (builds + serves `dist/` through the API on :8000, true prod parity).
- **ECharts tree-shaken.** New `ui/src/lib/echarts.js` imports `echarts/core` + only MapChart/BarChart/Tooltip/VisualMap/Grid/CanvasRenderer; `WorldMap`/`ProductBarChart` use `echarts-for-react/lib/core`. echarts chunk **~1.05 MB → 562 kB** (gzip 188 kB). (`EChart.jsx` keeps the full import but is test-only — not in the app bundle.)
- **Czech map tooltips.** Region English name → Czech via `referenceData.countryNames` (`/ref/country_names_cz.json`). Verified live: hovering shows "Gruzie"/"Estonsko", not "Georgia"/"Estonia".
- **Dead code / console cleanup.** Removed `SHOW_SKELETON` flag (layout now unconditional, visually identical), the commented `BenchmarkGroup` block, the `main.jsx` "TEMP API SMOKE TEST", and ~50 debug `console.*` (kept genuine `warn`/`error`). Also removed an **invalid `projection:{type:'mercator'}`** map config that was silently ignored but spamming ~500 `[ECharts] project and unproject…` warnings per render (map view unchanged — the nested `center` was never applied).

**Verified**
- `RENDER=true npm run build` clean: all 4 assets present & referenced by `index.html`, **0 `console.` in the built app chunk**, `world.json` (252 KB) in `dist`, no iCloud `* 2.js` dupes.
- Live (dev :5173 + API :8000): full page renders, map colored from bundled geometry, Czech tooltips, signals/bars/controls all work. Before/after screenshots captured inline (M1 PNGs in `screenshots/` remain the on-disk baseline).
- Tests: `npm run test` = **5 failed / 10 passed**, identical to `main` — all 5 are pre-existing stale placeholder tests (assert text like "Regions: 3" the current components never render). Not introduced here; left for a test-cleanup pass.

**Flagged (out of scope, pre-existing):** `KeyData.jsx:157` calls `.toLocaleString()` on null, so a failed/empty `/insights_data` fetch crashes the whole app via the ErrorBoundary (observed during a transient API blip). Not a file this track touched — flagged as a separate task.

**Next:** merge branch `m5-frontend-chrome`. Remaining M5 (two-tier display, analytics tab, consume `data/ref/labels.csv`) is an **M5-data** session after **M4b**.
---

## 2026-06-07 — M4a foundation ✅ (own session, Track A)

**Done** (branch `m4a-foundation`, isolated worktree off `main`)
- **Root cause nailed with numbers.** Raw BACI has **226 importers**; the old `etl/01` converted BACI numeric→ISO3 with **pycountry** (ISO-3166), which silently dropped the 6 BACI codes that deviate from ISO: **USA=842, France=251, Norway=579, Switzerland=757, India=699**, + aggregate **490 "Other Asia, nes"→S19** (mostly Taiwan). Compounded by a **LEFT-join** keyed on CZ's export partners → only **205** importers reached the table. Authoritative fix already on disk: BACI's own `data/raw/country_codes_V202501.csv` (238 rows, complete).
- **(a) Central country-code module — `country_ref.py` (repo root).** Single source of truth, backed by a **committed** copy `data/ref/baci_country_codes.csv` (raw dir is gitignored — the map must travel with the code). API: `num_to_iso3 / iso3_to_num / iso3_to_name / cz_numeric() / map_series_num_to_iso3`. BACI table only, **no pycountry**, for numeric↔iso3. Handles BACI's 3 duplicate-iso3 historical twins (BEL 56/58, DEU 276/280, SDN 729/736) by preferring the active (non-`(...YYYY)`) entry in reverse lookups. `api/normalizers.py` left intact — it parses arbitrary *user input* (names/alpha2), a different job.
- **(a′) BACI↔ISO-3166 crosswalk (Jan's ask).** The sheet now carries *both* numbering systems: added an `iso_numeric` (ISO-3166-1 numeric) column alongside the BACI `country_code`, so a consumer can key on whichever a library expects. They disagree for USA 842/840, France 251/250, Norway 579/578, Switzerland 757/756, India 699/356 (+ historical twins); aggregates (S19 etc.) have blank `iso_numeric`. New reproducible generator `etl/00_build_country_ref.py` (pycountry-derived from iso3; self-contained, no raw data needed). New helpers `iso3_to_iso_numeric / iso_numeric_to_iso3 / baci_num_to_iso_numeric`. Documented in README §5/§11 + architecture.html §⑤.
- **(b) `etl/01` → OUTER-join + central codes.** Coverage **205 → 226**; hard assertions baked in (zero unmapped codes; coverage == raw universe; no null iso3; `export ≤ import`). fact_base 338k → **1.78M rows** (an ETL intermediate; compaction is M4b).
- **(b) Prior-year/delta columns migrated into `etl/02`** (`export_cz_to_partner_prev`, `delta_export_abs`, `export_cz_total_for_hs6_prev`) — so the map reads them instead of re-deriving from raw.
- **(c) `etl/05` rebased onto `metrics.parquet`** — no more raw `trade_by_pair` read, **duplicate `* TRADE_SCALE` deleted**. Dollars now scaled in exactly one place (`etl/01`). Map covers all 226 (USA/FRA/CHE/IND/NOR/S19 verified present).
- **`etl/03b`**: replaced hardcoded `iso=='203'` with `cr.cz_numeric()` and the local pycountry reimplementation with `country_ref` (same dropped-code bug lurked here). Faked-median scaling untouched (M3).
- **Acceptance gate:** `_finalization/verify-M4a.command` (double-click) rebuilds 01→02→05 and asserts coverage 205→226, single $-scale point, zero dropped codes, integrity. **Runs green.**
- Docs synced: README §5/§8/§11 flags flipped, `architecture.html` §⑤ status rows → ✅ + contrast-note clarified.

**Decided**
- **Architecture call (Jan delegated): central code module lives at repo root (`country_ref.py`) + committed CSV**, rather than rewriting `api/utils/country_codes.py`. Reason: smallest blast radius for M4a, clean etl↔api sharing, no API-behavior change bleeding into M4b. Logged here + README §11 + architecture.html.
- **Aggregate S19 (490) is kept, not dropped** — it's real trade; it just lacks map geometry until one is supplied (M5). Net coverage = 226.
- **Live API untouched** — `/map_v2` still reads the `data/deployment/` CSV (a stubbed-out parquet path), so the live map won't show the new countries until **M4b** collapses the serving path. M4a acceptance is on the parquet artifacts, by design.

**Flagged for M3** (pre-existing, NOT introduced here): `etl/03b`'s opportunity path reads `peer_groups['iso']` but that parquet's column is `iso3` → it's *always* a KeyError, so opportunity peer medians have never generated (matches "opportunity has none" in README). M3 owns the opportunity rebuild.

**Env notes**
- Must use the repo **`.venv` (py3.13, pyarrow 21)** — anaconda's `python3` (pyarrow 19) cannot read the BACI parquets ("Repetition level histogram size mismatch"). The `.command` auto-prefers `.venv/bin/python`.
- Worked in worktree `/Users/janindracek/Documents/mapa-m4a` with `data/parquet` + `data/raw` symlinked read-only from the canonical checkout; `data/out` is local (gitignored intermediates). The canonical checkout was sitting on Track B's `m5-frontend-chrome` branch — did **not** touch it.

**To merge:** branch `m4a-foundation` → `main`. Touched only `country_ref.py`, `data/ref/baci_country_codes.csv`, `etl/01,02,03b,05`, `_finalization/verify-M4a.command`, README, architecture.html, LOG, 00_INDEX (M4a row only) — no `ui/` overlap with Track B.

**Next:** M3 — the 3 real peer methodologies (now unblocked). Read `modules/M3_methodology.md`.

---

## 2026-06-07 — M2 intent pass ✅ (README rewritten, same session)

**Done**
- Rewrote `README.md` as the **canonical source of truth** (replaced the drifted 24 KB version). Encodes adjudicated drifts + decisions, marks **[current]** vs **[target]** inline, and includes a **data dictionary** for the carry-over fields surfaced in M1.
- Demoted `SPEC.md` to a pointer (content merged into README).
- **Built the label registry** `data/ref/labels.csv` (Jan's ask): one row per concept (signal_type/methodology/map_metric/metric), one column per display surface (section_header/badge/card_title/short/tooltip/full_description/map_title) + status. Documented in README §5 + architecture.html §⑤. Wired: M3 fills methodology descriptors into it; M5 makes the UI consume it (kills the header-vs-badge inconsistency). Generalizes `config.yaml: metric_labels`.
- **New documentation findings folded in** (from the M1 visual audit): signal `type`→Czech-label mapping is internally inconsistent (section header vs badge vocab in `SignalsList.jsx`) + dead label branches; `/insights_data` exposes 7 undocumented fields with 2 bugs (`cz_delta_pct` duplicates `import_yoy_change`; `median_peer_share` 0.0 vs `/top_signals` 0.108 for same key); opaque `intensity`/`value` fields; map-metric→column chain; embedded `methodology` descriptor object; peer-group identity inconsistency between `/top_signals` and `/bars`.

**Remaining M2 (truth pass):** after M4b, strip the [current]/[target] flags so README == running system.

**Next:** M4a — country codes + all-country coverage. Read `modules/M4a_foundation.md`. (Fresh-session candidate.)

---

## 2026-06-07 — M1 boot & baseline ✅ (same session)

**Done**
- Booted locally: API (`.venv` py3.13, `uvicorn api.server_full:app` :8000, deployment-CSV path) + UI (Vite :5173). Both serve real data; all core endpoints smoke-tested OK.
- App renders fully (Czech UI, 3 benchmark categories, bar chart, two-metric map, LLM insight box w/ disclaimer). Screenshots in `screenshots/01-landing.png`, `02-fullpage.png`.
- Added `run-local.command` (double-click boot) + `current-state.md` baseline.

**Baseline findings (logged, not fixed)** — see `current-state.md`: map returns only 72 countries (M4a); benchmark labels (statistický / statistický-současný / geografický) don't map cleanly to the 3 methods (M2/M3); top_signals vs bars peer-group inconsistency (M3); faked medians confirmed live; `.env` live OpenAI key (gitignored, not leaked, rotate as precaution); dist iCloud dup artifacts (M5); map geometry via GitHub raw URL (M5).

**Env notes**
- Use repo `.venv` (py3.13, has deps: fastapi 0.116, pandas 2.3, pyarrow 21). conda env `mapa` is py3.11.
- Chrome MCP extension was offline; preview MCP is rooted at the session cwd (the vault) not the repo → used headless Chrome (`--headless=new --screenshot`) for screenshots. Added `.claude/launch.json` (ui config) in the repo for future preview use.
- Servers may still be running (API :8000, UI :5173) — `run-local.command` frees ports on next boot.

**Next:** M2 — rewrite README as canonical source of truth. Read `modules/M2_spec.md`.

---

## 2026-06-07 — Scaffolding & architecture (planning session)

**Done**
- Full read-only review: 3 subsystem audits (ETL/API/UI) + SWE architecture investigation. Findings in plan + `DRIFT_REGISTER.md`.
- Adjudicated all 16 drifts with Jan.
- Settled the methodology question definitively: `human`=stat×0.85, `opportunity`=stat×1.15, `geographic`=empty stub. Only statistical is real. → build all 3 for real.
- Confirmed serving-layer feasibility: app never reads third-country bilateral trade at runtime (peer bars = CZ→peer exports; benchmark = precomputed median). Raw matrix is droppable. Serving layer ~60–150 MB.
- Built this `_finalization/` scaffold + `architecture.html`.

**Decided**
- Architecture: ETL (heavy, local, ~once/year) → small serving parquet → API reads only that. GitHub Release asset for the artifact.
- Module spine: M1 → M2 → M4a → M3 → M4b → M5 → M6 → M7.
- Scope lock: show today's numbers only (no per-peer market share) → keeps serving layer compact.
- Maps stay dynamic; signals precomputed.
- **Methodology = Option 2 (evolve M3):** keep 3-method structure, drop/rework fragile CAGR-opportunity, add distance/FTA/market-size as filters. Full ITC-style re-foundation deferred to **v2** (`V2_BACKLOG.md`), after officials discussion. Challenge memo saved: `trade-economics-challenge.md`.
- **Descriptors:** all Czech prose, from one shared source; opportunity's name+explanation to be built.
- **Documentation protocol:** `README.md` = single source of truth; `architecture.html` kept in sync; `SPEC.md` demoted to drafting scratchpad (merges into README in M2).

**Peer-group system (recovered for the holistic architecture doc)**
- 3 methods: trade_structure (k-means cosine on HS2 shares, 10 clusters, CZ#4, 📝EN); human/geo (expert-curated, 23 clusters, CZ#3, 📝CZ); opportunity (k-means cosine on HS6+CAGR+openness, 10 clusters, ❌no descriptor).
- Live scripts are converters (explained-CSV → parquet); creation algorithms are archived (`etl/archive/30,31`). Source of truth = `*_explained.csv` (membership + descriptor co-located).
- Legacy `data/ref/peer_groups.json` (V4/Benelux/Nordics/ASEAN…) — placeholder, likely retire.
- Descriptor gaps: opportunity has none; language inconsistent (EN vs CZ); stray numeric codes in trade-structure membership.
- `architecture.html` rebuilt holistic: target on top, peer-group creation §②, full app-consumption block list §③ (incl. the two map logics: share vs absolute), current §④, reference §⑤.

**Open / next**
- **Next session: M1 — boot locally, together.** Read `modules/M1_boot.md`.
- Pre-existing uncommitted UI changes (4 files: App.jsx, useInsights.js, useSignalHandling.js, dist/index.html) are a coherent crash-guard pass — commit during M5 (dist/index.html = stale artifact, discard).
- pyarrow 19.0.0 locally cannot read the old-format deployed parquets ("Repetition level histogram size mismatch") — factor into M1 boot; may need a rebuild or a pinned reader.
- Canonical copy: `/Users/janindracek/Documents/mapa-prilezitosti` (tracks GitHub `main`).
