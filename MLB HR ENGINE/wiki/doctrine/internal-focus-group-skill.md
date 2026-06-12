# Internal Focus Group Utility Skill

## Status

Active utility doctrine.

## Operational Skill

The operational skill source lives at:

`skills/internal-focus-group/SKILL.md`

The Obsidian note is governance/reference only. It is not the runnable source of truth.

## Purpose

`/internal-focus-group` tests ideas before launch.

It lets the operator ask one person, a subset, or a full panel for honest product/user feedback based on ingested notes, interviews, transcripts, feedback, or defined persona material.

## Canonical Knowledge Route

Focus-group material lives at:

`MLB HR ENGINE/knowledge/focus-group/{name}/`

Do not use:

`focus-ygroup/`

## Setup Process

1. Identify real people or explicitly named internal personas.
2. Run `/ingest-source` or `/ingest-resource` on their notes, interviews, transcripts, or feedback.
3. Save material under `MLB HR ENGINE/knowledge/focus-group/{name}/`.
4. Use `/internal-focus-group` to test a launch item, app change, workflow, copy, or idea.
5. Synthesize agreements, disagreements, risks, and what should change before shipping.

## Identity Boundary

This skill must not fabricate person history, quotes, preferences, private opinions, or direct feedback.

If no source material exists for a person, return:

`DATA GAP`

## Relationship to Other Skills

- Use `/ingest-source` to add people.
- Use `/web-scraping` only when public source discovery or source extraction is required.
- Use `/ask-the-board` for expert-style strategic advice.
- Use `/internal-focus-group` for product/user feedback before launch.
- Use `/improve-system` when repeated feedback reveals durable system lessons.

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

Protected-surface changes require audit-first workflow.

## Ownership

Claude Code may place or update the skill files after operator authorization.

Obsidian records doctrine, usage, and governance.

Runtime integration requires separate authorization.
