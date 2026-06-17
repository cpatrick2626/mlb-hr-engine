---
seat: mlb-scouting
source_id: "001"
title: Pitch Mix Analysis and JIG Tactical Doctrine
source_type: internal-doctrine
source_file: "wiki/doctrine/design-pitch-mix-analysis.md, wiki/doctrine/jig-tactical-doctrine.md"
date_ingested: 2026-06-17
key_people: "--"
status: ingested
---

## Summary

Two internal doctrine files define the scouting-side intelligence layer: the Pitch Mix modal design doc (history of real-data wiring, display-only architecture, data-integrity rules for pitch arsenal) and the JIG Tactical Doctrine (arsenal hunting, HVY pitch-mix signal, handedness edges, HR environment targeting, aggressive filter philosophy). Together they describe how matchup-reading works in this engine — what signals exist, how they are isolated from model probability, and the operator workflow for exploiting them.

---

## Key Concepts

| Concept | Notes |
|---------|-------|
| HVY pitch-mix signal | JIG's flagship signal. Identifies when a pitcher's heavy usage of a specific pitch type creates exploitable matchup conditions for a batter profile. Display-only on JIG — never folded into MAIN model probability. |
| Arsenal hunting | Evaluation of pitcher's full pitch repertoire against batter's known vulnerabilities. Slot-specific (evaluate each pitch type separately), not aggregate. |
| Handedness edges | Platoon split (×0.90–1.12) is one of the most consistently predictive multipliers. JIG weights it explicitly in pick selection, not just as a post-processing multiplier. |
| HR environment targeting | Park factor, wind, temperature, and game-time conditions weighted explicitly in JIG pick selection — not just as λ multipliers. |
| Aggressive JIG filtering | JIG filters are deliberately more aggressive than MAIN. Narrower pool by design; matchup quality thresholds are stricter. |
| Pitch Mix modal (real data post-2026-06-15) | Before 2026-06-15 the entire pitch mix modal was fabricated via seeded RNG. Now wired to real data: pitcher stats from MLB Stats API, arsenal/batter-vs-pitch-type from `/api/pitcher-detail` endpoint. |
| Display-only architecture | No pitch mix modal field influences `model_prob`, `model_tier_rank`, `jigScore`, or role flags. Modal is display; pipeline is scoring. |
| Graceful fallback | Missing pitch-mix data shows `--`. Data is never fabricated as a fallback. The 3×3 zone grid was removed entirely (no free real-time source) rather than retained as fabrication. |
| Operator workflow | MATCHUP → CONFIRM → EXPLOIT. Structured sequence prevents premature exploitation of unconfirmed signals. |

---

## Decision Principles for MLB Scouting

1. **Arsenal hunting is slot-specific, not aggregate.** A pitcher's overall "stuff" rating is not the signal. Evaluate each pitch type individually: does this specific pitch, at this usage rate, match a known vulnerability in this batter's profile? A pitcher with mediocre aggregate stats may be highly exploitable on one pitch slot.
2. **HVY signal is display context, never a scoring input.** When HVY fires, it tells the operator WHERE the exploitation opportunity is. It does not adjust the model probability and should not be used to override or rerank MAIN output. The discipline is: HVY informs selection, not recomputation.
3. **Confirm environmental edges before deploying.** Handedness advantage + favorable park factor + wind direction toward HR zones = stacked confirmation. Single-signal matchup hunts carry higher variance. The CONFIRM step in the operator workflow exists to require multi-signal alignment before exploitation.
4. **A JIG exclusion is not a model weakness.** JIG filters are deliberately narrower than MAIN. A player who qualifies on MAIN but not JIG has passed probability qualification but failed tactical matchup quality. Do not cite a JIG absence as evidence the model undervalues a player.
5. **MATCHUP → CONFIRM → EXPLOIT is operator discipline, not optional.** Observation without confirmation is noise. Confirmed signal without exploitation is waste. The three-step sequence enforces that each stage completes before the next begins.
6. **Missing pitch-mix data = `--`, never estimated.** This system previously fabricated pitch arsenal data via RNG. That history is why the rule is hard: when Savant or the pitcher-detail endpoint returns incomplete data, display `--` and note the gap. Do not estimate, interpolate, or carry forward stale data as current.

---

## Direct Relevance to MLB Scouting Seat

- Provides the complete tactical vocabulary for matchup reading: HVY signal, arsenal hunting, handedness edges, HR environment targeting.
- The display-only architecture means this seat operates as a pure interpretive layer — it reads JIG signals and narrates matchup context, never recomputes or re-ranks.
- Data-integrity rules (fabrication history, `--` fallback, zone-grid removal) are directly relevant: the seat must not fabricate pitch-mix observations when data is absent, matching the same discipline the system now enforces in code.
- MATCHUP → CONFIRM → EXPLOIT gives the seat a structured workflow for translating observations into deployment recommendations.

---

## Data Gaps / Deferred

| Topic | Status |
|-------|--------|
| Pitch-arsenal platoon split tables (batter vs pitch-type by handedness) | DATA GAP — external Baseball Savant / FanGraphs; deferred to /web-scraping session |
| Park-specific HR zones and spray-chart data | DATA GAP — external; deferred |
| Pitch-type sequencing and tunneling theory | DATA GAP — external scouting methodology; deferred |
| Weather + wind modeling frameworks beyond current multipliers | DATA GAP — external meteorology/stadium modeling; deferred |
| Pitcher fatigue / multi-start pitch-mix drift | DATA GAP — external; deferred |

---

## Takeaways

- JIG is tactical and matchup-driven; MAIN is quantitative and model-driven. The scouting seat lives entirely on the JIG side — it reads signals, narrates matchups, and never recomputes probability.
- Arsenal hunting is slot-specific. The exploit opportunity is in a specific pitch type, not the pitcher's aggregate profile. That specificity is what separates scouting from model ranking.
- The pitch mix modal was fabricated for months before 2026-06-15. The seat must hold to the same standard the code now enforces: real data or `--`, never estimated.
- Environmental edges compound. Single-signal matchups are lower conviction. CONFIRM step = require multi-signal alignment before recommending exploitation.

---

## Related Wikilinks

- [[jig-tactical-doctrine]] — source doctrine page
- [[design-pitch-mix-analysis]] — pitch mix modal design doc and data-integrity history
- [[main-jig-separation]] — architectural invariant; JIG signals must not contaminate MAIN
- [[environmental-multipliers]] — multiplier ranges JIG weights explicitly
- [[main-model-doctrine]] — the separated quantitative layer this seat does not touch
