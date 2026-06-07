# M2 — Canonical spec (bracketing)

**State:** ⬜ · **Depends:** M1 · Read with `../00_INDEX.md`.

## Purpose
Rewrite the **canonical `README.md`** as the single source of truth — because the current README is drifted and can't be trusted. `../SPEC.md` is only the drafting scratchpad; its finished content merges into the README, which then governs. Two passes: **spec-of-intent** up front (target contract for the surviving views, signal types, lineage), and **spec-of-truth** after M4b (matches what actually runs).

## Boundary
- **In:** draft in `../SPEC.md`, then merge into `README.md`; for each surviving view state WHY it exists + the exact intended math; define signal types + the two-tier policy; metrics glossary; serving contract; lineage (point to `architecture.html`). Reconcile cosmetic drifts 9–14. Keep `architecture.html` in sync with the README.
- **Out:** no code. The README is the contract code is later tested against.

## Documentation protocol (applies from here on)
When anything changes: **README.md is the version of truth**; update it first, then keep `architecture.html` in sync. No second canonical doc (SPEC.md is draft-only).

## Preconditions
- M1 baseline exists (we know what runs today).
- Drift register adjudicated (done).

## Dependencies
M1. (Spec-of-truth pass also depends on M3 + M4b being decided.)

## Acceptance gate (Jan-verifiable)
- Jan reads the spec-of-intent and confirms the target contract for the three views.
- Final pass: spec matches the running system after M4b.

## Internal steps
*TBD when booted.*
