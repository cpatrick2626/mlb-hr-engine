# PropFinder Comparison and Strategy

**Date:** 2026-07-21

**Status:** Current audited-state reference

**Scope:** Strategy and documentation only; no scoring, payload, pipeline, or configuration changes

## Executive Position

PropFinder and MLB HR ENGINE overlap in baseball data, but they are built for different jobs:

- **PropFinder is a research environment.** It is optimized for broad exploration, historical inspection, pitch-level evidence, flexible time windows, and manual investigation.
- **MLB HR ENGINE is a decision environment.** It is optimized for converting selected inputs into explicit home-run probability, tactical matchup intelligence, ranked threats, escalation states, and operational deployment decisions.

The strategic goal is not to reproduce PropFinder screen for screen. The engine should borrow the research depth that improves operator understanding and future validation while preserving its decision-system identity. Research additions should begin as display and learning tools. They must not affect MAIN probability, JIG tactical scoring, tiers, rankings, or ticket roles until sufficient historical data exists and backtesting supports a separately authorized scoring change.

## Audited Stat Comparison Scorecard

The current audited comparison covers **34 PropFinder reference statistics**.

| Classification | Count | Meaning |
|---|---:|---|
| Matched | 19 | The engine has a directly usable equivalent with a sufficiently aligned meaning. |
| Partial | 3 | The engine covers related territory, but the formula, denominator, window, granularity, or source contract is not fully equivalent. |
| Null | 4 | The payload surface exists, but the value is currently unpopulated. |
| Missing | 8 | No equivalent field or data path is currently available on the audited surface. |
| **Total** | **34** | Complete audited comparison set. |

This is a capability scorecard, not a product-quality score. A matched field does not mean the two systems have equal research depth, and a missing field does not automatically justify adding it to predictive scoring.

## Formula-Contract Findings

### Pull Air% — open contract mismatch

The engine's current Pull Air value is a compound estimate based on the batter's pull rate and airborne-contact rate. PropFinder's research framing treats Pull Air% as an event-derived rate with an explicit batted-ball denominator. These values may point in the same directional-power direction but are not contract-equivalent.

Before treating them as interchangeable, the engine needs a documented contract covering:

- numerator: the exact set of pulled airborne batted-ball events;
- denominator: all batted-ball events or another explicitly named population;
- whether line drives, fly balls, popups, and home runs are included;
- minimum sample and fallback behavior;
- source, season/window, handedness split, and percentage scale.

Until that contract is resolved and validated, Pull Air comparisons should be labeled as partial rather than exact.

### HR/FB% — resolved in the current audited state

The earlier HR/FB field used a mismatched rate contract. **That issue was already resolved during the 2026-07-21 session.** The engine now populates true batter HR/FB as:

`season_hr / (season_hr + air_outs) × 100`

The old denominator-mismatch finding remains useful as audit history, but it is **not an open implementation gap** in this strategy. Future documentation and display work should preserve the corrected true HR/FB meaning and must not repoint the field to HR per plate appearance.

## Where PropFinder Is Ahead

### Research depth

PropFinder provides a deeper exploratory workspace around the underlying evidence. An operator can inspect the components behind a matchup instead of relying primarily on summarized outputs.

### Pitch-type tables

Pitch-type usage, results, and matchup tables support direct investigation of how a batter performs against the pitches a specific pitcher actually throws. The engine has tactical arsenal intelligence, but not the same breadth of transparent research tables.

### Recent-window analysis

PropFinder supports more flexible recent windows. This makes it easier to compare season baselines with shorter-term changes in contact, approach, pitch usage, and results without presenting the short window as automatically predictive.

### Pitch history

Historical pitch sequences and pitch-level outcomes expose how an arsenal has changed and how prior contact was produced. This is more informative than a single season-level summary when researching repertoire drift or recurring mistake locations.

### Event-level Statcast access

Event-level batted-ball and pitch data enables exact denominator contracts, custom windows, deep-contact studies, and retrospective validation. The engine currently relies more heavily on aggregated inputs and operational summaries.

