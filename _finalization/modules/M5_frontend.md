# M5 — Frontend finalization (DATA FEATURES track)

**State:** chrome ✅ done (Track B, 2026-06-07) · **data features ⬜ launched** (this track) · **Depends:** M4b ✅ · Read with `../00_INDEX.md`.

## Launch context (2026-06-09) — read this first
The **chrome** half is already merged (bundled `world.json`, build-on-deploy, ECharts tree-shake, Czech map tooltips, dead-code/console cleanup — see `../LOG.md` 2026-06-07 M5). This track is the **data features**, now unblocked by M4b. What M4b already gives you:
- **`data/serving/signals.parquet`** carries a **`band`** column (`strong` / `weak`) — the two-tier split is in the data; select at request time, no recompute. The API serves the FULL set (~108k signals).
- **`data/ref/labels.csv`** is the canonical string registry (one row per concept, one column per surface; methodology + signal-type rows `status=ok`, opportunity `retired`). M3 filled the Czech methodology descriptors.
- **`data/serving/peer_groups.parquet`** has per-cluster Czech descriptors (name + explanation) for both methods.
- API: `/signals`, `/top_signals`, `/signals/*` read the one serving layer. Request-time strong/weak selection belongs in `api/services/signals_unified.py` (the only API file this track should touch).
- **Boot:** `rebuild-all.command` populates `data/serving/` (gitignored); `run-local.command` boots API:8000 + UI:5173. Repo `.venv` (py3.13). `INSIGHTS_USE_LLM=0` for the deterministic insight fallback.

**Scope boundary vs the parallel M6 session:** M6 owns `api/insights_text.py` + the insight disclaimer banner — **leave those alone.** Stay in `ui/` + `api/services/signals_unified.py`. Shared docs: edit only your own LOG entry / your `00_INDEX` row.

**Jan's explicit ask:** surface the **methodology notes / descriptors prominently in the dashboard** (they now exist — wire them in).

## Purpose
Take the UI from working-prototype to ministry-presentable, and add the two new front-end data features.

## Boundary
- **In:** two-tier signal display (strong vs flagged "permissive" weak); analytics side-tab (filterable table over the full signal set); **consume the label registry** (`data/ref/labels.csv` → generated JSON) instead of hardcoding strings in `SignalsList.jsx`/etc. — this fixes the section-header-vs-badge inconsistency; serve world geometry from the bundled `world.json` (not the GitHub raw URL); ship the build correctly (no blank-page); commit the existing crash-guard edits (discard the stale `dist/index.html`); tree-shake ECharts; Czech country labels/tooltips; remove `SHOW_SKELETON` + commented-out debt; console cleanup.
- **Out:** hosting (M7); insight-box LLM swap (M6).

## Preconditions
- M1 baseline (know current UI state).
- Data-dependent features (two-tier, side-tab) need M4b's full signal set served.

## Dependencies
M1; M4b for the data features. Non-data chrome can start after M1.

## Acceptance gate (Jan-verifiable)
- Clean local `npm run build` with no blank-page; `build-ui.command`.
- Screenshots: two-tier signals, analytics tab, Czech-labelled map.

## Internal steps
*TBD when booted.*
