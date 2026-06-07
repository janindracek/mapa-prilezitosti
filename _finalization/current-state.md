# M1 — Current-state baseline (2026-06-07)

What the app does **today**, booted locally and observed. This is the "before" snapshot we change against. Screenshots in `screenshots/`.

## It boots and runs ✅
- **API:** `.venv` Python 3.13.5, `uvicorn api.server_full:app` on :8000. Comes up clean; serves the **deployment-CSV data path** (`data/deployment/core_trade.csv` present → deployment mode active). `/health` ok.
- **UI:** Vite 5 dev server on :5173 (Node 20). Renders fully.
- **One-command boot:** `run-local.command` (double-clickable) added.
- Endpoints smoke-tested OK: `/controls`, `/top_signals`, `/map_v2`, `/bars?mode=peer_compare`, `/signals/methodologies`.

## What renders (see `screenshots/01-landing.png`, `02-fullpage.png`)
- Title **"Obchodní příležitosti Česka"**, Czech UI throughout.
- **Controls:** country (default Belgie), optional HS6 picker.
- **Signals list**, grouped into Czech categories: **Benchmark (statistický)**, **Benchmark (statistický, pohled současný)**, **Benchmark (geografický)**, plus export-frequency lists.
- **Bar chart:** "Top 10 importérů — HS6 8517.13, 2023".
- **Map** with two-metric toggle: *Český podíl na importu* (share) vs *Celková hodnota exportu* (absolute) — the two map logics, live.
- **Insight box** with the LLM disclaimer banner ("VAROVÁNÍ: obsah vygenerovaný automaticky skrz LLM…"); empty KeyData until a signal is clicked.

## Baseline findings (observe only — fixes belong to later modules)
1. **Map coverage gap (live):** `/map_v2?hs6=851713` returns **72 countries**, not all importers → confirms the all-country fix (M4a).
2. **Benchmark labels don't map cleanly** to {trade_structure, human, opportunity}: UI shows *statistický* / *statistický pohled současný* / *geografický*; no obvious **opportunity** surface, and "pohled současný" is ambiguous. Reconcile in M2/M3.
3. **Peer-group inconsistency (live):** `/top_signals?country=DEU` returns human peers = CEE group (SVK,HUN,CZE,POL,ROU,AUT,SVN), but `/bars?mode=peer_compare&country=DEU&peer_group=human` returns EU-Core-West (NLD,IRL,BEL,LUX,DEU). Conceptual muddle about *whose* peer group is shown → M3.
4. **Faked medians confirmed:** `peer_median`/`delta_vs_peer` present and served, but per `etl/03b` they are statistical×0.85 / ×1.15 / stub → M3.
5. **`.env` holds a live OpenAI key** — gitignored, never committed, NOT leaked publicly; printed to this session only. Rotate as precaution (replaced by Claude in M6 anyway).
6. **dist/ has iCloud duplicate artifacts** (`index-… 2.js`) — cleanup in M5.
7. **Map geometry loads from a GitHub raw URL** — worked here (network available); risk on restricted/ministry networks → M5 (use bundled `world.json`).
8. **pyarrow 21** in `.venv`; runtime uses the CSV path, so the old-parquet read issue isn't hit while serving (only matters for ETL re-runs).

## Verdict
Functionally demo-able as a prototype; not yet ministry-polished. Nothing blocks proceeding. Next module: **M2 — canonical spec (rewrite README as source of truth)**.
