# Advisory Board Seat — Parlay Construction

## Purpose
Correlation-aware ticket construction, role usage, stake discipline, what makes a ticket a pass.

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
| 001 | [[source-001-ticket-roles-doctrine\|Ticket Roles Doctrine]] | internal-doctrine | 2026-06-17 |

## Deferred sources (need /web-scraping)

- Kelly stake sizing per role
- Correlation between role pairings (same-game, same-lineup)
- Devig / no-vig pricing integration with roles
- Leg-count compounding math
