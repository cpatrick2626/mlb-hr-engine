# Session: Tier Ranking Foundation Completion

Date: 2026-06-11
Agent: Claude Code
Owner: Operator
Project: MLB HR ENGINE — OPERATIONS
Room: Tier Ranking Room
Risk Class: LOW
Phase: Documentation only

---

## Scope

This session documents completion of the Tier Ranking Room foundation.

No runtime files were modified in this documentation session.
No frontend files were modified in this documentation session.
No backend, API, pipeline, config, or `app.py` files were modified.
No commit was created in this documentation session.
No push was performed in this documentation session.

---

## Completed Commits

The following commits were delivered and are present on `origin/main` prior to this session:

| Commit | Message | What it delivered |
|--------|---------|-------------------|
| `1b46e48` | `fix(app): migrate main tier displays to full slate tiers` | Tier vocabulary migration — MAIN surfaces now use APEX/ELITE/EDGE/SIGNAL/WATCH/COLD |
| `394172c` | `fix(app): migrate jig displays to model tier labels` | JIG MODEL TIER migration — JIG surfaces label tier as MODEL TIER, not TIER |
| `c00cf05` | `fix(frontend): clarify jig model tier labels` | Frontend JIG model tier label cleanup |
| `3de3d89` | `docs(doctrine): clarify jig tier display inheritance` | Doctrine: JIG row.tier inherits from MAIN, not JIG-native |
| `f13b02f` | `fix(api): read tier thresholds from config` | API reads `FS_TIER_THRESHOLDS` from `config.py` — market isolation enforced at config boundary |
| `10b1d25` | `feat(ranking): stamp model tier rank` | `model_tier_rank` foundation — field stamped on each row as `<TIER> #<N>` |
| `3149d18` | `feat(app): show model tier rank on main surfaces` | APEX #1 / ELITE #1 display on MAIN operator surfaces |
| `9231895` | `docs(doctrine): establish primary ranking doctrine` | Primary Ranking Doctrine codified in `main-model-doctrine.md` and `tier-vocabulary.md` |
| `61137c9` | `feat(app): add apex reason stack` | APEX Reason Stack Phase 1 — HR threat drivers displayed on APEX-tier rows |
| `de2fb52` | `fix(app): refine apex reason stack badges` | Reason Stack Phase 1.5 — badge visual cleanup and refinement |

---

## Final Doctrine

### Primary Ranking Doctrine

**`model_tier_rank` = HR Threat Rank. Primary ranking is pure model probability. No market data contaminates primary rank.**

- Established by commit `9231895` and operator decision 2026-06-11.
- Authoritative source: `wiki/doctrine/main-model-doctrine.md` (Primary Ranking Doctrine section).

### APEX #1 — What It Means

- Highest engine-estimated HR probability among all APEX-tier batters in the current slate.
- Pure Poisson-derived model output from `pipeline.py`.
- Reflects Statcast inputs (Barrel%, ISO, HR/FB, xSLG), pitcher vulnerability (HR/9, Barrel% Allowed, xFIP), and environmental multipliers (platoon, park, wind, temp).
- Nothing about market conditions, odds, or EV enters this rank.

### APEX #1 — What It Does NOT Mean

- Not "best bet"
- Not "highest EV"
- Not "highest edge percentage"
- Not "most favorable odds"
- Not "maximum recommended bet size"
- Not a guarantee of HR — it is a probability estimate

### Market Isolation Doctrine

- Odds, EV, edge, and sportsbook lines are **display-only** on all surfaces.
- They never influence `model_prob`, `model_tier_rank`, tier classification, or the primary sort key.
- `FS_TIER_THRESHOLDS` sourced from `config.py` exclusively — not derived from market lines.
- **Bet Value Rank (Deploy Score)** is deferred and not yet implemented. When added, it must be additive-only, operator-selectable, and must not replace primary HR Threat Rank.

### JIG Separation

- JIG remains separate and tactical.
- JIG `row.tier` inherits from MAIN via shallow copy — it reflects MAIN model probability context, not JIG tactical confidence.
- No `jigTier` field exists. JIG tactical priority is determined by `jigScore` and JIG sort order only.
- JIG is excluded from Bet Value Rank (Deploy Score) when eventually implemented.

