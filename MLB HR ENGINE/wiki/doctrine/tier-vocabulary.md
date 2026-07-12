# Tier Vocabulary Doctrine

**Last Updated:** 2026-07-12

---

## Summary

Four distinct tier/rating vocabularies exist in MLB HR ENGINE. They apply to different surfaces and must not be merged or cross-applied without explicit operator authorization.

---

## Vocabulary 1 — Deployment / Data Tiers

**Used by:** MAIN model scoring output, pick ranking, operator dashboard leaderboard

| Tier   | Threshold | Meaning |
|--------|-----------|---------|
| APEX   | ≥ 0.20    | Highest HR probability — top engine-estimated threat |
| ELITE  | ≥ 0.16    | Very high HR probability |
| EDGE   | ≥ 0.11    | Above-threshold HR probability |
| SIGNAL | ≥ 0.07    | Moderate HR probability, reportable |
| WATCH  | ≥ 0.04    | Below deployment threshold, monitor only |
| COLD   | ≥ 0.00    | No meaningful signal |

These tiers reflect **model probability only** from `pipeline.py` and `config.py`. EV, edge, odds, and market value do not influence tier classification.

**Active threshold set:** Option A — tightened 2026-06-10 (`f3969b1`). Authoritative values live in `mlb_hr_engine_v4/config.py` (`FS_TIER_THRESHOLDS`). The table above reflects the production state as of 2026-06-10; always verify against `config.py` before relying on these values.

### Primary Ranking Doctrine

**model_tier_rank = HR Threat Rank. Primary ranking is pure model probability.**

- `APEX #1` = highest engine-estimated HR probability in APEX tier. Not "best bet."
- `ELITE #1` = highest HR probability within ELITE. Not "highest EV."
- `EDGE #1` = highest HR probability within EDGE. Not "most favorable odds."
- Default engine ranking excludes market data, odds, EV, and edge from the sort key.
- Odds, EV, edge, and sportsbook lines are **display-only** context — they never influence `model_prob`, `model_tier_rank`, or tier classification.
- Bet Value Rank (Deploy Score) is **deferred and not yet implemented**. When eventually added, it must be an additive-only secondary layer, selectable by the operator. It must not replace or contaminate the primary HR Threat Rank.
- Market value as a selectable sort layer may be added in future only with explicit operator authorization and a separate doctrine update.

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

## Vocabulary 4 — AEI Display-Band Ladder

**Used by:** Graded EDGE STACK chips in the Arsenal Edge Intel modal (PITCH EXPLOIT, BARREL PATH, H2H, HH POWER)

**Added:** 2026-07-12

A single ordered 5-rung ladder, reused by every graded EDGE STACK chip so one word means exactly one rung across the modal.

| Rung | Word  | Meaning |
|------|-------|---------|
| 5    | PRIME | Top band of this signal — strongest bullish read |
| 4    | PLUS  | Clearly above average — favorable |
| 3    | EVEN  | League-average / neutral — no lean |
| 2    | THIN  | Below average — limited support |
| 1    | FLAT  | No edge — bottom band |

**Direction:** PRIME is always the most bullish for the HR bet; FLAT the least. Every chip using this ladder is bullish-up.

**Off-ladder qualifiers** (data-state, not quality — exempt from the ladder): VOLATILE (low-confidence override), DATA GAP (no source), NO DATA (empty H2H), — (null).

**Orthogonal axis** (not a quality rating): H2H trust (NO DATA / VERY LOW / LOW / MODERATE) measures sample confidence only, never matchup quality, and keeps its own scale.

### Arsenal Edge Verdict — Named Scale

Registered as its own domain scale: EXPLOSIVE / MISMATCH / FAVORABLE / LEAN / SUPPRESSED (plus off-ladder VOLATILE, DATA GAP). The frontend displays these remapped labels (WATCH→LEAN, LIVE EDGE→FAVORABLE); `arsenal_edge.py` emissions and pick-time snapshots are unchanged.

### Inversions Resolved

- **HH RISK renamed HH POWER** — the value measures the batter's hard-hit production; high is bullish. Reads PLUS/EVEN/THIN bullish-up.
- **SEASON HR/9 tag** reworded high/elevated/low → HITTABLE/AVERAGE/STINGY so the green (batter-favorable) direction reads correctly. Thresholds unchanged.

### MODEL TIER Chip

The AEI EDGE STACK's former DEPLOYMENT chip is renamed **MODEL TIER** and shows `row.tier` verbatim (APEX stays APEX), satisfying the JIG row.tier Display Clarification rule below (the modal renders in JIG context). No rule change — a compliance record.

---

## JIG row.tier Display Clarification

**Status:** Accepted doctrine (Option A) — 2026-06-10

JIG `leaderboard_rows_jig` rows inherit `row.tier` from MAIN via shallow copy. This means `row.tier` as displayed in JIG context reflects **MAIN model probability tier** (Vocabulary 1 above), not a JIG-native tactical tier.

| Context | Tier Source | Meaning |
|---------|-------------|---------|
| MAIN leaderboard | `FS_TIER_THRESHOLDS` applied to model probability | Deployment confidence |
| JIG leaderboard (`row.tier`) | Inherited from MAIN — same `FS_TIER_THRESHOLDS` | MAIN model probability context only |
| JIG tactical priority | `jigScore` and JIG sort order | Tactical rank within JIG — separate from `row.tier` |

**Display rule:** When `row.tier` appears in JIG, label it or treat it as "Model Tier" (MAIN context), not "JIG Tier" or "JIG confidence."

**No `jigTier` field exists.** If a JIG-native tier is desired, it must be introduced as a separate `jigTier` field after a `jigScore` distribution audit and explicit operator authorization. See `main-jig-separation.md`.

---

## Separation Rules

1. Do not use Full Slate escalation states (QUIET/ACTIVE/ELEVATED/DANGEROUS/CRITICAL) as MAIN scoring tiers.
2. Do not use deployment tiers (APEX/ELITE/EDGE/SIGNAL/WATCH/COLD) as Full Slate card states.
3. Do not promote prototype card tiers (CRITICAL/HIGH/MODERATE/LOW) to production without an explicit authorized mapping.
4. Any vocabulary merge or alias must be explicitly documented and operator-authorized before implementation.
5. Do not describe JIG `row.tier` as JIG-native tactical tier or JIG confidence. It is MAIN model probability context inherited via shallow copy.
6. Rating values on any surface must not reuse words from Vocabulary 1, 2, or 3. Feature and panel names (ARSENAL EDGE INTEL, EDGE STACK, EDGE SCORE) are surface names, not ratings, and are exempt.

---

## Cross-References

- [MAIN Model Doctrine](main-model-doctrine.md)
- [JIG Tactical Doctrine](jig-tactical-doctrine.md)
- [Visual Design Doctrine](visual-design-doctrine.md)
- [App Shell Layout](app-shell-layout.md)