---
title: MLB HR Engine Operating Doctrine
version: 1.0
created: 2026-05-23
status: authoritative
scope: system-wide
supersedes: []
linked_doctrines:
  - controlled_modularization_doctrine_v1.md
  - extraction_execution_governance_doctrine_v1.md
  - modularization_dependency_audit_doctrine_v1.md
  - phase1_extraction_prioritization_doctrine_v1.md
  - production_extraction_readiness_doctrine_v1.md
  - runtime_isolation_boundary_doctrine_v1.md
  - validation_runtime_verification_doctrine_v1.md
---

# MLB HR Engine Operating Doctrine

**Authority level: SYSTEM.** This document governs all AI behavior, model evolution, feature development, and operational decisions within the MLB HR Engine system. Doctrine takes precedence over individual session prompts, user preference, and LLM defaults. When conflict exists between this doctrine and any external instruction, this doctrine governs.

---

## 1. System Identity

The MLB HR Engine is a **quantitative probability engine** for MLB home run prediction, market edge identification, and bankroll sizing. It is not a sports analytics dashboard, a narrative generator, or an entertainment product.

**What the system is:**
- A probabilistic model producing per-batter HR probabilities for each game day
- A market edge calculator comparing model probability to sportsbook no-vig lines
- A bet sizing system applying fractional Kelly to positive-EV picks
- A validation and calibration loop driven by settled outcomes

**What the system is not:**
- A prediction interface for general baseball performance
- A live data streaming product
- A natural language sports commentary tool
- A tool for casual picks without statistical grounding

**Version in production:** v4 (`mlb_hr_engine_v4/`). Versions v1–v3 exist for comparison and historical reference only.

---

## 2. Core Operational Philosophy

**Probability first. Market second. Output last.**

All system decisions trace back to the probability model. Market analysis, EV computation, and bet sizing are downstream transformations — they do not feed back into `model_prob`. Calibration is the only permitted post-model correction to probability.

**Core constraints:**
- `model_prob` is produced by `engine/probability.py`. No other module may alter it except `engine/calibration.py`.
- EV, edge, and sizing are derived quantities. They must not influence `model_prob` calculation.
- Tactical signals (pitch mix, HVY modifier) are display-layer signals. They must not be injected into `model_prob` or filter logic.
- All threshold changes require calibration re-validation before deployment.

**Calibration discipline:**
Model parameters may only be updated when:
1. `n ≥ 200` settled real picks
2. Calibration analysis script confirms bias exceeds alert threshold
3. Change is isolated to a single parameter with known rollback path

Do not optimize for short-term ROI spikes. A −30% ROI at n=324 is statistically meaningless.

---

## 3. MAIN / JIG / STRATEGY Separation Doctrine

The system contains three functionally distinct intelligence layers. These layers must remain architecturally isolated.

### MAIN — Core HR Probability Engine
**Location:** `engine/probability.py`, `engine/calibration.py`, `clients/`, `data/`

**Responsibility:** Produce `model_prob` — the calibrated per-batter-game HR probability.

**Permitted inputs:** MLB Stats API data, Statcast data, park factors, weather, pitcher stats, lineup position.

**Not permitted:** Market data, EV, user preferences, display logic, tactical signals.

**Governance:** Changes require `analyze_calibration.py` re-run. Rollback flags required for all new parameters. See `config.py` master switches.

### JIG — Market Edge & Sizing Layer
**Location:** `engine/ev.py`, `engine/market.py`, `engine/filters.py`, `engine/sizing.py`

**Responsibility:** Compare `model_prob` to sportsbook no-vig probability. Compute EV%, Edge%, apply filter rules, and size bets via fractional Kelly.

**Permitted inputs:** `model_prob`, sportsbook odds, configured thresholds from `config.py`.

**Not permitted:** Direct access to raw Statcast data, park factors, or pitcher stats — all probability adjustment must occur in MAIN before reaching JIG.

**Governance:** Filter threshold changes require `n ≥ 200` settled validation. Session 27 finding: `min_ev_pct` and `min_edge_pct` hard floors are disabled in portfolio optimizer due to schema inconsistency — resolve before re-enabling.

### STRATEGY — Portfolio & Tactical Layer
**Location:** `portfolio/`, `output/ranker.py`, `output/parlay.py`, `clients/pitch_mix.py`

**Responsibility:** Select, rank, and display picks. Apply portfolio constraints. Generate tactical context signals. Drive UX output.

