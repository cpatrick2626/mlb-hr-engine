# Advisory Board Seat — MLB Scouting

## Purpose
Matchup feel, handedness/platoon edges, mechanics and form context behind a model rank.

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
| 001 | [[source-001-pitch-mix-and-tactical-doctrine\|Pitch Mix Analysis and JIG Tactical Doctrine]] | internal-doctrine | 2026-06-17 |

## Deferred sources (need /web-scraping)

- Pitch-arsenal platoon split tables (batter vs pitch-type by handedness)
- Park-specific HR zones and spray-chart data
- Pitch-type sequencing and tunneling theory
- Weather + wind modeling frameworks beyond current multipliers
