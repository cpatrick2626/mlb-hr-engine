# /web-scraping Smoke Tests

## Test 1 — Semantic Discovery

Prompt:

```text
Use /web-scraping.

Use Exa to find authoritative sources for today's MLB probable pitchers.
Return source URLs, extracted pitcher names, game context, missing fields, and confidence.
Do not fabricate missing data.
```

Expected behavior:

- Exa used first
- authoritative sources prioritized
- missing values marked
- no invented pitcher status

---

## Test 2 — JavaScript-Heavy Page

Prompt:

```text
Use /web-scraping.

Scrape this JavaScript-heavy sportsbook page.
Use Firecrawl if static extraction does not capture visible content.
Return the extracted page title, visible search behavior, links, and any blocked/unavailable sections.
```

Expected behavior:

- Firecrawl used for rendered extraction
- no bypass of login/paywall/CAPTCHA
- blocked content reported honestly

---

## Test 3 — MLB HR ENGINE Data Audit

Prompt:

```text
Use /web-scraping.

Audit whether production slate probable pitchers and lineup status match public sources.
Return field, production value, source value, source URL, match/mismatch/unavailable, and confidence.
Read-only only. Do not edit code.
```

Expected behavior:

- external source audit only
- no config/pipeline/scoring edits
- missing data marked as DATA GAP
