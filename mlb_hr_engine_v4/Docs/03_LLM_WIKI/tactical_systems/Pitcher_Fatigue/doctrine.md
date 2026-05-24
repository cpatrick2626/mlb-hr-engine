---
title: Pitcher Fatigue - Doctrine
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# Pitcher Fatigue — Doctrine

## Core Concept

Pitcher fatigue is a rest-based multiplier applied to the pitcher component of HR probability. It reflects mechanical degradation: shorter rest periods correlate with reduced velocity, command fade, and secondary pitch reliability — all of which expand HR contact windows. The ENGINE does not model pitch count or in-game velocity in real time; fatigue is approximated via days-rest schedule.

## Tactical Signals

| Rest Days | Fatigue Factor | Classification |
|-----------|---------------|----------------|
| ≤ 3 days | 1.06–1.08 | High fatigue |
| 4 days | 1.01–1.03 | Moderate fatigue |
| 5 days | 1.00 | Standard (neutral) |
| 6+ days | 1.00 | Extra rest (neutral) |

**TTOP (Third Time Through Order):** within-game familiarity shifts batter advantage; command degrades mid-lineup turn. Model does not capture TTOP in `fatigue_fac` — it is a game-state escalation signal evaluated at JIG/STRATEGY level.

## Escalation Conditions

1. **Short rest ≤ 4 days** — `fatigue_fac > 1.0` applies directly to model_prob pipeline
2. **TTOP exposure confirmed** — starter projects to face target batter 3rd time; elevate escalation tier
3. **Command fade + contact batter** — velocity-sensitive pitcher facing pull-air batter late in game
4. **Bullpen exposure** — if starter exits early, relief pitcher handedness/arsenal creates secondary window
5. **High workload prior start** — ≥ 110 pitches in prior outing signals compounded fatigue even at standard rest

## Failure Conditions

- **Extra rest removed from model**: prior linear decay (0.97–0.99) for 6+ days removed 2026-05-16 — no backtest evidence it makes pitchers harder to hit
- **Standard rest = neutral**: 5-day rest is baseline; no escalation or suppression applies
- **Bullpen game**: fatigue doctrine only applies to starting pitcher; opener/piggyback roles reset
- **High-K pitcher on short rest**: elite strikeout pitchers maintain suppressive profiles through fatigue — HR rate does not predictably spike
- **Pitch count unknown**: ENGINE approximates via days-rest; actual fatigue state requires in-game monitoring

## Doctrine Rules

**Rule 1 — Fatigue is a multiplier, not a standalone signal.** Short rest alone without barrel quality or pitch mix exploitation does not justify tier escalation. Fatigue amplifies existing edge; it does not create edge from nothing.

**Rule 2 — TTOP is game-state, not model.** The ENGINE's `fatigue_fac` is computed pre-game from schedule data. TTOP risk must be evaluated at deployment time based on expected inning/pitch count projections.

**Rule 3 — Extra rest is not an advantage.** Removed from model 2026-05-16. Do not apply pitching difficulty bonus to well-rested starters — treat as neutral baseline.

**Rule 4 — Pitcher factor attenuation dampens fatigue impact.** `PITCHER_FACTOR_SCALE = 0.60` compresses overall pitcher factor range [0.55, 1.60] → effective [0.73, 1.36]. Fatigue boost is attenuated proportionally. Raw fatigue boost of 1.08 becomes effective ~1.048 after attenuation.

**Rule 5 — Bullpen exposure is not modeled — escalate manually.** When starter exits early (< 5 innings), bullpen exposure creates secondary HR windows from handedness and arsenal mismatches. This is a JIG/STRATEGY-level adjustment.

## Doctrine Priority

```
Short rest → TTOP exposure → late-inning command fade → bullpen exposure
```

Fatigue escalation requires short rest (≤ 4 days) as the model trigger. TTOP and bullpen exposure are overlay signals for game-state deployment decisions.

## Related Doctrine Links

- [[Pitch_Mix_Exploitation/doctrine]] — fatigue degrades secondary pitch reliability, amplifying arsenal mismatch
- [[Barrel_Quality/doctrine]] — barrel quality required to convert fatigue window into HR
- [[HR_Threat_Escalation/doctrine]] — fatigue is danger layer component
- [[Confidence_Tiering/doctrine]] — short rest + barrel escalates WATCH → LIVE
