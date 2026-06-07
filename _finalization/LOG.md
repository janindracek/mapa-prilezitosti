# LOG — decisions & session handoff

Newest first. One entry per working session: what changed, what was decided, what the next session should pick up.

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
