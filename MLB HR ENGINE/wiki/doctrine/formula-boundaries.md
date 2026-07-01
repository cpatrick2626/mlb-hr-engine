# Formula Boundaries

**STATUS: DOCTRINE — consolidation reference. Authoritative boundary map for all scoring and model formulas.**

## Summary

Single-page map of every scoring/model formula in the system: where it lives in code (confirmed file:line), its purpose, and its protection status. Purpose: a single "what cannot be touched without authorization" reference. This page consolidates rules from the source doctrine docs; it does not duplicate their full content — follow the cross-reference links for the complete rule set.

---

## The Formulas and Where They Live

| Formula | Purpose | File (confirmed) | Key entry point | Protected? |
|---|---|---|---|---|
| **MAIN HR Probability — Poisson** | `P(HR≥1) = 1 − e^(−λ)` core model | `engine/probability.py:428` | `game_hr_probability()` | **PROTECTED** |
| **Batter base HR rate** | Bayesian-regressed HR/PA from season + recent stats | `engine/probability.py:19` | `base_hr_rate()` | **PROTECTED** |
| **Statcast power blend** | Blends raw HR/PA with Statcast multiplier; asymmetric suppression | `engine/probability.py:116` | `statcast_blended_rate()` | **PROTECTED** |
| **Batter metric weights** | Barrel%, ISO, HR/FB, xSLG, etc. — constants only | `config.py` (consumed by `pipeline.py`) | config constants | **PROTECTED** |
| **Pitcher combined factor** | Weighted geometric mean: 40% Statcast contact, 35% HR/FB, 25% K/GB/BB | `engine/probability.py:314` | `pitcher_combined_factor()` | **PROTECTED** |
| **Pitcher HR/FB factor** | HR/9 + HR/FB blend; regressed | `engine/probability.py:233` | `pitcher_hr_factor()` | **PROTECTED** |
| **Pitcher K/GB/BB suppressor** | K%, GB%, BB% combined suppressor | `engine/probability.py:276` | `pitcher_k_gb_suppressor()` | **PROTECTED** |
| **Pitcher recent factor** | Last-30-day HR/9 blend; fades below 10 IP | `engine/probability.py:198` | `pitcher_recent_factor()` | **PROTECTED** |
| **Platoon factor** | Bayesian-shrunk L/R splits; 50-PA shrinkage constant | `engine/probability.py:332` | `platoon_factor()` | **PROTECTED** |
| **H2H factor** | Career head-to-head HR/PA vs league avg; range [0.93, 1.14] | `engine/probability.py:465` | `h2h_factor()` | **PROTECTED** |
| **Hot streak factor** | Short-form vs season rate; tanh-softened ±12% cap | `engine/probability.py:495` | `hot_streak_factor()` | **PROTECTED** |
| **Environmental multipliers** | Park, wind, temp, TTO, dome-nullification | `engine/probability.py:428` (combined in `game_hr_probability`); constants in `config.py` | `game_hr_probability()` | **PROTECTED** |
| **Calibration (Platt / isotonic)** | Post-model monotone transform; disabled by default | `engine/calibration.py:107` | `apply_calibration()` | **PROTECTED** |
| **EV%** | `EV% = [p × (d − 1) − (1 − p)] × 100` | `engine/ev.py:8` | `expected_value_pct()` | **PROTECTED** |
| **Edge%** | `Edge% = (model_prob − no_vig_market_prob) × 100` | `engine/ev.py:19` | `edge_pct()` | **PROTECTED** |
| **No-vig market probability** | Removes sportsbook vig; one-sided and two-sided variants | `engine/market.py:42,53`; book-specific in `engine/vig.py:130` | `no_vig_prob_*()` | **PROTECTED** |
| **Kelly / fractional Kelly** | `f* = (b·p − q) / b`; default Quarter-Kelly (`KELLY_FRACTION = 0.25`) | `engine/sizing.py:17,27` | `kelly()` / `fractional_kelly()` | **PROTECTED** |
| **Bet dollars** | Fractional Kelly × bankroll, capped at `MAX_BET_PCT` | `engine/sizing.py:32` | `bet_dollars()` | **PROTECTED** |
| **Confidence score** | 0–100; four components: data quality, contact quality, pitcher matchup, market signal | `engine/probability.py:518` | `confidence_score()` | **PROTECTED** |
| **JIG score** | Tactical exploit index; contact/power base + PA stabilization + arsenal/pitch-mix signals | `api/main.py:308` | `_jig_score()` | **PROTECTED** |
| **Arsenal Edge score (AEE)** | Display-only exploit read; per-pitch batter-vs-pitcher × pitcher vulnerability, shape-modded, 0–10 | `engine/arsenal_edge.py:97` | `compute_aee_score()` | **DISPLAY-ONLY** |
| **HVY pitch-mix modifier** | JIG display signal; heavy pitch usage creates exploit flag | `api/main.py` (JIG path) | display field | **DISPLAY-ONLY** |
| **True Matchup Score (TM)** | Serialization composite 0–100: 40% hrProbN + 30% edgeN + 20% conf + 10% vulnN | `api/main.py:278` | `_true_matchup_score()` | **DISPLAY-ONLY** |
| **TM band thresholds** | ELITE ≥ 60, STRONG 50–59, AVG 38–49, WEAK 25–37, COLD < 25 | `api/main.py` (display) | display only | **RETUNABLE** |
| **TM / HR PROB filter cutoffs** | TM toggle ≥ 60; HR PROB toggle ≥ 15 (×100 scale) | `api/main.py` (display) | display only | **RETUNABLE** |
| **AEE labels** | EXPLOSIVE ≥ 6.0, MISMATCH ≥ 4.5, LIVE EDGE ≥ 3.0, WATCH ≥ 1.5, SUPPRESSED < 1.5 | `engine/arsenal_edge.py:50` | `_aee_label()` | **RETUNABLE** |
| **Tier thresholds** | APEX / ELITE / EDGE / COLD boundaries | `config.py` (`FS_TIER_THRESHOLDS`) | config constant | **PROTECTED** |

