# Finalization — Master Index

> **The spine.** This file + one `modules/MX.md` is everything a fresh session needs to work a module. Read both, ignore the rest.

Project: `mapa-prilezitosti` — trade-opportunity dashboard for the Czech Ministry of Industry (Python ETL → FastAPI → React/ECharts).
Goal: finish it, fix the faked methodologies, collapse the data architecture to one clean source, ship a clickable online preview that preserves the full any-product × any-country version.

Plan of record: `~/.claude/plans/so-of-course-this-mossy-lecun.md` (approved). This scaffold operationalizes it.

---

## How to work this project (bootability contract)

1. Open this file + the target `modules/MX.md`.
2. Check **Status board** (below) — confirm the module's dependencies are ✅ done.
3. The module brief gives Purpose · Boundary · Preconditions · Dependencies · Acceptance. **Internals are filled in just-in-time when the module is booted** (Jan reviews before execution).
4. On finishing: update the Status board here, append a dated entry to `LOG.md`, and tick the module's acceptance gate.

Each module is sized to fit one focused session. Do not chain modules in a single session without Jan's go.

---

## Status board

| Module | Title | State | Depends on | Acceptance gate |
|--------|-------|-------|-----------|-----------------|
| M1 | Boot & baseline | ✅ done | — | `run-local.command` boots + screenshots in `screenshots/`; baseline in `current-state.md` |
| M2 | Canonical spec (bracketing) | 🔄 intent pass done | M1 | README rewritten as SoT (intent); truth pass after M4b removes [current]/[target] flags |
| M4a | Foundation: country codes + all-country coverage | ✅ done (Track A, branch `m4a-foundation`) | M2 (intent) | ✅ `verify-M4a.command` green: coverage 205→226, single $-scale point, zero dropped codes, integrity |
| M3 | Methodology rebuild (real methods) | ✅ done (branch `m3-methodology`) | M4a | ✅ `verify-M3.command` green: 2 real distinct methods (top-3 product overlap ≈0.05 Jaccard), real medians (recompute-verified), opportunity retired→v2, Czech descriptors. Access filters deferred (design pass) |
| M4b | Serving layer + path unification | ✅ done (branch `m4b-serving`) | M3 | ✅ `rebuild-all.command` green (9/9 serving==ETL checks); API boots on `data/serving/` only, every endpoint 200, `/map_v2`=226; 3 dead paths + `data/deployment/` deleted |
| M5 | Frontend finalization | 🔄 chrome ✅ done (Track B, branch `m5-frontend-chrome`: bundled world.json, build-on-deploy, ECharts tree-shake, Czech tooltips, dead-code/console cleanup) · data features wait for M4b | M1 (data features after M4b) | clean build + screenshots + `build-ui.command` ✅ |
| M6 | Insights re-engineering (OpenAI→Claude) | ⬜ deferred | M2; pre-deploy | decision + impl + banner correct |
| M7 | Hosting & deploy | ⬜ last | M3, M4b, M5, M6 | live URL + smoke-test + redeploy runbook |

State legend: ⬜ not started · 🔄 in progress · ✅ done · ⏸ blocked.

**Sequence:** M1 → M2 → M4a → M3 → M4b → M5 → M6 → M7. (M5 frontend chrome can run in parallel after M1; its data-dependent features wait for M4b.)

---

## Dependency graph

```
M1 ──▶ M2 ──▶ M4a ──▶ M3 ──▶ M4b ──▶ M5 ──▶ M6 ──▶ M7
                                       ▲
        (M5 non-data chrome can start after M1) ─┘
```

Why this order: country codes + all-country coverage (M4a) must precede the methodology rebuild (M3) — you cannot define honest peer groups on broken codes. The serving layer (M4b) must follow M3 because it serves the real methodologies' output.

---

## Key decisions (full rationale in plan + `LOG.md`)

- **One serving layer.** ETL (heavy, local, ~once/year) → small `data/serving/*.parquet` (~60–150 MB) → API reads only that. Drop the raw matrix; it's an ETL input, not a serving need.
- **Build the methodologies for real — Option 2 (evolve).** Replace the fakes (`human`=stat×0.85, `opportunity`=stat×1.15, `geographic`=stub) with real medians; **drop/rework the fragile CAGR-opportunity method**; add distance/FTA/market-size as **filters**. All descriptors → Czech prose, from one shared source (opportunity gets built). Full benchmark re-foundation = **v2** (`V2_BACKLOG.md`), after officials discussion. Rationale: `trade-economics-challenge.md`.
- **Two-tier signals.** Strong (disciplined thresholds, ≤10); if <5, backfill with flagged "permissive" weak signals. Selection at request time.
- **Analytics side-tab.** Expose the full signal set as a filterable table.
- **Dynamic maps, precomputed signals.** Maps computed on request (ms-fast); no map cache.
- **Scope lock:** show the numbers shown today (CZ→peer + precomputed median). NOT each peer's own market share (keeps serving layer compact; revisit only if a methodology demands it).

---

## Documentation protocol (NON-NEGOTIABLE)

**`README.md` (repo root) is the single source of truth.** When anything changes: update the README first, then keep `architecture.html` in sync as its visual companion. There is no second canonical prose doc — `_finalization/SPEC.md` is a *drafting scratchpad only* (its content merges into the README in M2, after which the README governs). This rule exists to prevent the exact doc↔code drift this project is cleaning up.

## Artifacts in this folder

- `architecture.html` — holistic architecture (Target · Peer-group creation · App consumption · Current · Reference). Open in Chrome. Kept in sync with the README.
- `DRIFT_REGISTER.md` — 16 doc↔code drifts with Jan's adjudications.
- `trade-economics-challenge.md` — the methodology challenge memo (drove Option 2).
- `V2_BACKLOG.md` — deferred items (benchmark re-foundation), revisit after officials discussion.
- `SPEC.md` — **working draft only** (merges into README in M2). Not a source of truth.
- `LOG.md` — running decisions + per-session handoff notes.
- `modules/` — the seven module briefs.