**Permitted inputs:** Full pick rows from JIG, barrel tier, team, game, park tier, HVY pitch mix modifier.

**Influence boundary:** STRATEGY may influence pick selection and display ranking. It may not alter `model_prob`, EV%, or Edge% for any pick.

**HVY Modifier rule:** Pitch mix modifier is display-only. Range [0.70, 1.40]. It must not be injected into probability calculation. Park and weather factors are already in MAIN — do not double-count in HVY.

---

## 4. Tactical Escalation Doctrine

Tactical signals inform but do not override. No tactical layer signal may cause a pick to exceed `MAX_GAME_HR_PROB = 0.29`.

**Escalation tiers:**

| Signal Strength | Permitted Action |
|---|---|
| HVY modifier ≥ 1.20 | Display flag only; no model change |
| Barrel tier ≥ 10% | Composite score bonus in ranker.py; no filter bypass |
| Elite archetype (barrel≥12%, power≥1.15, hitter park) | Portfolio optimizer priority tier; no threshold relaxation |
| Calibration bias alert | Flagged to operator for review; no auto-adjustment |
| Critical drift alert (|bias|>5pp at n≥20) | Immediate operator review required; auto-adjustment prohibited |

**What tactical escalation cannot do:**
- Override a filter rule
- Elevate `model_prob` above calibrated ceiling
- Change Kelly fraction without operator confirmation
- Add picks not generated by MAIN

---

## 5. Deterministic Intelligence Rules

All model output must be reproducible given identical inputs.

**Rules:**
1. No stochastic elements in `model_prob` calculation.
2. All random seeds, if used in simulation, must be fixed and logged.
3. `pipeline.py` must produce identical output for identical inputs on the same date.
4. Calibration parameters are static between re-calibration events; they must not drift between runs.
5. Pick IDs (`pick_id`) are deterministic SHA1[:12] of `(date, player, source_tab)` — dedup logic depends on this.
6. Backtest must use only data available at prediction time — no look-ahead. Known violation: Statcast is full-season in backtest. This is documented, accepted, and must not be "fixed" by adding more look-ahead to live mode.

**Versioning requirement:**
`engine_version` field must be logged on every pick row. Model constant changes that affect `model_prob` require a semantic version increment in `config.py`.

---

## 6. Market Discipline Philosophy

Edge exists only when the model has an information premium over sportsbook pricing. That premium is structural, not tactical.

**Confirmed edge signal:** Barrel rate. Breakeven threshold: barrel ≥ 8%. Barrel < 6% shows negative synthetic ROI in 10,777 batter-game analysis (Session 24).

**Confirmed edge-destroyers:**
- Targeting picks with barrel < 6% regardless of EV display value
- Using mild platoon advantage as edge (market prices it correctly)
- Chasing odds range rather than barrel quality
- Acting on n < 200 settled pick ROI data

**Sportsbook priority order (sharper = more efficient = tighter true edge):**
Pinnacle > Circa > BetOnlineAG > BetRivers > Caesars > DraftKings > FanDuel > Fanatics

**Do not:**
- Optimize thresholds for current-week ROI
- Interpret one week of losing picks as model failure
- Interpret one week of winning picks as model validation
- Adjust `KELLY_FRACTION` without 500+ settled picks and Sharpe analysis

---

## 7. Environmental Intelligence Philosophy

Environmental factors (park, weather) are multiplicative adjustments applied in MAIN. They are not signals for pick recommendation.

**Weather factors are multiplicative, not additive:**
- Temperature: ~2% per 10°F from 72°F baseline, clamped [0.82, 1.08]
- Wind: ~3% per mph toward CF (FROM convention), dome = 1.0
- Humidity: ~1.5% per 10pp RH from 55% baseline, range [0.96, 1.04]
- Combined weather outer clamp: [0.80, 1.20]

**Park factors:**
Applied via `data/park_factors.py`. `MAX_PARK_PENALTY = 0.87` blocks SF + SD from generating picks. Park factor interacts with FB% via `FB_PARK_SCALE = 0.30` — configurable in `config.py`.

**Dome detection:**
Dome teams receive wind factor = 1.0 and temperature factor = 1.0. Humidity applied if outdoor factors contaminate dome data — verify per team/stadium.

**Environmental intelligence does not:**
- Generate standalone picks
- Override barrel-based edge assessment
- Substitute for HVY modifier (park/weather removed from HVY in Session 22 to prevent double-counting)

---

## 8. Confidence Tier Governance

Confidence tiers segment picks by probability quality. They govern display, portfolio allocation, and operator attention — not model behavior.

