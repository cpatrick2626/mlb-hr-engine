# /web-scraping

## Purpose

`/web-scraping` is a utility skill for source discovery, webpage extraction, and structured web research workflows.

It uses:

- **Exa** for semantic search, source discovery, and finding relevant pages when the exact URL is unknown.
- **Firecrawl** for JavaScript-heavy pages, rendered pages, dynamic websites, SPAs, crawl jobs, and structured extraction from difficult pages.

This skill is designed for tactical, source-backed research. It must not fabricate missing data.

---

## When to Use

Use `/web-scraping` when the task requires:

- discovering relevant sources
- scraping public webpage content
- extracting structured fields from pages
- auditing data from external sites
- comparing multiple web sources
- collecting URLs, snippets, metadata, or page text
- validating whether a production data feed matches public references

For MLB HR ENGINE, use this skill for read-only external data checks such as:

- probable pitchers
- lineup status
- MLB schedule context
- weather and park environment references
- player news / injuries
- Statcast / Savant references
- sportsbook search-link behavior
- HR-relevant matchup references

---

## Tool Routing

### Use Exa First When

Use Exa when:

- the user asks for semantic discovery
- the target source is not already known
- multiple relevant sources need to be found
- query intent matters more than exact keyword matching
- you need source candidates before scraping
- you need relevant pages, articles, docs, or references

Expected Exa outputs:

- source title
- source URL
- relevance rationale
- extracted snippet or summary
- publication/update date if available
- confidence level

---

### Use Firecrawl When

Use Firecrawl when:

- the page is JavaScript-heavy
- the page is a SPA
- static fetch misses visible content
- rendered HTML is required
- the page needs crawling beyond one URL
- structured extraction is needed
- content is behind client-side rendering
- Exa finds the page, but page contents require rendered scraping

Expected Firecrawl outputs:

- requested URL
- final resolved URL
- extracted markdown/text
- structured fields if requested
- crawl depth if used
- pages crawled
- extraction warnings
- missing fields

---

## Routing Pattern

Default workflow:

1. Clarify the target data fields.
2. Use Exa to discover or rank source candidates.
3. Select the most authoritative sources.
4. Use Firecrawl only for pages that require rendered extraction or structured scraping.
5. Normalize results into a source-backed output.
6. Mark missing, blocked, stale, or ambiguous data clearly.
7. Never invent values.

---

## Data Integrity Rules

Never fabricate:

- player status
- lineup status
- probable pitcher status
- Statcast values
- odds
- sportsbook availability
- weather
- injuries
- pitch mix
- HR probability
- confidence
- matchup tier
- timestamps

If data is missing, use:

`--`

or:

`DATA GAP`

If a source is blocked, stale, unavailable, or ambiguous, report that directly.

---

## MLB HR ENGINE Rules

This skill is read-only unless explicitly authorized otherwise.

It must preserve:

- MAIN / JIG separation
- HVY display-only doctrine
- `config.py` source-of-truth boundaries
- `pipeline.py` canonical data assembly boundaries
- no hidden scoring
- no fabricated model inputs
- no invented external data
- no sportsbook-clone behavior
- no production logic edits unless separately authorized

For MLB HR ENGINE audits, output should identify:

- field checked
- source URL
- extracted value
- production value if provided
- match / mismatch / unavailable
- confidence
- recommended next action

---

## Recommended Output Format

```md
## /web-scraping Result

### Objective
...

### Sources Checked
| Source | URL | Method | Status | Notes |
|---|---|---|---|---|

### Extracted Fields
| Field | Value | Source | Confidence |
|---|---:|---|---|

### Data Gaps
| Field | Reason |
|---|---|

### Findings
...

### Recommended Next Action
...
```

---

## Environment Requirements

The runner must provide API keys through environment variables or secure secret storage.

Recommended environment variables:

```bash
EXA_API_KEY=...
FIRECRAWL_API_KEY=...
```

Never commit API keys, secrets, tokens, cookies, or `.env` files.

---

## Safety / Access Boundaries

Do not bypass paywalls, logins, CAPTCHAs, robots restrictions, or access controls.

Do not scrape private data.

Do not store secrets.

Do not commit scraped datasets unless the operator explicitly authorizes it.

Do not run large crawls without explicit scope.

Prefer small, targeted, rate-conscious extraction.
