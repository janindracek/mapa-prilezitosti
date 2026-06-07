# M4a — Foundation: country codes + all-country coverage

**State:** ⬜ · **Depends:** M2 (intent) · Read with `../00_INDEX.md`.

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

## Internal steps
*TBD when booted.*
