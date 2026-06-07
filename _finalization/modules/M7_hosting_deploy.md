# M7 — Hosting & deploy

**State:** ⬜ last · **Depends:** M3, M4b, M5, M6 · Read with `../00_INDEX.md`.

## Purpose
Put it online as a clickable preview the ministry can use, without foreclosing the full any-product × any-country version.

## Boundary
- **In:** pin a working pyarrow wheel (Python 3.12); package the serving layer as a GitHub Release asset; make `build.sh` download it; deploy with one code path (no CSV fallback); decide hosting tier given the ~60–150 MB serving layer (free 512 MB tier is tight; 1 GB tier comfortable) and the frontend/backend split (JS-native host for the SPA vs server for the API); smoke-test; write a redeploy runbook + the annual-refresh procedure.
- **Out:** any further feature work.

## Preconditions
- M3 (real methods), M4b (serving layer + one source), M5 (shippable build), M6 (insight box decided).

## Dependencies
M3, M4b, M5, M6.

## Acceptance gate (Jan-verifiable)
- A live URL the ministry can click and navigate.
- A smoke-test checklist passing; a redeploy + annual-refresh runbook.

## Open decision (carry from plan)
Hosting substrate must preserve the full-DB path. Candidates: finish FastAPI (split or single service) · DuckDB-WASM in-browser over a hosted parquet · hybrid preview→full. Decide here, with data.

## Internal steps
*TBD when booted.*