---

## Final Runtime Behavior

### `model_tier_rank` Stamping

- Each row in `pipeline.py` output carries `model_tier_rank` as `<TIER> #<N>`.
- Example: `APEX #1`, `APEX #2`, `ELITE #1`, `EDGE #3`.
- Rank is per-tier ordinal by descending `model_prob` within each `FS_TIER_THRESHOLDS` band.
- Displayed on MAIN operator surfaces.

### APEX Reason Stack

- **Phase 1** (`61137c9`): APEX-tier rows show a reason stack explaining HR threat drivers.
  - Drivers are pulled from the underlying Statcast and environmental inputs.
  - Reason stack communicates the "why" behind high model probability in APEX territory.
  - Reason stack is HR threat explanation only — not EV justification, not bet recommendation.
- **Phase 1.5** (`de2fb52`): Badge visual cleanup and refinement.
  - Reason badges refined for clarity and visual consistency.
  - No logic or signal changes — display only.

### Tier Labels by Surface

| Surface | Tier Label | Source |
|---------|------------|--------|
| MAIN Full Slate | TIER | `row.tier` → APEX/ELITE/EDGE/SIGNAL/WATCH/COLD |
| JIG Full Slate | MODEL TIER | `row.tier` inherited from MAIN |
| JIG Builder | MODEL TIER | Same `row.tier` inheritance |

---

## Reason Stack Status

| Phase | Status | Commits |
|-------|--------|---------|
| Phase 1 — APEX drivers display | **Complete** | `61137c9` |
| Phase 1.5 — Badge cleanup | **Complete** | `de2fb52` |
| Phase 2 — Not yet defined | **Deferred** | — |

Reason Stack scope: APEX-tier rows only. Explains HR threat drivers. Does not display EV, edge, or market signals.

---

## Repo State at Documentation Time

- Branch: `main`
- Most recent commit: `de2fb52` — `fix(app): refine apex reason stack badges`
- Tier Ranking foundation commits all present and pushed on `origin/main`
- Working tree: clean

---

## Next Phase — Live APEX Trust Review

**No further ranking changes until sufficient live observations are collected.**

- Observe APEX #1 through APEX #N predictions against live game outcomes.
- Record hit rate, tier distribution, and calibration across observed slates.
- Do not modify `FS_TIER_THRESHOLDS`, `model_tier_rank` logic, or Reason Stack signal weights based on small samples.
- Operator rule: no threshold or calibration changes from n<200 settled real picks without explicit authorization.
- When observations accumulate, initiate a calibration review session as a separate authorized assignment.

---

## Invariants Preserved

The following were explicitly confirmed unchanged by all Tier Ranking Room commits:

- `api/main.py` — no ranking logic changes
- `pipeline.py` — probability construction unchanged
- `engine/*` — model computation unchanged
- MAIN probability (`model_prob`) — unchanged
- JIG scoring (`jigScore`) — unchanged
- Calibration / Platt parameters — unchanged
- `MIN_QUAL_PROB` — unchanged
- Top Targets filter — unchanged
- No `jigTier` introduced
- No composite MAIN/JIG blend introduced

---

## Files Touched By This Documentation Session

- `MLB HR ENGINE/wiki/log.md`
- `MLB HR ENGINE/wiki/doctrine/build-log-and-spec-status.md`
- `MLB HR ENGINE/wiki/sessions/2026-06-11-tier-ranking-foundation-completion.md`
- `MLB HR ENGINE/wiki/sessions/_Index_of_sessions.md`

---

## Cross-References

- [[wiki/doctrine/main-model-doctrine|main-model-doctrine]] — Primary Ranking Doctrine authoritative source
- [[wiki/doctrine/tier-vocabulary|tier-vocabulary]] — APEX/ELITE/EDGE vocabulary and separation rules
- [[wiki/doctrine/main-jig-separation|main-jig-separation]] — JIG row.tier inheritance doctrine
- [[wiki/sessions/2026-06-10-option-a-tier-threshold-production-validation|2026-06-10-option-a-tier-threshold-production-validation]] — prior session: Option A thresholds validated in production
