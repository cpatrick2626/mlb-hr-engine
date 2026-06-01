---
title: Barrel Quality - Doctrine
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# Barrel Quality — Doctrine

## Core Concept

Barrel quality doctrine defines how the ENGINE measures, weights, and applies batter power signals from Baseball Savant Statcast data. Barrel rate is the single most predictive batter-level signal for HR probability. All other power signals are secondary and explicitly weighted below barrel rate in the `batter_power_multiplier`.

## Signal Weighting (batter_power_multiplier)

| Signal | Weight | League Avg | Source |
|--------|--------|-----------|--------|
| Barrel rate | 40% | 5.5% | Statcast |
| FB% (fly-ball rate) | 20% | 26.4% | Statcast (excl. popups) |
| Pull% | 10% | 39.2% | Statcast |
| Sweet Spot% | 10% | 33.4% | Statcast |
| Hard-Hit% (≥95 mph) | 10% | 39.9% | Statcast |
| xSLG | 8% | 0.418 | Statcast |
| Exit Velocity | 4% | 89.1 mph | Statcast |
| xISO | — | 0.157 | derived |

**Note**: FB% uses Savant `fb_pct` (pure fly-ball rate, excludes popups). Do NOT use FanGraphs FB% (~0.34) which includes popups.

## Barrel Tier Classification

| Tier | Barrel Rate | Treatment |
|------|-------------|-----------|
| Elite | ≥ 12% | Elite Platt calibration (crossover 22.3%); +2 danger layers |
| Above-Avg | 8–12% | Standard + elite regression target; +1 danger layer |
| Average | 5.5–8% | Standard treatment; 0 danger layers |
| Below-Avg | 4–5.5% | Sub-average; context moderation guard applies |
| BLOCK | < 4% | Hard deployment block; NO DEPLOYMENT regardless of signals |

## Escalation Conditions

1. **Elite barrel (≥ 12%)**: `ELITE_PLATT_BARREL_THRESHOLD = 0.10` — applies near-identity calibration across 10–29% probability range; prevents Platt compression of genuine elite HR threats
2. **Regression target ceiling**: `ELITE_REG_TARGET_BARREL_THRESHOLD = 0.08` — raises Bayesian anchor from league avg (3.0%) to `min(ceiling=1.5, power_mult) × league_avg` for qualified elite batters
3. **Pull-air profile**: pull% above league avg (0.392) with above-avg FB% → combined signal for HR contact zone targeting
4. **Recent hard-contact form**: Statcast trends last 14 days — display signal indicating current-season hot streak

## Failure Conditions

- **Blended-source inflation**: prior-year Statcast trusted at 85% for players with < 50 current-year PA (`MIN_CURRENT_YEAR_PA = 50`). Prior-year Statcast produces +1.75pp systematic bias — treat blended-source picks with caution
- **FB% quality gate**: high FB% without barrel quality (barrel_mult low) → gate discounts FB% upside by up to 50%. Formula: `gate = 0.50 + 0.50 × min(1.0, barrel_mult)`. Ground-ball hitters with negative FB% deviation unaffected
- **Regression floor**: `reg_target_adj = max(0.30, min(ceiling, statcast_mult))` — floor lowered from 0.40 to 0.30 in 2026. Extreme contact-hitter profiles (mult < 0.30) now properly suppressed
- **Context stacking on sub-average barrel**: `power_mult < 1.0` batters in favorable environments hit context moderation guard — combined multiplier capped at 1.25

## Doctrine Rules

**Rule 1 — Barrel rate is the primary signal. Period.** No combination of FB%, hard-hit%, or xSLG overrides sub-4% barrel rate. Hard block is absolute.

**Rule 2 — FB% signal requires barrel quality gate.** High fly-ball rate without corresponding barrel quality produces weak fly balls — not HR. The FB% quality gate enforces this. `FB_QUALITY_GATE_ENABLED = True`.

**Rule 3 — Elite barrel batters use separate calibration.** Standard Platt calibration (crossover 10.9%) compresses genuine elite HR probabilities. Barrel ≥ 10% uses `ELITE_PLATT_A = 0.92, ELITE_PLATT_B = -0.10` (crossover 22.3%) to preserve rank-order integrity for top-tier power hitters.

**Rule 4 — Blended-source picks require cautious sizing.** Players with prior-year Statcast blending show systematic +1.75pp bias. Do not size CORE at maximum for blended-source picks until current-year PA ≥ 50.

**Rule 5 — Re-calibrate after signal weight changes.** Any change to `batter_power_multiplier` weights requires Platt re-calibration. Current params fitted before FB% promotion — Step 3 from Session 23 remains pending.

## Related Doctrine Links

- [[Hard_Hit_Danger/doctrine]] — hard-hit rate secondary co-signal
- [[HR_Threat_Escalation/doctrine]] — barrel tier maps to danger layer count
- [[Environmental_Leverage/doctrine]] — context moderation guard protects against barrel + environment stacking
- [[Confidence_Tiering/doctrine]] — barrel rate sets tier floor gate