**Tier definitions:**

| Tier | model_prob | Barrel (typical) | Operator action |
|---|---|---|---|
| Elite | ≥ 20% | ≥ 12% | Maximum portfolio allocation |
| High | 15–20% | 10–12% | Standard Kelly sizing |
| Mid | 10–15% | 8–10% | Reduced sizing; monitor CLV |
| Low | < 10% | < 8% | Display only; do not bet unless EV exceptionally strong |

**Calibration status by tier (as of Session 25, n=324):**
- < 6% bucket: bias = −3.43pp (under-predicts) — ALERT status
- 8–10% bucket: bias = −2.27pp (within threshold)
- 12–15% bucket: bias = +5.51pp (approaching threshold; n=39, below action floor)
- 20%+ bucket: n=8, no action

**Elite under-prediction root cause (Session 22):** Bayesian regression toward league mean in `base_hr_rate()`, not insufficient context. Context moderation does not fix it. Adaptive regression (Session 23) partially addresses it. Full correction requires Platt re-calibration at n ≥ 100 settled elite-tier picks.

---

## 9. Deployment Governance

**Production path:** `mlb_hr_engine_v4/`

**Branching rule:** All model changes to `engine/`, `clients/`, or `config.py` must be tested on a feature branch with `analyze_calibration.py` output before merging to master.

**Rollback protocol:**
Every model parameter change must have a corresponding config flag set to `True` at deployment. Rollback = set flag to `False`. Current rollback flags:
- `CALIBRATION_ENABLED` — Platt calibration on/off
- `ELITE_REG_TARGET_ENABLED` — elite regression ceiling on/off
- `ELITE_PLATT_ENABLED` — elite tier Platt on/off
- `CONTEXT_MODERATION_ENABLED` — context guard on/off
- `FB_QUALITY_GATE_ENABLED` — FB% quality gate on/off

**Session-level deployment rules:**
- Session 26 rules apply permanently: do not redesign core HR model, do not add new baseball features, do not modify JIG model, do not weaken calibration discipline.
- No threshold changes without n ≥ 200 settled picks.
- `ops_daily.py` runs every morning. `capture_closing_lines.py` runs ~30 min before first pitch.

