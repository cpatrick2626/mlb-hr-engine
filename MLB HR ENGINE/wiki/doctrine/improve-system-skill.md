# Improve System Utility Skill

## Status

Active utility doctrine.

## Operational Skill

The operational skill source lives at:

`skills/improve-system/SKILL.md`

The Obsidian note is governance/reference only. It is not the runnable source of truth.

## Purpose

`/improve-system` compounds the operating system over time.

It captures lessons, finds note conflicts, improves skills, mines recent execution history, and identifies missing foundation content.

## Tools

None.

This skill does not require Exa, Firecrawl, APIs, scraping, browser tools, or external services.

## Modes

`/improve-system` has five modes:

1. Audit — find stale, conflicting, or duplicate notes.
2. Skill Review — improve a skill based on recent back-and-forth.
3. Experience — capture a story, win, failure, or lesson.
4. Historical Review — mine recent Claude Code sessions for missed learnings.
5. Foundation — fill in missing foundational content such as brand, audience, offers, and voice.

The assistant should pick the mode from context or ask if unclear.

## Knowledge Base Routing

Use:

`MLB HR ENGINE/knowledge/`

for stable operating knowledge.

Use:

`MLB HR ENGINE/projects/`

for active work and current project lessons.

## Relationship to Other Skills

Use `/web-scraping` when fresh external source discovery or extraction is needed.

Use `/ingest-source` when a specific source needs to be captured into the knowledge base.

Use `/improve-system` when the operating system itself needs to get better.

## Data Integrity Rules

Never fabricate lessons, history, session results, file contents, people, dates, claims, or operator intent.

Use:

`--`

or:

`DATA GAP`

when information is missing.

Clearly separate confirmed findings, inferred patterns, proposed improvements, and open questions.

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

It must preserve:

- MAIN / JIG separation
- HVY display-only doctrine
- TCC orchestration-only doctrine
- no hidden scoring
- no fabricated model inputs

Actual edits require operator authorization.

## Ownership

Claude Code may place or update the skill files after operator authorization.

Obsidian records doctrine, usage, and governance.

Runtime integration requires separate authorization.
