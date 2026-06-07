# Trade-economics challenge — peer-benchmark methodology

> Decision input, 2026-06-07. A trade-economist/export-promotion sub-agent was asked to challenge or verify the three-method peer-group design. Verdict drove the **Option 2 (evolve M3)** decision; the full re-foundation is logged for **v2** (`V2_BACKLOG.md`), to revisit after the officials discussion. Memo preserved verbatim.

---

## 1. Is "comparable import markets" the right axis? No — it has a structural flaw.

The tool's logic is: *"In markets like this one, Czechia captures X% of imports; here only Y%; the gap = opportunity."* This conflates two things that must be kept separate: **where Czech share is low** and **where Czech share is winnable.** It treats Czechia's own realized share elsewhere as the counterfactual ceiling. That embeds a hidden, usually false, assumption: that the only reason Czechia's share differs across "similar import markets" is under-exploited effort — rather than tariffs, distance, FTAs, incumbent suppliers, or standards. A low share in a distant, high-tariff market with an entrenched regional supplier is not an "opportunity"; it's a structural ceiling. The benchmark will systematically flag the hardest markets as the biggest prizes, because that's where the gap is largest — and largest *for reasons the model can't see.*

The deeper issue: the peer group is built on the **target market's** characteristics (its import mix, geography, growth), but the gap being explained is a property of the **bilateral relationship** (Czechia→market). You cannot benchmark a bilateral quantity using a unilateral grouping. Two markets with identical import baskets can have wildly different *achievable* Czech share because one is in the single market 200 km away and one is across an ocean behind a tariff wall.

**The competitor-exporter framing is closer to right, but also incomplete.** "What share do Czechia-like exporters (Slovakia, Hungary, Austria, Slovenia) win in this market?" is a better counterfactual than "what does Czechia win in similar markets," because peer exporters face roughly the same distance/tariff/capability constraints Czechia does. If Slovakia and Austria each hold 6% of Market Z's imports of HS6 X and Czechia holds 1%, that 5-point gap is far more credibly *winnable* than a gap derived from Czechia's share in some structurally-different third market. It controls for the supply side, which the current design ignores entirely.

**But the genuinely right answer is neither single axis — it's the ITC decomposition:** potential exports = Czech *supply capacity* × target *demand* × *ease of trade* (tariffs, FTA, distance, bilateral frictions). The current tool captures a noisy proxy for demand and nothing else. A peer-exporter benchmark at least proxies supply + ease-of-trade jointly (because peers share them). So the competitor-exporter framing beats the current import-market framing for the stated question; best of all is to drop "median peer share" as the organizing primitive and adopt supply×demand×access, with peer-share as a sanity check only.

## 2. Each method on its own terms

**A. Trade-structure / k-means on HS2 import mix.** Right: groups by *what a market buys* — a real demand-side signal. Misleads: import-mix shape is largely a function of development level and structure, not accessibility; it places Czechia next to advanced Asia and distant high-income markets it cannot serve at the same intensity (distance, no single-market access). Compositional clustering normalizes away absolute size, treating a tiny and a huge market with the same basket as equivalent peers. Failure mode: large, flattering gaps in unwinnable markets.

**B. Geographic / hand-curated 23 clusters.** Right: perversely the *least wrong* here, because region + development level proxies the two things that matter and the others miss — distance/ease-of-trade and income/demand level. CEE peers share FTA status, EU membership, distance band, standards regime. Misleads: static, encodes curator priors, no product dimension (same 23 clusters for every HS6 — relevant peers for glassware ≠ pharma), and "CEE" can lump Czechia with markets it dominates (drags the median down) or much poorer markets. Failure mode: bias laundered as expertise; product-blind grouping.

**C. Opportunity / k-means on HS6 shares + CAGR + openness.** Most wrong for prioritization. CAGR over 2022–2023 is two data points — not a growth rate, a difference — and at HS6 single-market level it's dominated by noise, base effects, one-off shipments. Clustering on growth selects for *volatility*: highest-CAGR markets are disproportionately small markets where a single contract doubles imports. Mixing levels (shares), a rate (CAGR) and a ratio (openness) into one cosine k-means without principled scaling means whichever feature has the largest variance dominates the distance metric — cluster structure becomes a preprocessing artifact. Failure mode: directs scarce promotion budget toward small, volatile, possibly-saturated markets, branded as "AI opportunity."

