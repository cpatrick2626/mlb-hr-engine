---
title: Hard Hit Danger - Doctrine
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# Hard Hit Danger — Doctrine

## Core Concept

Hard-hit danger doctrine governs the use of contact authority signals as secondary HR probability predictors. Hard-hit rate and exit velocity are weaker standalone signals than barrel rate — but they confirm contact quality for batters whose barrel classification is borderline or whose sample is limited. Danger clustering (multiple hard-hit hitters in same lineup vs same pitcher) creates game-level escalation beyond individual player cards.

## Signal Hierarchy

```
Primary:   barrel_rate (40% weight)
Secondary: hard_hit_pct (10%) + exit_velo (4%) = 14% combined
Tertiary:  pitcher_hard_contact_allowed (matchup signal — not in model_prob)
```

Hard-hit and exit velocity are NOT independent escalation triggers. They confirm barrel quality but cannot replace it.

## Tactical Signals

| Signal | Threshold | Classification |
|--------|-----------|----------------|
| Hard-hit rate | ≥ 50% | Elite contact authority |
| Hard-hit rate | 45–50% | Above-average |
| Hard-hit rate | 39.9% (avg) | Neutral |
| Hard-hit rate | < 35% | Below-average |
| Exit velocity | ≥ 92 mph avg | Elite |
| Exit velocity | 89.1 mph (avg) | Neutral |
| Exit velocity | < 87 mph avg | Contact-hitter profile |
| Pitcher HH allowed | ≥ 45% | Danger matchup zone |

## Escalation Conditions

1. **Dual-power confirmation**: hard-hit ≥ 45% AND barrel ≥ 8% → co-signal confirmation; supports +1 danger layer if not already counted
2. **Pitcher danger matchup**: pitcher hard-contact allowed ≥ 45% → contact window elevated regardless of pitcher HR rate stats
3. **Danger clustering**: 4+ above-average hard-hit batters in lineup vs same pitcher → game-level escalation flag
4. **Pull-air authority**: hard-hit ≥ 45% + pull% ≥ 45% → pull-air danger profile confirmed

## Failure Conditions

- **Ground-ball hard-hitter**: high hard-hit rate without barrel or FB% quality → contact authority does not convert to HR. Hard-hit GB hitters are damage suppressors in HR model.
- **Small sample instability**: hard-hit rate based on < 100 PA is noise; regress to 39.9% league avg
- **Pitcher sample thin**: pitcher HH allowed based on < 60 BF — unreliable matchup signal
- **Exit velo without angle**: high avg EV with ground-ball launch angle profile does not elevate HR probability

## Doctrine Rules

**Rule 1 — Hard-hit danger requires barrel support.** Hard-hit rate ≥ 50% without barrel rate ≥ 6% is a contact-hitter signal, not an HR signal. Do not escalate on hard-hit alone.

**Rule 2 — Pitcher hard-contact allowed is a matchup overlay.** This signal does not feed `model_prob` directly. It is a JIG/STRATEGY-layer matchup confirmation used to validate pitch mix exploitation windows.

**Rule 3 — Danger clustering is a game-level signal.** When 4+ batters in a lineup have hard-hit ≥ 42%, the game-level threat escalates independent of individual player escalation states. Evaluate at the game level, not player level.

**Rule 4 — Exit velocity is least predictive in the power multiplier.** EV at 4% weight reflects low marginal signal value once barrel and hard-hit are accounted for. High EV batters are already captured by barrel and hard-hit rate — do not double-count.

## Danger Clustering Protocol

Game-level hard-hit danger clustering triggers when:
- Opposing pitcher allows hard contact at ≥ 42% rate AND
- ≥ 4 starting batters in lineup have hard-hit ≥ 42%

Cluster signal: escalate all qualifying players in that lineup by +1 game-context layer (STRATEGY layer evaluation).

## Related Doctrine Links

- [[Barrel_Quality/doctrine]] — primary signal; hard-hit is secondary confirmation
- [[Pitch_Mix_Exploitation/doctrine]] — pitcher hard-contact allowed feeds arsenal mismatch scoring
- [[HR_Threat_Escalation/doctrine]] — danger clustering produces game-level escalation
- [[Confidence_Tiering/doctrine]] — dual-power signal (barrel + hard-hit) supports tier escalation
