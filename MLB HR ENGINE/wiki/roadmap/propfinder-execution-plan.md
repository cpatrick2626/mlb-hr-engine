# PropFinder-Informed Execution Plan

**Date:** 2026-07-21

**Status:** Current audited-state roadmap

**Source:** Distilled from `wiki/reference/propfinder-comparison-strategy.md`

**Scope:** Sequencing guidance only; no scoring, payload, pipeline, configuration, or runtime authorization

## Objective

Add the research depth that can improve MLB HR ENGINE without turning it into a generic research dashboard or allowing unvalidated signals to affect decisions. The sequence is deliberately **display/learning-first**. Predictive use begins only after the historical warehouse contains enough representative data for backtesting and shadow evaluation.

## Sequencing Doctrine

1. Start formula contracts and the historical data warehouse together.
2. Use those foundations to build trustworthy display and research layers.
3. Add pitcher research before zone collision because much of its evidence can use existing or earlier-acquired data.
4. Add Zone Collision only after the required event-level Statcast zone data and coordinate contracts exist.
5. Backtest and shadow-score only after the warehouse has accumulated adequate history.
6. Consider scoring changes only through a separate audit and explicit operator authorization.

The warehouse is not a late analytics enhancement. It is an **early prerequisite for all predictive work** and should run in parallel with formula-contract cleanup.

## Phase 1 — FOUNDATION

### 1A. Formula contracts

Define a canonical contract for every comparison statistic:

- canonical name and operator-facing label;
- numerator and denominator;
- source and retrieval method;
- unit and percentage scale;
- season, rolling window, and handedness split;
- minimum sample and fallback/null behavior;
- payload/display consumers;
- permitted scoring consumers, if any.

Priority actions:

- Resolve the open Pull Air% contract mismatch between the engine's compound estimate and an event-derived pulled-air rate.
- Record HR/FB% as **resolved on 2026-07-21** and preserve true HR/FB as `season_hr / (season_hr + air_outs) × 100`.
- Classify the remaining 34-stat audit set as 19 matched, 3 partial, 4 null, and 8 missing until a new audit changes the baseline.
- Prevent labels from implying equivalence where formula, denominator, window, split, or granularity differs.

### 1B. Historical data warehouse — begin early and run in parallel

Design and start the warehouse alongside formula-contract work. Capture enough source provenance to reproduce every research value and later test every predictive hypothesis.

Minimum capabilities:

- immutable or versioned daily slate snapshots;
- event-level Statcast pitch and batted-ball records where authorized and available;
- player, game, pitcher, batter, handedness, pitch-type, zone, and timestamp keys;
- source, retrieval time, season/window, and formula-version metadata;
- outcome settlement suitable for replay and backtesting;
- missingness and sample-size tracking;
- stable joins between pregame features and postgame outcomes.

Foundation exit criteria:

- formula contracts are documented for the first display-layer fields;
- HR/FB remains correctly defined and Pull Air is not mislabeled as exact parity;
- warehouse ingestion and retention can support reproducible historical queries;
- no new field has entered MAIN or JIG scoring through this phase.

## Phase 2 — DISPLAY LAYER

Use the foundation to improve transparency without changing decision logic.

### Populate null fields

- Identify authoritative sources for the four currently null comparison fields.
- Populate only when source, denominator, window, sample, and fallback behavior are explicit.
- Show unavailable values honestly; never fabricate or substitute an unlabeled proxy.

### Add display-only fields

- Prioritize missing or partial fields that materially help HR research.
- Label source, time window, handedness context, and sample size.
- Keep every new field display-only unless a later validation and authorization stage promotes it.

### Surface stranded pitcher-arsenal data

- Expose existing pitch-mix and arsenal evidence that is already computed or fetched but not visible.
- Prefer transparent pitch-type tables and supporting facts over another composite score.
- Keep MAIN and JIG behavior unchanged: MAIN remains probability-driven; JIG remains tactical and matchup-driven.

