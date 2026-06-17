# Advisory Board Seat — HR Prediction

## Purpose
Plain-language explanation of HR threat and the dominant drivers behind a tier placement (narrates model_prob, never computes it).

## Grounding
This is an expert-INSPIRED method lens. It does NOT impersonate any real person,
fabricate quotes, opinions, or current positions. Grounded only in public methods
and ingested public source material.

## Ingestion
Capture sources here via `/ingest-source`. Each source records:
- source
- source type
- date
- key people
- key concepts
- decision principles / frameworks
- direct relevance to this seat
- related [[wikilinks]]
Missing fields → `--` or `DATA GAP`. Never fabricate.

## Read-only / scope invariants this seat carries
- Read-only over pipeline.py output. Never recomputes model_prob, alters tiers, or folds signals into MAIN.
- config.py is source of truth for thresholds/constants.
- MAIN / JIG separation; HVY display-only.
- Missing data → `--` / `DATA GAP`.

## Ingested sources

| ID | Title | Type | Date |
|----|-------|------|------|
| 001 | [[source-001-engine-modeling-method\|Engine Modeling Method]] | internal-doctrine | 2026-06-17 |

## Deferred sources (need /web-scraping)

- Statcast expected-stats methodology (xSLG, xwOBA derivation)
- Poisson vs empirical-Bayes calibration for low-HR-rate batters
- Platoon split sample-size stabilization rates
- Park factor construction methodology