### Zone views

Location and zone visualizations make mistake exposure, damage zones, and batter-pitcher location overlap directly inspectable. The engine does not currently have the required Statcast zone dataset for a credible Zone Collision layer.

## Where MLB HR ENGINE Is Ahead

### Explicit HR probability

MAIN produces an explicit model-driven home-run probability and threat ranking. PropFinder helps research a prop; the engine converts inputs into a decision-ready probability surface.

### MAIN/JIG intelligence separation

The engine preserves two distinct systems:

- **MAIN:** quantitative, model-driven HR probability and threat ranking (`SCAN -> QUALIFY -> DEPLOY`).
- **JIG:** tactical, matchup-driven exploit intelligence and `jigScore` ordering (`MATCHUP -> CONFIRM -> EXPLOIT`).

Research-layer additions must not merge these systems. JIG may use or display matchup evidence within its authorized contract, but it must not redefine MAIN probability. MAIN model tier shown in a JIG context remains inherited probability context, not a JIG-native tactical tier.

### Environmental integration

The engine incorporates park and weather context into its operational view of home-run conditions rather than leaving those factors as disconnected research tabs.

### Pitcher fatigue

Pitcher rest and fatigue are integrated into the engine's current probability workflow, creating a decision advantage beyond static season lines.

### Ranking and escalation

The engine converts inputs into ranked HR threats, tiers, tactical order, vulnerability states, and escalation cues designed for rapid slate scanning.

### Ticket roles

The engine adds operational role classification for constructing and reviewing tickets. These roles are separate from MAIN probability and JIG tactical scoring and should remain governed by their existing contract.

## Improvement Opportunities

### 1. Formalize formula contracts

Create a source-of-truth contract for every displayed or modeled statistic: name, numerator, denominator, source, time window, split, unit, null behavior, and permitted consumers. Resolve Pull Air% before claiming direct parity. Preserve the already-resolved true HR/FB contract.

### 2. Build the historical data warehouse early

Persist event-level and daily snapshot data before adding predictive features. The warehouse is a prerequisite for exact research views, replay, stable denominator calculations, backtesting, calibration, shadow scoring, and drift analysis. It should begin in parallel with formula-contract work rather than being deferred until after UI features.

### 3. Close display-layer gaps without changing scoring

Populate useful null fields where authoritative sources exist, add selected missing fields as display-only research context, and clearly label source/window/sample. Display availability must not silently create a scoring dependency.

### 4. Surface stranded pitcher-arsenal data

Expose already-available arsenal and pitch-mix evidence in transparent research views before inventing new scores. Operators should be able to see the evidence behind matchup labels and tactical conclusions.

### 5. Add a pitcher research layer

Develop display-first tools for arsenal drift, pitch history, deep-contact allowed, mistake exposure, and pitcher HR threat profiles/archetypes. Treat archetypes as descriptive research classifications until outcome data validates predictive use.

### 6. Add a zone layer only when the data contract exists

Zone Collision should compare batter damage zones with pitcher location and mistake zones, but it requires new event-level Statcast zone data, stable coordinate normalization, handedness handling, and sample rules. Do not infer zone intelligence from aggregate statistics.

### 7. Validate before scoring

Once the warehouse has accumulated representative data, backtest candidate signals, measure incremental value beyond the existing model, run shadow scores, and audit stability by season, handedness, pitch type, and sample size. Only then should a separately authorized scoring proposal be considered.

## Strategic Guardrails

- Display and learning first; scoring only after backtesting.
- Pull the warehouse forward as an early prerequisite for all predictive work.
- Never fabricate missing pitch-level or zone data.
- Keep MAIN probability and JIG tactical intelligence separate.
- Do not alter model probability, tiers, rankings, ticket roles, or payload contracts through research UI work.
- Prefer transparent evidence and explicit sample context over new composite scores.
- Treat current comparison findings as an audited planning baseline, not proof that every PropFinder feature should be copied.