Display-layer exit criteria:

- high-value null and missing fields have trustworthy display contracts;
- existing arsenal evidence is visible and traceable;
- UI labels do not overstate confidence or predictive validity;
- no changes have been made to scoring, rankings, tiers, or ticket roles.

## Phase 3 — PITCHER RESEARCH LAYER

Build a research workspace around pitcher change and damage exposure.

### Arsenal drift

- Compare current pitch usage, velocity, movement, and results with season and longer baselines.
- Separate real repertoire change from small-sample noise.

### Pitch history

- Provide pitch-level or appearance-level history with date, count, pitch type, location, velocity, and outcome where available.
- Make the selected window and sample visible.

### Deep-contact analysis

- Track barrels, hard-hit airborne contact, exit velocity, launch angle, and extra-base/HR outcomes allowed by pitch type and handedness.
- Preserve event-level denominators.

### Mistake exposure

- Identify pitches left in damage-prone locations using explicit zone definitions.
- Present this as observed exposure, not a hidden predictive score.

### HR threat profiles and archetypes

- Create descriptive pitcher profiles such as velocity-loss risk, fastball damage exposure, hanging-breaking-ball risk, or platoon-sensitive vulnerability.
- Keep archetypes display/learning-only until backtests demonstrate stability and incremental predictive value.

Pitcher-layer exit criteria:

- research findings are reproducible from warehouse data;
- every trend carries window and sample context;
- descriptive archetypes are not used by MAIN probability or JIG scoring.

## Phase 4 — ZONE LAYER

### Zone Collision

Create a research view that compares batter damage zones with pitcher usage, location, and mistake zones. This phase **requires new Statcast zone data** and must not start from aggregate approximations.

Required prerequisites:

- event-level plate coordinates and pitch outcomes;
- normalized zone geometry across batter handedness and data-source conventions;
- clear definitions for heart, shadow, chase, waste, and custom damage cells;
- batter damage maps by pitch type and handedness;
- pitcher location and mistake maps by pitch type and handedness;
- sample thresholds, smoothing rules, and missing-data behavior;
- replayable warehouse history for testing whether collisions preceded HR outcomes.

Zone-layer exit criteria:

- coordinate and denominator contracts are documented;
- maps can be reproduced from stored events;
- Zone Collision remains an evidence surface, not an unvalidated scoring input.

## Phase 5 — VALIDATION / SCORING

This phase begins only after the warehouse contains sufficient representative history. Availability of a new statistic is not evidence that it improves prediction.

### Backtest

- Measure each candidate signal against settled HR outcomes.
- Test incremental value beyond existing MAIN inputs rather than only standalone correlation.
- Audit leakage, missingness, selection bias, season drift, handedness, pitch type, and sample-size sensitivity.
- Compare calibration, discrimination, stability, and operational usefulness.

### Shadow-score

- Run candidate formulas without changing production probability, rankings, JIG order, tiers, or ticket roles.
- Store shadow outputs and versions in the warehouse.
- Compare shadow recommendations with the live system over a meaningful sample.

### Scoring authorization gate

Only after backtesting and shadow evaluation may a candidate proceed to a separate high-risk scoring audit. Any execution would require explicit operator authorization and must preserve:

- MAIN as the quantitative HR probability engine;
- JIG as the separate tactical matchup workspace;
- no hidden scoring from display fields;
- unchanged tier, ranking, role, payload, and configuration contracts unless specifically approved.

Validation/scoring exit criteria:

- evidence supports a stable, incremental improvement;
- the proposed consumer is explicit: MAIN, JIG, display-only, or neither;
- a protected-surface audit is complete;
- the operator has separately authorized any scoring implementation.

## Recommended Immediate Next Action

Begin **Phase 1A: Formula Contracts** while scoping **Phase 1B: Historical Data Warehouse** in parallel. The first formula-contract deliverable should lock the Pull Air% numerator/denominator and record true HR/FB as resolved. No scoring change is part of that work.
