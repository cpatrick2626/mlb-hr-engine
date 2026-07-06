Status: SEED for Strategy-section design mission (Fable 5, queued). 2026-07-06. Companion to doctrine/operator-pick-workflow.md.

# Strategy Section — Seed

## Purpose
Seed input for designing the Strategy section: how the app should help build winning HR tickets by scoring/ranking/guiding picks from its signals. Combines the operator's actual workflow (see [[operator-pick-workflow]]) with a reasoning framework. NOTE: this is REASONING, not proven method — see the critical caveat below.

## CRITICAL CAVEAT (must anchor the whole mission)
The self-learning feedback loop has NEVER run end-to-end. No settled pick outcomes have been fed back. Therefore NOBODY — not the operator, not the app, not any model — currently knows which signals or combinations actually predict HRs on this slate. Every weighting/priority below is baseball/betting REASONING, not validated fact. The only path to real "best" is: settle picks → measure hit rates by signal → let calibration data earn the weighting. The Strategy mission must treat signal-weighting as HYPOTHESES to be validated by the feedback loop, not as settled rules to hardcode.

## Reasoning framework (hypotheses, to be validated)
1. **Slate framing first:** assess environment (temp/wind/park — hot+wind-out inflates HR), count of APEX/ELITE hitters and TARGET pitchers, before picking. Aggression scales with HR environment.
2. **Core funnel** (refines operator's TM→dot→AEI flow): TM + HR prob (headline) → green dot (batter-threat axis agrees) → open AEI → weight the ARSENAL EDGE verdict (MISMATCH/EDGE) + whether batter crushes the pitcher's most-thrown pitch ("HUNT THIS" × batter HR/SLG vs that pitch type). This pitch-mix ALIGNMENT is hypothesized as the strongest single "why" the app surfaces.
3. **DO NOT gate on the season pitcher grade ("TOUGH"):** a season-tough pitcher can be a great SPECIFIC matchup (verified case: Caminero vs Schlittler — tough season HR/9 but batter crushes his 45%-usage 4-seam). This is why the AEI relabel is queued — current "TOUGH" wording causes good picks to be faded. The matchup-specific read should outweigh the season grade.
4. **Weight tiny-sample H2H LEAST:** AEI itself flags "3 PA — NOT PREDICTIVE." Small-sample H2H is usually noise; must not override the pitch-mix read.
5. **Diversification vs conviction:** operator picks all-different players (flagged as possibly suboptimal). All-different manages variance (independent single-HR bets). Conviction (bigger/repeated stake) may be warranted IF an edge is real — but "real" is unknowable without the feedback loop. Default to variance-management until data informs it.
6. **Role-based small ($1) picks** are a coverage/lottery layer — funnel bar can be slightly lower, but don't fill a role slot with a genuinely bad matchup.

## What the Strategy mission must design
- How to SCORE/RANK picks from the combined signals (a pick-quality score?), treating weights as tunable hypotheses.
- How to ENCODE workflows (operator's funnel; possibly others) so the app guides or automates pick-building.
- How the FEEDBACK LOOP (settlement → hit rates by signal) validates and re-tunes the weighting so "best" is earned, not asserted.
- Dependency: this is gated on the settlement job (legs.hr_result) + per-user attribution actually working — flag settlement/calibration as the prerequisite for any validated strategy.

## Cross-refs
- doctrine/operator-pick-workflow.md (how the operator actually picks)
- The AEI relabel pass (queued — fixes the "TOUGH" bypass gate that misleads the funnel)
- Settlement job + calibration loop (Phase D backlog — prerequisite for validated weighting)
