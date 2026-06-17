---
seat: hr-prediction
source_id: "001"
title: Engine Modeling Method
source_type: internal-doctrine
source_file: "wiki/formulas/batter-score-weights.md, wiki/formulas/environmental-multipliers.md, wiki/formulas/pitcher-vulnerability.md, wiki/doctrine/main-model-doctrine.md"
date_ingested: 2026-06-17
key_people: "--"
status: ingested
---

## Summary

Four internal doctrine files define the complete HR-prediction modeling method: batter base score construction (weighted Statcast metrics), pitcher vulnerability modifier (28% of base score), environmental multipliers (applied after base score), and the MAIN model doctrine governing how those components assemble into `model_prob` and operator-facing ranks. The core formula is Poisson: `P(HR≥1) = 1 − e^(−λ)`. λ is the assembed composite. Primary rank is pure HR Threat Rank — market data never contaminates it.

---

## Key Concepts

| Concept | Notes |
|---------|-------|
| Poisson HR probability | `P(HR≥1) = 1 − e^(−λ)`. λ = assembled composite of batter score × pitcher vulnerability × environmental multipliers. |
| Batter base score (100%) | Barrel% 20%, ISO 15%, HR/FB 12%, xSLG 10%, Avg EV 7%, Hard Hit% 6%, Sweet Spot% 6%, Pull% 5%, Launch Angle 4%, xwOBA 2%, SwStr% −2%, K% −1%. |
| Pitcher vulnerability (28%) | HR/9 9%, Barrel% Allowed 5%, xFIP 4%, Recent HR/9 4%, Hard Hit% Allowed 3%, GB% 3%. Applied as modifier to batter base score. |
| Environmental multipliers | Applied multiplicatively after base score. Platoon ×0.90–1.12, Park ×0.88–1.14, Wind ×0.93–1.09, Temp ×0.93–1.03, Time Through Order ×1.00–1.03, H2H This Season ×0.93–1.14, H2H Career ×0.94–1.08. |
| Dome rule | Dome/retractable-roof-closed games: wind and temperature multipliers revert to ×1.00. Park factor still applies. |
| Model qualifies first | Market data (odds, EV, edge) is display-only. It does not gate player qualification in MAIN. |
| HR Threat Rank | `model_tier_rank` = pure HR probability rank within each tier (APEX/ELITE/EDGE/…). Never re-sorted by market rank, EV, or edge. |
| Negative batter weights | SwStr% (−2%) and K% (−1%) reduce batter score. High strikeout/whiff rates penalize the λ even when power metrics are strong. |

---

## Decision Principles for HR Prediction

1. **Barrel% is the dominant explainer.** At 20% of batter base score it carries more weight than any other single metric. When narrating why a batter ranks where they do, Barrel% is the first check. A batter with weak Barrel% needs other metrics to compensate substantially.
2. **Pitcher GB% suppresses HR regardless of batter quality.** High GB% means fewer fly balls, which means fewer HR chances. A strong batter profile meeting a high-GB pitcher takes a λ hit that can drop a tier. The signal is real and consistent, not a rounding artifact.
3. **H2H This Season carries the widest multiplier range (×0.93–1.14).** Fresh head-to-head this season is the strongest situational signal in the environmental layer. When it exists and is substantial, it overrides the weight of aggregate seasonal averages. Absence of current-season H2H defaults to career H2H (×0.94–1.08), a narrower range.
4. **Recent HR/9 catches what seasonal xFIP misses.** A pitcher in a bad stretch accumulates HR allowed that xFIP hasn't fully processed. Recent HR/9 (4%) exists specifically to surface hot/cold pitcher states. Use it to explain unexpected λ amplification on "safe" pitchers.
5. **Market data displays after model qualifies.** Odds, EV%, and edge are context for bet sizing, not player selection. A player with negative EV is still correctly placed at APEX #1 if their HR probability is highest. Do not conflate rank with bet recommendation.
6. **Never cite weather for dome games.** The dome rule is a hard override. Wind direction and temperature are ×1.00 for dome/retractable-closed. Citing weather as a factor for Minute Maid, Tropicana, or Rogers Centre is a data-integrity error.
7. **APEX #1 = highest HR probability, not best bet.** The model's primary output is probability rank. Bet value (Deploy Score) is a deferred, additive-only secondary layer. These must not be conflated in any explanation.

---

## Direct Relevance to HR Prediction Seat

- Provides the complete weight table the seat uses to narrate why a specific batter is ranked where they are: which metrics are strong, which are dragging the score, and what the pitcher/environment added or subtracted.
- Decision Principles give the seat a ranked reading order for explanation: start with Barrel%, check pitcher GB%/HR/9, check H2H this season, then park/wind (dome check first), then platoon.
- The market-qualifies-last rule is critical for seat integrity: the seat narrates model probability, never bet value. Confusing APEX #1 with "best bet" is a scope violation.
- Negative weights (SwStr%, K%) are counterintuitive — the seat needs to surface them when a seemingly strong power profile is suppressed by contact issues.

---

## Data Gaps / Deferred

| Topic | Status |
|-------|--------|
| Statcast expected-stats methodology (xSLG, xwOBA derivation) | DATA GAP — external Baseball Savant methodology; deferred to /web-scraping session |
| Poisson vs empirical-Bayes calibration for low-HR-rate batters | DATA GAP — external statistical theory; deferred |
| Platoon split sample-size stabilization rates | DATA GAP — external research; deferred |
| Park factor construction methodology | DATA GAP — external (e.g., FanGraphs park factor derivation); deferred |
| Calibration findings (n<200 real settled picks) | DEFERRED — Phase 3 auto_learn per commit af85399; insufficient sample for threshold changes |

---

## Takeaways

- λ assembly is three-layer: batter base score (power quality) → pitcher vulnerability (fly-ball / hard-contact yield) → environmental multipliers (situational context). Each layer compounds multiplicatively.
- The highest-weight single signal is Barrel% (20%). The highest-range single multiplier is H2H This Season (×0.93–1.14). Both deserve priority in any HR-probability explanation.
- Market data never gates model output. The seat narrates probability, not value — these are distinct outputs with distinct purposes.
- All weights live in `config.py`. This note reflects 2026-06-17 production state; verify before acting.

---

## Related Wikilinks

- [[batter-score-weights]] — full weight table source
- [[pitcher-vulnerability]] — full vulnerability weight table source
- [[environmental-multipliers]] — multiplier table source
- [[main-model-doctrine]] — MAIN architecture, ranking doctrine, market-data rules
- [[main-jig-separation]] — why JIG tactical signals must not contaminate λ
- [[pipeline-data-flow]] — how these components flow through pipeline.py
