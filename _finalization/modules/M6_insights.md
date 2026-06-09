# M6 — Insights re-engineering (OpenAI → Claude)

**State:** ⬜ launched (this track, 2026-06-09) · **Depends:** M2 ✅ · Read with `../00_INDEX.md`.

## Launch context (2026-06-09) — read this first
After M4b, `/insights` reads the single serving layer (`settings.METRICS_PARQUET_PATH` = `data/serving/core_trade.parquet`). The current code (`api/insights_text.py`):
- builds a Czech prompt in `_build_prompt_for_llm` and calls **OpenAI** `gpt-4o-mini` via stdlib `urllib` in `_llm_generate`, gated by `INSIGHTS_USE_LLM` (default on);
- falls back to a deterministic Czech template (`generate_insights`) when no key / call fails;
- **M4b already fixed** the `_fmt_usd` ×1000 unit bug — values are USD; don't reintroduce scaling.

**Recommended approach (Claude — my rec, confirm in design):** **live Claude call per request, with the deterministic fallback kept.** Rationale: the any-product×any-country space is ~5,609 HS6 × 226 markets ≈ 1.3M combos, so full ETL precompute is impractical; a live call matches the current per-request architecture and the dataset-frozen concern is covered by caching. *Optional optimization:* precompute insights only for the **surfaced** signals (the ~10/country shown) into the serving layer, live-call for arbitrary drill-downs — a hybrid, only if latency/cost demands it. Use the **`claude-api` skill** for current model ids / SDK usage (don't hardcode from memory); replace the `urllib`→OpenAI block with the Anthropic API; key via env (`ANTHROPIC_API_KEY`), handled safely for a public preview (server-side only, never shipped to the client).

**Scope boundary vs the parallel M5 session:** you own `api/insights_text.py`, any new `etl/` precompute stage, env/secrets, and the insight **disclaimer banner** (the one `ui/` component — touch only that). M5 owns the rest of `ui/` + `api/services/signals_unified.py` — leave those alone. Shared docs: edit only your own LOG entry / your `00_INDEX` row.

**Boot:** `rebuild-all.command` populates `data/serving/`; `run-local.command` boots API:8000 + UI:5173. Repo `.venv` (py3.13).

## Purpose
Re-engineer the AI-generated insight text box. Currently runs on OpenAI `gpt-4o-mini`; the live preview serves a deterministic template. Move it to Claude.

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
