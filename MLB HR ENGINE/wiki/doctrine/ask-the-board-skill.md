# Ask the Board Utility Skill

## Status

Active utility doctrine.

## Operational Skill

The operational skill source lives at:

`skills/ask-the-board/SKILL.md`

The Obsidian note is governance/reference only. It is not the runnable source of truth.

## Purpose

`/ask-the-board` is a Board of Advisors decision skill.

It helps the operator make stronger decisions by selecting relevant expert-inspired advisor lenses, giving each advisor-style take, flagging agreement/disagreement, identifying hidden risk, and synthesizing what the operator should actually do.

## 4-Step Workflow

1. Identify the experts.
2. Ingest their training data with `/ingest-source`.
3. Create the `/ask-the-board` skill.
4. Ask the board a question with `/ask-the-board`.

## Default Board

1. Billy Walters-inspired market discipline lens
2. Bill Benter-inspired quant edge lens
3. Marty Cagan-inspired product strategy lens
4. John Carmack-inspired engineering clarity lens
5. Jakob Nielsen / NNGroup-inspired UX lens

## Identity Boundary

This skill must not impersonate real people.

It must not fabricate direct quotes, private opinions, current positions, or personal advice from any expert.

Use advisor-style lenses only.

## Knowledge Base Route

Board source material should be ingested into:

`MLB HR ENGINE/knowledge/advisory-board/`

Use `/ingest-source` for source capture.

Use `/web-scraping` first if source discovery or rendered extraction is needed.

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

## Gambling Boundary

The skill may evaluate betting logic and risk, but must not guarantee outcomes, encourage reckless staking, fabricate odds, or present gambling as risk-free.

## Ownership

Claude Code may place or update the skill files after operator authorization.

Obsidian records doctrine, usage, and governance.

Runtime integration requires separate authorization.
