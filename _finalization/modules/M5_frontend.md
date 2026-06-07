# M5 — Frontend finalization

**State:** ⬜ · **Depends:** M1 (chrome) / M4b (data features) · Read with `../00_INDEX.md`.

## Purpose
Take the UI from working-prototype to ministry-presentable, and add the two new front-end features.

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