## 3. Three methods — triangulation or three-flavored wrong?

Triangulation works only when methods are **independent estimators of the same quantity with uncorrelated errors.** These aren't: all three estimate the same flawed quantity (peer-median import share) and share the same blind spots (no tariffs, distance, FTA, supply, competitive intensity). Three views blind to the same four variables don't triangulate; they agree for the wrong reasons or disagree unexaminably. Disagreement gives the ministry user no principled way to adjudicate — decision paralysis dressed as optionality. A serious agency (ITC EPM) presents **one defensible model** (supply × demand × ease-of-trade) **with filters and adjustable assumptions** and component transparency — not three competing definitions of "peer." Multiplicity belongs in filters/scenarios, not in the definition of the benchmark.

## 4. What's missing (load-bearing variables, none captured)

- **Tariffs and FTAs / preferential access** — biggest determinant of winnable share for an EU exporter; absent.
- **Distance / gravity** — most robust regularity in trade economics; ignoring it overstates far-market opportunity.
- **Absolute market size** — proportional clustering discards it; 5 points of €10bn ≠ 5 points of €10m. Opportunity must be value-weighted.
- **Competitive intensity / incumbents** — is the gap open space or owned by Germany/China?
- **Czech RCA / supply capacity** — can Czechia actually supply HS6 X at scale? No supply side at all.
- **Standards / NTMs / regulatory regime** — often the real barrier for CEE exporters.
- **Peer-EXPORTER benchmark** — the missing controlled counterfactual.

## 5. Verdict and recommendation

**Re-found the benchmark; don't keep tuning three peer definitions.** The organizing primitive — "median Czech share across similar import markets" — is the wrong primitive, and no clustering fixes a benchmark blind to tariffs, distance, FTA, supply.

1. Replace the three-method core with one ITC-style decomposition: Opportunity(product, market) = Czech supply signal (RCA / export capacity) × market demand (absolute import value + credible multi-year growth, not 2-point CAGR) × ease-of-trade (tariff/FTA/distance). Buildable from BACI + a tariff/FTA join + a CEPII distance file.
2. Demote peer-share to one sanity-check lens, and make it a peer-EXPORTER benchmark. Keep geographic grouping as the *control* (proxies access); drop import-mix and opportunity clusterings.
3. Move all multiplicity into filters/scenarios, not competing definitions of "comparable."
4. If forced to keep multiple lenses, keep two at most: gravity/access-aware model (primary) + geographic peer-exporter check (secondary). Kill CAGR-opportunity clustering outright.

---

- **(a) Strongest FOR the current 3-method design:** it makes the contestable choice of "comparable" explicit; a gap that survives all three lenses is more credible than one in only one.
- **(b) Strongest AGAINST:** all three estimate the same flawed quantity and share the same blind spots, so they cannot triangulate — they will systematically flag structurally-unwinnable markets as the biggest prizes, with no principled way to adjudicate disagreement.
- **(c) One-line recommendation:** Replace the three peer-clustering methods with a single ITC-style supply × demand × ease-of-trade model, keep one geographic peer-*exporter* benchmark as a sanity check, and push all remaining variety into filters.

**Sources:** ITC Export Potential Map methodology (EPA) · ITC Export Potential Map (exportpotential.intracen.org) · World Bank — Gravity Model–Based Export Potential · OEC — Rethinking Export Potential.

---

## What we decided (Jan, 2026-06-07)

- **Now (M3, Option 2):** keep the three-method structure but (1) **drop/rework the CAGR-opportunity method** (the most statistically fragile), and (2) add the cheapest missing access variables — **distance, FTA/tariff flag, absolute market-size weighting — as filters** on top, not as new "peer" definitions.
- **v2 (after officials discussion):** the full re-foundation (ITC supply×demand×ease-of-trade + geographic peer-*exporter* sanity check). Logged in `V2_BACKLOG.md`.
