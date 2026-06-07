# M6 — Insights re-engineering (OpenAI → Claude)

**State:** ⬜ deferred (Jan's call, pre-deploy) · **Depends:** M2 · Read with `../00_INDEX.md`.

## Purpose
Re-engineer the AI-generated insight text box. Currently runs on OpenAI `gpt-4o-mini` (only in the non-deployment path; the live preview serves a deterministic template). Jan wants to move it to Claude — to be decided and built right before deploy.

## Boundary
- **In:** decide live-LLM-on-Claude vs precompute-offline (dataset is frozen → precompute keeps it instant + no live key); implement the chosen path; fix the Czech LLM-disclaimer banner; handle key/secrets cleanly for a public preview.
- **Out:** the analytics/signal data work (M4b).

## Preconditions
- M2 spec (what the insight box should say).
- Decision taken with Jan (this is an explicit discussion point).

## Dependencies
M2. Sequenced just before M7.

## Acceptance gate (Jan-verifiable)
- Decision recorded in `../LOG.md`; implemented; disclaimer banner correct; preview needs no exposed secret (or one handled safely).

## Internal steps
*TBD when booted.*
