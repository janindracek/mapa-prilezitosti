# M4b — Serving layer + path unification

**State:** ⬜ · **Depends:** M3 · Read with `../00_INDEX.md`.

## Purpose
Make the architecture single-source. Add a final ETL stage that emits a compact serving layer; make the API read only that, through one loader; unify the map to the core source; serve the full (un-capped) signal set; make the whole pipeline reproducible.

## Boundary
- **In:** new final ETL stage → `data/serving/*.parquet` (core_trade all-country/both-years, signals FULL, peer_relationships, metadata, all HS6 + country names); collapse the 3 serving paths to one loader (delete deployment-CSV branch, dead `api.shapes`, `/signals_unified` second source); map = slice of the one core table; orchestration `rebuild-all.command` (raw→serving) with loud assertions; serving==ETL invariant; fix the `import_partner_total_x/_y` collision.
- **Out:** the strong/weak request-time tiering lives in the API service layer (pairs with M5); hosting/Release-asset packaging (M7).

## Preconditions
- M3 done (real methodologies to serve).
- M4a done (clean codes + coverage).

## Dependencies
M3, M4a.

## Acceptance gate (Jan-verifiable)
- One `rebuild-all.command` runs raw→serving end-to-end with assertions that fail loudly.
- Every endpoint reads one source; an integrity report shows serving == ETL output and full signal set present.

## Internal steps
*TBD when booted.*