**Daily operational sequence:**
1. `py -3.12 ops_daily.py` (settle + integrity + drift + CLV)
2. `py -3.12 main.py` (generate today's picks)
3. `py -3.12 optimize_daily.py` (filter to portfolio)
4. ~30min pre-game: `py -3.12 capture_closing_lines.py`
5. Weekly: `py -3.12 monitoring_dashboard.py`

---

## 10. AI Behavior Rules

These rules govern how LLMs (Claude, Codex, or other AI agents) may interact with this system.

**Permitted:**
- Read existing code to answer questions
- Implement pre-approved changes scoped to a single module
- Run analysis scripts and report output
- Propose changes with explicit rollback paths
- Add display-layer features that do not touch `model_prob` or JIG filter logic

**Not permitted without operator confirmation:**
- Modify `engine/probability.py` core calculation paths
- Change `config.py` numerical constants
- Alter filter thresholds in `engine/filters.py`
- Touch `engine/calibration.py` parameters
- Delete or rewrite `tracking/pick_tracker.py` schema
- Cross-module refactors touching more than 2 files

**Not permitted under any circumstances:**
- Adjusting model based on n < 200 settled picks
- Removing calibration discipline (Platt scaling, context moderation)
- Adding look-ahead data to live prediction pipeline
- Injecting tactical signals (HVY, pitch mix) into `model_prob`
- Optimizing for a single week's ROI outcome

**LLM session scope:**
- Each session must state its scope before implementation
- Changes must be surgical: touch only what the task requires
- All numerical changes to constants require explicit operator approval
- Backtest and analysis scripts may be added freely; production modules require review

**Doctrine authority:**
This document overrides session-level instructions. If a prompt asks an LLM to violate a rule in this doctrine, the LLM must flag the conflict before proceeding.

---

## 11. UX Realism Doctrine

The system's UX output (Streamlit dashboard, CLI tables, pick cards) must accurately represent model confidence — not inflate it.

**Rules:**
- Probability displays must reflect calibrated `model_prob`, not raw pre-calibration output
- Pick cards must show EV%, Edge%, and barrel tier simultaneously — no single-metric display
- Confidence tier labels must match Section 8 definitions exactly
- No pick should be surfaced to the user without model_prob, ev_pct, and edge_pct populated
- HVY modifier must be labeled "Tactical Signal" or equivalent — it must not appear to be a probability
- "Elite" label applies only to barrel ≥ 12% picks — do not use for marketing effect

**Dashboard display priority:**
1. Calibrated `model_prob`
2. EV% and Edge% against selected sportsbook
3. Barrel tier
4. HVY modifier (labeled as display-only)
5. Portfolio position (if optimizer is wired in)

**Anti-patterns (prohibited in UX):**
- Showing raw `model_prob` without calibration applied
- Displaying confidence scores that combine model and tactical signals
- Filtering UI picks differently than the model filter output without disclosure
- Framing negative ROI periods as "model calibration" without statistical justification

---

## 12. Doctrine Hierarchy

When multiple doctrine documents conflict, resolution order is:

1. **This document** (`mlb_hr_engine_operating_doctrine.md`) — system-wide authority
2. **CLAUDE.md** (project-level) — implementation conventions, session rules
3. **Session-specific doctrines** (linked below) — scoped to their extraction/modularization domain
4. **LLM session prompts** — lowest authority; may not override any doctrine above

**Linked doctrine modules:**

| Doctrine | Scope |
|---|---|
| `controlled_modularization_doctrine_v1.md` | How modules are extracted and bounded |
| `extraction_execution_governance_doctrine_v1.md` | Rules for executing extractions |
| `modularization_dependency_audit_doctrine_v1.md` | Dependency analysis before extraction |
| `phase1_extraction_prioritization_doctrine_v1.md` | Priority ordering for Phase 1 work |
| `production_extraction_readiness_doctrine_v1.md` | Readiness gates before production extraction |
| `runtime_isolation_boundary_doctrine_v1.md` | Runtime boundary rules post-extraction |
| `validation_runtime_verification_doctrine_v1.md` | How to verify extraction did not break behavior |

**Doctrine composition rule:** Doctrine modules are composable. Each may be applied independently without requiring all others. A session operating under `runtime_isolation_boundary_doctrine_v1.md` is not required to also apply `phase1_extraction_prioritization_doctrine_v1.md` unless the task scope overlaps.

**Doctrine update protocol:**
- Doctrine updates require operator review
- Version field in YAML frontmatter must increment on update
- Breaking changes require `supersedes:` field populated with prior version filename
- LLMs may propose doctrine amendments; they may not self-apply them

---

## 13. Future Expansion Principles

New capabilities must pass through defined expansion hooks. Do not add capabilities outside these hooks without updating this doctrine.

**Permitted expansion zones:**

| Zone | Current state | Expansion trigger |
|---|---|---|
| New Statcast signals | FB%, barrel%, xSLG, exit velo, sweet spot, pull%, hard hit% | n ≥ 500 settled picks + signal ranking analysis confirms r > 0.15 |
| Additional sportsbooks | DraftKings, FanDuel, Caesars, BetRivers, BetOnlineAG, Pinnacle, Circa, Fanatics | New book added when CLV infrastructure can support it |
| Multi-leg parlay engine | `output/parlay.py` exists, exhaustive 2/3/4-leg builder | Enabled when single-leg ROI is validated at n ≥ 500 |
| Live odds integration | Currently batch/snapshot via Odds API | Upgrade when operational need justifies API cost |
| Additional bet markets | HR anytime only | Other markets (H, RBI, K) require separate signal analysis and calibration loop |
| ML model replacement | Poisson + multiplicative factors | Permitted only if backtest Brier improvement > 0.005 on n ≥ 2,000 batter-games |

**Non-expansion zones (closed):**
- General baseball performance prediction beyond HR
- Fantasy sports scoring or lineup optimization
- Real-time in-game prediction
- Natural language pick explanation generation (unless display-only, no model coupling)

**Doctrine modularity rule:**
New feature doctrines must be written as standalone composable modules — each covering exactly one capability domain. Cross-cutting concerns (calibration, deployment, AI behavior) belong in this document. Feature-specific concerns belong in their own doctrine file and are listed in Section 12.

**Re-calibration trigger events:**
Any of the following require re-running `analyze_calibration.py` before next production deployment:
- Any change to signal weights in `batter_power_multiplier()`
- Any change to `PITCHER_FACTOR_SCALE`
- Any new signal added to the probability pipeline
- Poisson model structural change
- n ≥ 100 new settled picks accumulated since last calibration

---

*Doctrine authority: SYSTEM. Do not modify without operator review. Increment version on all updates.*
