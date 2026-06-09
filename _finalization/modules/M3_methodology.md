# M3 — Methodology rebuild (real methods)

**State:** ✅ done (branch `m3-methodology`, 2026-06-08) · **Depends:** M4a · Read with `../00_INDEX.md`.

> **Outcome (v1):** shipped **2** real, distinct peer methods — `trade_structure` + `human`. `opportunity` **retired** (2-point CAGR fragile) → v2. Real leave-one-out cluster medians replace the 0.85/1.15 fakes; both descriptors Czech in `labels.csv`. The two methods recommend genuinely different products per country (top-3 overlap ≈ 0.05 Jaccard). Acceptance: `../verify-M3.command`. **Access filters deferred** to a dedicated design pass (Jan); threshold discipline → M4b. Full write-up in README §3/§4 + `../LOG.md` (2026-06-08).

## Purpose
Replace the faked methodologies with three genuinely distinct, defensible peer benchmarks. Today: `human`=statistical×0.85, `opportunity`=statistical×1.15, `geographic`=empty stub. Build geographic from scratch; compute human and opportunity medians for real.

## The three methods (recovered)
- **Trade-structure** (`trade_structure`): k-means cosine on HS2 import-share profiles, 10 clusters; CZ in #4. Descriptor: name + EN prose (in `peer_groups_hs2_explained.csv`).
- **Geographic/human** (`human`): expert hand-curation, 23 clusters; CZ in #3. Descriptor: name + CZ prose (in `peer_groups_human_explained.csv`).
- **Opportunity** (`opportunity`): k-means cosine on HS6 shares + CAGR + openness, 10 clusters. **No descriptor.**
- Creation algorithms are archived (`etl/archive/30_build_peer_groups.py`, `31_...opportunity.py`); only converters are live. Legacy `data/ref/peer_groups.json` (V4/Benelux/…) likely to retire.

## Descriptor requirement (Jan)
The SAME source that defines group membership must produce the app descriptor (the `*_explained.csv` pattern). All three methods need a name + explanation. Fix: **build opportunity's name+explanation; ALL descriptors in Czech prose** (translate trade-structure EN→CZ; human already CZ); remove stray numeric codes from trade-structure membership.
The finished descriptors populate the **label registry** `data/ref/labels.csv` (the `methodology` rows' `full_description`/`short_label` cells; flip their `status` todo/review → ok).

## Evolution decision (Jan — Option 2, 2026-06-07)
Keep the three-method structure, but evolve it per the trade-economics challenge (`../trade-economics-challenge.md`):
- **Drop/rework the CAGR-opportunity method** — the most statistically fragile (2-point CAGR = noise; mixed-scale k-means). Either replace its growth feature with something defensible or retire it for v1.
- **Add the cheapest missing access variables as FILTERS** (not as new peer definitions): distance/gravity, FTA-or-tariff flag, absolute market-size weighting.
- **Full re-foundation (ITC supply×demand×ease-of-trade) is v2** — see `../V2_BACKLOG.md`, revisit after the officials discussion.

## Boundary
- **In:** for each surviving method, (1) define/recover the peer-group *membership* rationale + Czech-prose descriptor from one shared source; (2) compute the real peer median (median of peers' import shares) over the full BACI; (3) delete the 0.85/1.15 constants and the stub; (4) rework/retire CAGR-opportunity + add access filters (above); (5) write each view's WHY + exact math into the canonical **README** (drafted via `../SPEC.md`).
- **Out:** serving-layer packaging (M4b); UI display (M5). **Scope lock:** show today's numbers (CZ→peer + precomputed median); do NOT add per-peer own-market-share unless a method demands it (flag if so — keeps serving layer bounded).

## Preconditions
- M4a done: central country codes + all-country coverage (medians need clean peer membership + full coverage).

## Dependencies
M4a. (Feeds M4b and the M2 spec-of-truth pass.)

## Acceptance gate (Jan-verifiable)
- A before/after table proving the three methods now recommend genuinely different, defensible products for the same country (real differentiation, not a ±15% shift).
- Per-view validation `.command` + the three views written up in `../SPEC.md`.

## Internal steps
*TBD when booted.*
