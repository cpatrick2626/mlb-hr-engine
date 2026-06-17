# Advisory Board Seat — Data Integrity

## Purpose
Input validation before any explanation; handedness/HR/pitch-metric sanity; enforces -- / DATA GAP over fabrication.

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
| 001 | [[source-001-tracking-infrastructure-overhaul\|Tracking Infrastructure Overhaul]] | internal-session | 2026-06-17 |

## Deferred sources (need /web-scraping)

- Idempotency guarantees for settlement re-runs
- Schema validation frameworks (Pandera, Great Expectations)
- Automated data-quality monitoring patterns
