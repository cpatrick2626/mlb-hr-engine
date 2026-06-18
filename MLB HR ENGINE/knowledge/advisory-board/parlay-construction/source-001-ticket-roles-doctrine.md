---
seat: parlay-construction
source_id: "001"
title: Ticket Roles Doctrine
source_type: internal-doctrine
source_file: "wiki/doctrine/ticket-roles.md"
date_ingested: 2026-06-17
key_people: "--"
status: ingested
---

## Summary

Internal doctrine defining four batter usage archetypes (PRIME / EXPLOSIVE / ADVANTAGE / WILDCARD) that describe HOW to use a player on a ticket. Roles are derived from existing row fields — no new data fetched, no model recomputation. Additive and display-only; they never modify `model_prob`, `model_tier_rank`, or `jigScore`.

---

## Key Concepts

| Concept | Notes |
|---------|-------|
| PRIME (green) | Anchor play. Gates: APEX/ELITE tier + barrel ≥ 9 + xSLG ≥ 0.500 + HH ≥ 45 + EV ≥ 90. Use as ticket spine. |
| EXPLOSIVE (orange) | Ceiling / slate-breaking upside. Gates: maxEV ≥ 113 + barrel ≥ 8.5 + ≥1 of {blast ≥ 12, pullair ≥ 20}. Null trait = not counted, not disqualifying. |
| ADVANTAGE (blue) | Underpriced quality — model grades player above rank. Gates: NOT APEX/ELITE + (xSLG ≥ 0.490 OR barrel ≥ 9.0). Threshold recalibrated 2026-06-15. |
| WILDCARD (purple) | Chaos upside — lower-tier player with one elite tool. Gates: NOT APEX/ELITE + ≥1 of {maxEV ≥ 116, barrel ≥ 12, xSLG ≥ 0.520, pullair ≥ 30}. Trait-count cap removed 2026-06-15 (bug fix). |
| Roles vs Tiers | Tiers = model probability strength (APEX/ELITE/EDGE/…). Roles = ticket usage intent. Separate systems, never merged. |
| Non-exclusive | Player can hold multiple roles simultaneously. |
| Market-free | No odds, EV, or edge data influence role assignment. |

---

## Decision Principles for Parlay Construction

1. **PRIME = anchor.** If ticket has a spine pick, it should be PRIME-qualified. Survives every quality test simultaneously (not just one gate).
2. **EXPLOSIVE = leverage / differentiation.** Use when you want ceiling upside that can separate a ticket from the field. Best in GPP-style construction, not as the only leg.
3. **ADVANTAGE = correlation target.** Underpriced relative to rank → good correlation candidate alongside a PRIME anchor. More available legs than PRIME, less strict gate.
4. **WILDCARD = small allocation.** Single-elite-tool profile = high variance. Cap exposure. Pair with stable legs, not other WILDCARDs.
5. **Role filter uses AND logic on boards.** Multi-role filter = player must hold ALL selected roles. Construction implication: filtering PRIME + EXPLOSIVE gives only players who are both anchors AND ceiling plays.
6. **Roles cannot contaminate scoring.** Role assignment is post-model. Never back-derive model preference from role presence.

---

## Direct Relevance to Parlay Construction Seat

- Provides the operator-facing taxonomy for which legs belong where on a ticket.
- PRIME/EXPLOSIVE/ADVANTAGE/WILDCARD maps naturally to construction roles: anchor → leverage → value → chaos.
- Non-exclusive nature means a single player can serve multiple ticket functions (e.g., PRIME + EXPLOSIVE = safe ceiling play).
- Thresholds are maintained in `config.py` — construction rules must always verify gate values there, not here.

---

## Data Gaps / Deferred

| Topic | Status |
|-------|--------|
| Kelly stake sizing per role | DATA GAP — needs /web-scraping session |
| Correlation between role pairings (e.g., PRIME+EXPLOSIVE same game) | DATA GAP |
| Devig / no-vig pricing integration with roles | DATA GAP |
| Leg-count compounding math | DATA GAP |

---

## Takeaways

- Roles are the engine's construction vocabulary. Learn the gates; they directly answer "which player goes in what position on a ticket."
- PRIME is the strictest gate (5 simultaneous conditions). WILDCARD is the loosest (1-of-4 elite tool). Construction discipline = don't over-index WILDCARD.
- All thresholds are live in `config.py`. This note reflects 2026-06-15 production state; verify before acting.

---

## Related Wikilinks

- [[ticket-roles]] — source doctrine page
- [[tier-vocabulary]] — APEX/ELITE/EDGE/… tier definitions
- [[main-jig-separation]] — roles display both boards, must not contaminate scoring
- [[known-gaps]] — role calibration latent gaps
- [[feature-backlog]] — future role expansion items
