# Web Scraping Utility Skill

## Status

Active utility doctrine.

## Operational Skill

The operational skill source lives at:

`skills/web-scraping/SKILL.md`

The Obsidian note is governance/reference only. It is not the runnable source of truth.

## Purpose

`/web-scraping` defines the standard routing pattern for source-backed web research:

- Exa for semantic source discovery.
- Firecrawl for JavaScript-heavy, rendered, SPA, crawl, or structured extraction workflows.

## MLB HR ENGINE Use Cases

Use for read-only audits of:

- MLB probable pitchers
- lineup status
- weather / park environment references
- player news and injuries
- Statcast / Savant references
- sportsbook link/search behavior
- external data source validation

## Data Integrity Rules

Never fabricate scraped values.

If a value is missing, blocked, stale, or unavailable, report:

`--`

or:

`DATA GAP`

Do not invent:

- player status
- lineup status
- probable pitcher status
- Statcast values
- odds
- weather
- pitch mix
- HR probability
- matchup confidence
- model tiers

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

External web data may support audits, but must not silently overwrite model or production source-of-truth values.

## Environment Requirements

The runner needs secure API key configuration, typically:

```bash
EXA_API_KEY=...
FIRECRAWL_API_KEY=...
```

Never commit secrets or `.env` files.

## Ownership

Claude Code may place or update the skill files after operator authorization.

Obsidian records doctrine, usage, and governance.

Runtime integration requires separate authorization.