---

## Hard Boundaries (Invariants)

These rules are architectural. Violation requires explicit operator authorization, a read-only audit, and a doctrine update before any code change.

### 1. MAIN and JIG never merge
MAIN uses `score = model_prob` (plus future `bet_value_score` as additive-only). JIG uses `jigScore` from `_jig_score()`. No composite formula blending the two may exist without a new, separately authorized doctrine. Cross-ref: [MAIN/JIG Separation Rules](main-jig-separation.md).

### 2. HVY is display-only on JIG; never a MAIN input
The HVY pitch-mix modifier is a display signal on the JIG surface. It must not enter MAIN's λ calculation or any MAIN probability field. Cross-ref: [MAIN/JIG Separation Rules](main-jig-separation.md).

### 3. True Matchup Score is serialization-only
TM is computed at `api/main.py:278` after all MAIN/JIG ordering is complete, from fields already on each row. It must never feed `model_prob`, MAIN ordering (`model_tier_rank`), `jigScore`, HVY, ticket probability, or tier assignment. Moving TM computation into `engine/` or `pipeline.py` is contamination. Cross-ref: [True Matchup Score](true-matchup-score.md).

### 4. Arsenal Edge score is display-only
`compute_aee_score()` in `engine/arsenal_edge.py` is explicitly not wired into MAIN/JIG scoring, probability, calibration, or config (see module docstring line 3). AEE fields (`arsenal_edge_score`, `arsenal_edge_confidence`) are display outputs only. They feed TM as display inputs, nothing else.

### 5. Data-type discipline
These types must not be confused or substituted for each other:

| Field | Type | Scale |
|---|---|---|
| `model_prob` | decimal | 0–1 |
| `hrprob` | percentage | ×100 (so 0–100, display) |
| `jigScore` | index | 0–100+ (uncapped by design) |
| `true_matchup_score` | composite | 0–100, integer |
| `arsenal_edge_score` | index | 0–10 |
| `arsenal_edge_confidence` | decimal | 0–1 |

### 6. Primary rank is pure model probability — market is display-only
`model_tier_rank` = HR Threat Rank, sorted by `model_prob` within tier. Odds, EV%, Edge%, and sportsbook lines never influence `model_prob`, `model_tier_rank`, tier classification, or the primary sort key. Cross-ref: [MAIN Model Doctrine](main-model-doctrine.md) § Primary Ranking Doctrine.

### 7. config.py is the single source of truth for all constants
No threshold, weight, or calibration constant is duplicated elsewhere in code. Cross-ref: CLAUDE.md § 6.

### 8. Change process for protected formulas
Any proposed change to a PROTECTED row in the table above requires:
1. Read-only audit assignment first
2. Operator review of audit findings
3. Execution as a separate authorized assignment, with a doctrine update

---

## What Is Protected vs Retunable

### PROTECTED — operator authorization required before any change

