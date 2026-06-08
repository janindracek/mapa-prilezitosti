# M4a — Foundation: country codes + all-country coverage

**State:** ✅ done (branch `m4a-foundation`) · **Depends:** M2 (intent) · Read with `../00_INDEX.md`.

## Purpose
Fix the data foundations that everything downstream silently needs: a centralized country-code system (nothing dropped), all-country coverage in the core table (so the world map has every importer), and a single dollar-scaling point. Must precede the methodology rebuild — honest peer groups can't be built on broken codes.

## Boundary
- **In:** one country-code module/table as the single source of truth, used everywhere (kills numeric-vs-iso3 mismatch, hardcoded `iso=='203'`, the 10 dropped BACI codes); change stage-01 to OUTER-join so the core table covers all importers; migrate prior-year delta columns into stage 02; delete the duplicate dollar scale in stage 05.
- **Out:** methodology medians (M3); serving layer + path collapse (M4b).

## Preconditions
- M2 spec-of-intent defines the metrics/coverage contract.

## Dependencies
M2.

## Acceptance gate (Jan-verifiable)
- A `.command` showing: all-country coverage (importer count rises from 205 → full universe), dollars scaled in exactly one place, and zero dropped country codes.
- Integrity check (e.g. world total = Σ bilaterals where applicable).

## Internal steps (as executed)
1. **`country_ref.py`** (repo root) + committed `data/ref/baci_country_codes.csv` — single source of truth for BACI numeric ↔ ISO3 ↔ name. No pycountry. Reverse lookups prefer active over historical-twin iso3.
2. **`etl/01`** — codes via `country_ref` (recovers 6 dropped: USA/FRA/NOR/CHE/IND/S19); **OUTER-join** → 226 importers; assertions (zero dropped, coverage==universe, no null iso3, export≤import). Single `TRADE_UNITS_SCALE` stays here.
3. **`etl/02`** — added prior-year/delta columns (`export_cz_to_partner_prev`, `delta_export_abs`, `export_cz_total_for_hs6_prev`).
4. **`etl/05`** — rebased onto `metrics.parquet`; deleted the duplicate `* TRADE_SCALE` and the raw `trade_by_pair` read.
5. **`etl/03b`** — hardcoded `iso=='203'` → `cr.cz_numeric()`; local pycountry impl → `country_ref`. (Faked medians = M3.)
6. **`_finalization/verify-M4a.command`** — double-click acceptance gate (rebuild 01→02→05 + assert). Runs green.

**Acceptance:** ✅ coverage 205→226 · single $-scale point · zero dropped codes · integrity. See `../LOG.md` (2026-06-07 M4a).
