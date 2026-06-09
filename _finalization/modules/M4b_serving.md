# M4b — Serving layer + path unification

**State:** ✅ done (branch `m4b-serving`, 2026-06-09) · **Depends:** M3 · Read with `../00_INDEX.md`.

> **Outcome:** ONE serving layer `data/serving/` (`core_trade`, `signals` [full+banded], `peer_groups`, `hs6_names`, `countries`) built by `etl/07_build_serving.py`; `rebuild-all.command` runs raw→serving with a serving==ETL integrity report. API collapsed to one loader (`api/data/serving.py` + settings) — deleted the `data/deployment` CSV branch, dead `api.shapes`, `/signals_unified`, `/bars_v2`, and `data/deployment/` itself. `/map_v2` now serves all 226 importers. Fixed: `import_partner_total_x/_y` collision, `cz_delta_pct` dup, `median_peer_share` 0.0, `_fmt_usd` ×1000, NaN-500s. Disciplined signal floors restored; full banded set served (strong/weak tier at request time = M5). Boot-tested: every endpoint 200. Full write-up in `../LOG.md` (2026-06-09).

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