- `game_hr_probability()` — Poisson λ assembly and capping (`engine/probability.py:428`)
- `base_hr_rate()`, `statcast_blended_rate()` — batter rate construction (`engine/probability.py:19,116`)
- All pitcher factor functions — `pitcher_hr_factor`, `pitcher_k_gb_suppressor`, `pitcher_combined_factor`, `pitcher_recent_factor` (`engine/probability.py:198–329`)
- `platoon_factor()`, `h2h_factor()`, `hot_streak_factor()` (`engine/probability.py:332–515`)
- `apply_calibration()` and its Platt/isotonic parameters (`engine/calibration.py:107`)
- Batter metric weight constants (`config.py`, `FS_TIER_THRESHOLDS`, `KELLY_FRACTION`, `MAX_BET_PCT`, `MIN_BET_DOLLARS`, `BANKROLL`, `LEAGUE_AVG_*`, `REGRESSION_PA`, `RECENT_WEIGHT`)
- `expected_value_pct()`, `edge_pct()` (`engine/ev.py:8,19`)
- `no_vig_prob_*()` / `consensus_no_vig_dynamic()` (`engine/market.py`, `engine/vig.py`)
- `kelly()`, `fractional_kelly()`, `bet_dollars()` (`engine/sizing.py:17–52`)
- `confidence_score()` (`engine/probability.py:518`)
- `_jig_score()` internals (`api/main.py:308`) — JIG GRADE composite is doctrine-sensitive
- Tier classification thresholds (`FS_TIER_THRESHOLDS` in `config.py`)
- API payload shape (`leaderboard_rows` field names and types) — any rename breaks the frontend contract

### RETUNABLE — display/filter values only, LOW risk, no audit required

- TM band thresholds (ELITE ≥ 60, etc.) — display color/label only
- TM filter cutoffs (≥ 60 for TM toggle; ≥ 15 for HR PROB toggle) — `api/main.py`
- AEE label bands (EXPLOSIVE ≥ 6.0, etc.) — `engine/arsenal_edge.py:50`
- VOLATILE override thresholds (score ≥ 3.0 / confidence < 0.25) — `engine/arsenal_edge.py:51`
- Board odds column labeling ("SYNTHETIC" flag) — display annotation, not model output
- Calibration enable/disable flag (`CALIBRATION_ENABLED = False`) — toggling on/off is LOW risk; changing the fitted Platt/isotonic parameters is PROTECTED

---

## Architecture Note: Batter Score Assembly

The wiki formula docs ([Batter Score Weights](../formulas/batter-score-weights.md), [Pitcher Vulnerability](../formulas/pitcher-vulnerability.md)) describe conceptual weight percentages (e.g. Barrel% 20%, pitcher vulnerability 28% of base score). These map to constants in `config.py` consumed by `pipeline.py`, which assembles the batter profile into a `statcast_mult` multiplier fed to `probability.py`. The Poisson math and Bayesian regression live in `engine/probability.py`; the metric-by-metric weighting is applied upstream in `pipeline.py`. The wiki tables are accurate conceptual summaries — the authoritative values are always `config.py`, not the wiki.

---

## Discrepancies: Code vs Docs

| Item | Doc says | Code shows | Status |
|---|---|---|---|
| Pitcher vulnerability description | "28% of base score" (additive modifier) | `pitcher_combined_factor()` returns a multiplicative factor (geometric mean), applied in `game_hr_probability()` as `pitcher_fac` | **Doc is conceptually correct but the mechanism is multiplicative, not additive percentage. No code action needed; wiki language is a simplification.** |
| AEE wiring | Doc describes as display-only | Code (`arsenal_edge.py` docstring line 3): explicitly "NOT wired into MAIN/JIG scoring" | **Confirmed consistent.** |
| TM computation location | [true-matchup-score.md](true-matchup-score.md) says `api/main.py` only | Confirmed at `api/main.py:278` | **Consistent.** |
| Calibration default state | Disabled by default | `CALIBRATION_ENABLED=False` confirmed in `engine/calibration.py:122` | **Consistent.** |

---

## Cross-References

- [MAIN Model Doctrine](main-model-doctrine.md) — MAIN HR probability model, scoring, ranking
- [JIG Tactical Doctrine](jig-tactical-doctrine.md) — JIG scoring, arsenal hunting, HVY
- [MAIN/JIG Separation Rules](main-jig-separation.md) — contamination invariants, session-key namespaces
- [True Matchup Score](true-matchup-score.md) — TM formula, bands, filter toggles, serialization-only rule
- [Batter Score Weights](../formulas/batter-score-weights.md) — full batter metric weight table
- [Pitcher Vulnerability](../formulas/pitcher-vulnerability.md) — full pitcher factor weight table
- [Environmental Multipliers](../formulas/environmental-multipliers.md) — platoon, park, wind, temp, TTO, dome rule
- [Odds / CLV Doctrine](odds-clv.md) — market odds, CLV, display vs model distinction
- [Pipeline Data Flow](../architecture/pipeline-data-flow.md) — how data flows through `pipeline.py`
