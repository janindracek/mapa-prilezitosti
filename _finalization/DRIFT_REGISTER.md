# Drift Register — README/docs ↔ code

Neutral record of where documentation and code disagreed, with Jan's adjudication. "Verdict" = which side we treat as correct; "Action" = where it's fixed.

Severity: 🔴 correctness · 🟠 behavioral · ⚪ cosmetic.

## A. Substance — what the tool claims to be

| # | Sev | Topic | Doc says | Code does | Verdict (Jan) | Action |
|---|-----|-------|----------|-----------|---------------|--------|
| 1 | 🔴 | Three methodologies | 3 independent peer benchmarks (human/geo, trade-structure, opportunity) | `statistical` real; `human`=stat×0.85 (`03b:187`); `opportunity`=stat×1.15 (`03b:262`); `geographic`=stub (`03b:98`) | **Build all 3 for real.** Fix the qualitative "why these countries are bundled" rationale first. | M4a→M3 |
| 2 | 🟠 | Signal thresholds | Disciplined: `MAX_TOTAL 10`, `S1_REL_GAP_MIN 0.20`, etc. | Loosened to "VERY PERMISSIVE": `MAX_TOTAL 5000`, `0.001`, etc. | **Two-tier.** Strong = disciplined (≤10); if <5 for a country, backfill with flagged "permissive" weak signals. | M4b + M5 |
| 3 | ⚪ | Fixed signal counts | "531/532/2000" per type | Data-dependent caps | **New feature:** expose full set in a filterable analytics side-tab. | M4b + M5 |

## B. Correctness — are the numbers right

| # | Sev | Topic | Doc says | Code does | Verdict (Jan) | Action |
|---|-----|-------|----------|-----------|---------------|--------|
| 4 | 🔴 | Dollar scaling sites | One place (`etl/01`) | Also `etl/05:90` (reads raw, scales again) | **One scale point (stage 01); delete stage-05 scale; fix docs.** | M4a |
| 5 | 🔴 | Map source | Built "from metrics" | Built from raw `trade_by_pair` (for all-country coverage) | **Map from the same core source.** Achieve coverage via stage-01 outer-join, then map = thin slice. | M4a + M4b |
| 6 | 🟠 | "Dynamic" map | Served dynamically | Serves pre-baked CSV | **Keep dynamic — it works** (≤226 rows/view, ms-fast). | M4b |
| 7 | 🔴 | Data path | Clean ETL→parquet→API | 3 inconsistent paths (deployment CSV; dead `api.shapes`; `signals_unified` 2nd source) | **Collapse to one serving layer + one loader.** | M4b + M7 |
| 8 | 🟠 | Country codes | API converts at runtime | ETL never standardizes; hardcoded `iso=='203'`; 10 codes dropped | **Centralized country-code system, used everywhere.** | M4a |

## C. Cosmetic — doc tidiness

| # | Sev | Topic | Note | Verdict | Action |
|---|-----|-------|------|---------|--------|
| 9 | ⚪ | Two pipelines documented (old 03/04/06–08 vs current 03b/04b/06b) | not labelled which is current | Fix later | M2 spec |
| 10 | ⚪ | "Where to tweak" references legacy scripts | stale | Fix later | M2 spec |
| 11 | ⚪ | `intensity` always `abs(delta)` | differentiation is ranking only | Fix later | M2/M3 |
| 12 | ⚪ | `/bars_v2` undocumented; `/bars` mode not type-enforced | leftover | Fix later | M4b |
| 13 | ⚪ | `metric_labels` README subset (6) vs config (11) | stale | Fix later | M2 spec |
| 14 | ⚪ | LLM (OpenAI gpt-4o-mini) runs only in non-deployment path | preview needs no key today | Note for M6 | M6 |

All adjudicated 2026-06-07. Cosmetic items (9–14) are batched into M2/M4b/M5/M6, no standalone work.
