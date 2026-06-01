---
title: HR Threat Escalation - Doctrine
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# HR Threat Escalation — Doctrine

## Core Concept

Escalation doctrine governs the logic by which player-level signals aggregate into a deployable threat classification. Individual signals (barrel rate, park factor, fatigue, pitch mix, market edge) carry different weights and interact multiplicatively through the ENGINE's probability model. The escalation system converts this into categorical threat states used for deployment decisions and confidence tier assignment.

## Danger Layer System

Each confirmed tactical signal adds or subtracts a danger layer:

| Signal | Condition | Layer Δ |
|--------|-----------|---------|
| Barrel rate | ≥ 0.12 (elite) | +2 |
| Barrel rate | 0.08–0.12 (above avg) | +1 |
| Barrel rate | < 0.04 | BLOCK |
| HVY modifier | ≥ 1.25 | +1 |
| HVY modifier | ≥ 1.35 | +2 |
| HVY modifier | ≤ 0.80 | −1 |
| Fatigue factor | ≥ 1.06 (≤ 3 days rest) | +1 |
| Fatigue factor | ≥ 1.06 + TTOP projected | +2 |
| Environmental combined | ≥ 1.25 | +2 |
| Environmental combined | ≥ 1.15 | +1 |
| Park factor | ≤ 0.87 (suppressed park) | −1 |
| EV% | ≥ 5.0% | +1 |
| EV% | ≥ 8.0% | +2 |

## Threat Level Classification

| Danger Layers | Threat Level | Tier Eligible |
|---------------|-------------|---------------|
| 4+ | MAX THREAT | CORE |
| 3 | HIGH THREAT | STRONG |
| 2 | LIVE THREAT | LIVE |
| 1 | WATCH STATE | WATCH |
| 0 | NEUTRAL | WATCH |
| Any BLOCK | SUPPRESSED | NO DEPLOYMENT |

## Escalation Conditions

1. **Full stack**: barrel ≥ 0.10 + favorable environment + HVY ≥ 1.20 → 3 layers → HIGH THREAT
2. **Elite barrel alone**: barrel ≥ 0.12 → +2 layers → minimum LIVE THREAT
3. **Max stack**: barrel ≥ 0.12 + environment ≥ 1.25 + fatigue + HVY ≥ 1.25 → 6 layers → MAX THREAT
4. **Market confirmation**: EV% ≥ 5% adds layer — confirms model edge is priced in the market

## Failure Conditions

- **Hard block conditions** (any single one blocks deployment):
  - `barrel_rate < 0.04` — insufficient power quality
  - `park_factor ≤ 0.87` — suppressive park auto-block
  - `model_prob < MIN_EV_PCT` — base probability insufficient
  - `power_mult < 1.0` AND context stack creates false positive (context guard fires)

- **Single-signal escalation prohibited**: HVY alone, environment alone, or fatigue alone does not reach LIVE THREAT

## Game-Level Escalation

Beyond player-level signals, game-level escalation considers:
- Multiple high-threat players in same lineup → game-level MAX THREAT flag
- Opposing pitcher on short rest → amplifies all player-level threats in lineup
- Weather event (unusual wind shift, temperature drop at game time) → downgrades environment layer

## Player Card Escalation

Player card escalation states render as:
- `MAX THREAT` — red card header, all signals confirmed
- `HIGH THREAT` — orange card header, 3 layers
- `LIVE THREAT` — yellow card header, 2 layers
- `WATCH` — gray card header, monitoring state
- `SUPPRESSED` — blocked card, no display in deployment tab

## Deployment Readiness Gate

A player passes deployment readiness when:
```
danger_layers ≥ 2
AND model_prob ≥ MIN_EV_PCT
AND barrel_rate ≥ 0.06
AND no BLOCK condition active
AND confidence_tier ≥ LIVE
```

## Related Doctrine Links

- [[Barrel_Quality/doctrine]] — primary layer signal; BLOCK condition gatekeeper
- [[Environmental_Leverage/doctrine]] — environment layer rules
- [[Pitch_Mix_Exploitation/doctrine]] — HVY modifier layer rules
- [[Pitcher_Fatigue/doctrine]] — fatigue layer rules
- [[Confidence_Tiering/doctrine]] — tier assignment from threat level
- [[Market_Inefficiency/doctrine]] — EV/Edge layer rules
