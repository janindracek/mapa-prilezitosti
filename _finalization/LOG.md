# LOG — decisions & session handoff

Newest first. One entry per working session: what changed, what was decided, what the next session should pick up.

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
