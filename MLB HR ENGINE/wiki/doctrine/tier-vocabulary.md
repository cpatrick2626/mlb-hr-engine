# Tier Vocabulary Doctrine

**Last Updated:** 2026-06-08

---

## Summary

Three distinct tier vocabularies exist in MLB HR ENGINE. They apply to different surfaces and must not be merged or cross-applied without explicit operator authorization.

---

## Vocabulary 1 — Deployment / Data Tiers

**Used by:** MAIN model scoring output, pick ranking, operator dashboard leaderboard

| Tier | Meaning |
|------|---------|
| APEX | Highest model confidence, strongest EV |
| ELITE | Very high model confidence |
| EDGE | Above-threshold model confidence |
| SIGNAL | Moderate model confidence, reportable |
| WATCH | Below deployment threshold, monitor only |
| COLD | No meaningful signal |

These tiers reflect **model probability and EV** output from `pipeline.py` and `config.py`.

---

## Vocabulary 2 — Full Slate Escalation States

**Used by:** Full Slate Matrix game-card escalation hierarchy (visual escalation, not pick ranking)

| State | Meaning |
|-------|---------|
| QUIET | No elevated threat detected |
| ACTIVE | Mild threat signal present |
| ELEVATED | Moderate threat — operator attention |
| DANGEROUS | High threat — active escalation |
| CRITICAL | Maximum escalation — top priority |

These states reflect **visual escalation** within the Full Slate Matrix surface. They communicate game-card threat level to the operator, not model rank.

---

## Vocabulary 3 — Prototype Card Tiers

**Used by:** `mlb_hr_engine_v4/frontend/` prototype HR threat card components (design iteration only)

| Tier | Meaning |
|------|---------|
| CRITICAL | Prototype top-tier card signal |
| HIGH | Prototype high-tier card signal |
| MODERATE | Prototype moderate-tier card signal |
| LOW | Prototype low-tier card signal |

These tiers exist in **prototype mock data only**. They are not production scoring tiers. Do not map prototype card tiers to deployment tiers or escalation states without a separate operator-authorized mapping.

---

## Separation Rules

1. Do not use Full Slate escalation states (QUIET/ACTIVE/ELEVATED/DANGEROUS/CRITICAL) as MAIN scoring tiers.
2. Do not use deployment tiers (APEX/ELITE/EDGE/SIGNAL/WATCH/COLD) as Full Slate card states.
3. Do not promote prototype card tiers (CRITICAL/HIGH/MODERATE/LOW) to production without an explicit authorized mapping.
4. Any vocabulary merge or alias must be explicitly documented and operator-authorized before implementation.

---

## Cross-References

- [MAIN Model Doctrine](main-model-doctrine.md)
- [JIG Tactical Doctrine](jig-tactical-doctrine.md)
- [Visual Design Doctrine](visual-design-doctrine.md)
- [App Shell Layout](app-shell-layout.md)
