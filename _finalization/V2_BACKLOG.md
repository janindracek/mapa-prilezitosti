# v2 backlog — revisit after the officials discussion

Items deliberately deferred past the first shippable version. Decided with Jan; rationale in `trade-economics-challenge.md`.

## V2-1 — Re-found the opportunity benchmark (ITC-style)
**Why deferred:** the trade-economist challenge argues the core primitive ("median Czech share across similar import markets") is structurally flawed — it benchmarks a *bilateral* quantity with a *unilateral* grouping and is blind to tariffs, distance, FTAs, supply capacity, and competitive intensity. The right destination is the field-standard model, but it's a bigger scope change needing extra data and is better decided once officials have seen the tool run and reacted.

**What v2 would do:**
- Replace the peer-median core with **Opportunity = Czech supply (RCA / export capacity) × market demand (absolute import value + credible multi-year growth) × ease-of-trade (tariff/FTA/distance)** — ITC Export Potential Map decomposition.
- Demote peer-share to a single sanity-check lens, reframed as a **peer-EXPORTER** benchmark ("Slovakia/Austria win 6% here, Czechia 1%") — controls for shared access constraints.
- Keep the geographic grouping as the *control* (it proxies access); push all other variety into **filters**, not competing peer definitions.
- New data joins required: a tariff/FTA table, a CEPII distance file, a multi-year import series (more than 2022–2023).

**Trigger to pick this up:** after the ministry/officials discussion of the v1 tool.

## Parking lot (smaller v2 candidates)
- Multi-year data (beyond 2022–2023) so growth is a real trend, not a 2-point difference.
- Product-specific peer groups (today the geographic 23 clusters are the same for every HS6).
- Competitive-intensity / incumbent-share signal per (hs6, market).
