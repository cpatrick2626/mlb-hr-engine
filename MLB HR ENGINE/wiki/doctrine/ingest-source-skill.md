# Ingest Source Utility Skill

## Status

Active utility doctrine.

## Operational Skill

The operational skill source lives at:

`skills/ingest-source/SKILL.md`

Alias:

`/ingest-resource`

The Obsidian note is governance/reference only. It is not the runnable source of truth.

## Purpose

`/ingest-source` captures articles, YouTube links, transcripts, PDFs, and notes into the knowledge base with:

- correct folder routing
- source/date/key people/key concepts summary block
- first-mention `[[wikilinks]]`
- durable markdown structure
- explicit data-gap handling

## Knowledge Base Root

The knowledge base root is:

`MLB HR ENGINE/`

Default routes:

- `MLB HR ENGINE/knowledge/`
- `MLB HR ENGINE/projects/`

## Routing Doctrine

Use `knowledge/` for stable information:

- frameworks
- voice
- people processes
- evergreen references
- reusable methods
- durable doctrine

Use `projects/` for active work:

- videos
- newsletters
- launches
- campaigns
- implementation work
- current production/project materials

## Relationship to /web-scraping

Use `/web-scraping` first when source discovery or rendered extraction is required.

Use `/ingest-source` after the source content is available and needs to be routed, summarized, linked, and stored.

## Data Integrity Rules

Never fabricate source metadata, transcripts, claims, people, dates, quotes, or project status.

Use:

`--`

or:

`DATA GAP`

when data is missing or unavailable.

## Protected MLB HR ENGINE Boundaries

This skill must not modify:

- `config.py`
- `pipeline.py`
- MAIN probability
- JIG scoring
- HVY logic
- calibration
- routing
- session state
- cache ownership
- frontend production behavior
- deployment configuration

This skill may create knowledge-base notes only when explicitly asked to ingest a source.

## Ownership

Claude Code may place or update the skill files after operator authorization.

Obsidian records doctrine, usage, and governance.

Runtime integration requires separate authorization.
