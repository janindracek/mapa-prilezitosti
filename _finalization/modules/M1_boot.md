# M1 — Boot & baseline

**State:** ⬜ next (do together) · **Depends:** — · Read with `../00_INDEX.md`.

## Purpose
Get the app running locally exactly as it stands today, click through every view, and capture an honest baseline (screenshots + one-page current-state) before we change anything. This is the first quality gate — Jan sees it run.

## Boundary
- **In:** boot ETL/API/UI locally; produce `run-local.command`; screenshot every view; write a one-page "current state" (what works, what's broken, what's empty).
- **Out:** NO fixes, NO refactors, NO methodology/data changes. Observe only. (Defensive UI crash-guards already uncommitted — leave them; they're an M5 item.)

## Preconditions
- Canonical repo `/Users/janindracek/Documents/mapa-prilezitosti` on `main`.
- Python env + node available.

## Dependencies
None.

## Acceptance gate (Jan-verifiable)
1. A `run-local.command` (double-clickable) that boots API + UI reliably.
2. A screenshot set: map, product bars, signals list, signal-click detail, insight box, each peer methodology.
3. A one-page `current-state.md` baseline.

## Known hazards (from review — confirm during boot)
- The live map runs through the deployment CSV loader; `data/out/ui_shapes/map_rows.parquet` does not exist.
- Local `pyarrow 19.0.0` may fail to read old-format deployed parquets ("Repetition level histogram size mismatch") — the running app may depend on the CSV path; note what actually loads.
- UI fetches world geometry from a raw GitHub URL — may need network.

## Internal steps
*TBD when booted (do together with Jan).*
