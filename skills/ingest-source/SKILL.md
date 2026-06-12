# /ingest-source

Alias: `/ingest-resource`

## Purpose

`/ingest-source` captures useful external or internal material into the knowledge base with clean routing, summary metadata, cross-links, and durable note structure.

It can ingest:

- articles
- YouTube links
- transcripts
- PDFs
- pasted notes
- meeting notes
- research notes
- strategy documents
- project references

This skill does not fabricate missing details. If source data is unavailable, blocked, incomplete, or unclear, mark it directly.

---

## Knowledge Base Root

Default knowledge base root:

`MLB HR ENGINE/`

Default routing folders:

- `MLB HR ENGINE/knowledge/`
- `MLB HR ENGINE/projects/`

Create folders if they do not exist.

---

## Folder Routing

### Route to `knowledge/` when the source is stable

Use `knowledge/` for evergreen or reusable information:

- frameworks
- operating principles
- voice and tone guidance
- people processes
- decision frameworks
- reusable strategy
- reference doctrine
- durable research
- stable tutorials
- long-term notes

### Route to `projects/` when the source is active work

Use `projects/` for live or time-bound work:

- videos
- newsletters
- launches
- campaigns
- current project work
- implementation plans
- production validation notes
- active experiments
- release materials
- room/task outputs

If unclear, choose `projects/` for active execution material and `knowledge/` for stable reference material.

---

## Required Note Header

Every ingested note must begin with this summary block:

```md
---
source: "<source URL, file name, or pasted note>"
source_type: "<article | youtube | transcript | pdf | note | other>"
captured_date: "YYYY-MM-DD"
routed_to: "<knowledge | projects>"
status: "<active | evergreen | archived | needs-review>"
key_people:
  - "<person or team>"
key_concepts:
  - "<concept>"
related_notes:
  - "[[Related Note]]"
---

# <Clean Note Title>

> [!summary]
> **Source:** <source>
> **Captured:** <YYYY-MM-DD>
> **Key People:** <people or `--`>
> **Key Concepts:** <concepts or `--`>
> **Route:** <knowledge/ or projects/>
```

If a field is unknown, use:

`--`

Do not invent metadata.

---

## Required Note Sections

Each ingested note should use this structure:

```md
## Summary

Concise summary of the source.

## Key Takeaways

- ...

## Important Details

- ...

## People / Organizations

- ...

## Concepts

- ...

## Useful Quotes or Claims

Use short excerpts only when necessary. Avoid copying large copyrighted sections.

## Links / References

- Source: <URL or file reference>
- Related: [[Related Note]]

## Follow-Up Actions

- ...
```

---

## Wikilink Rules

Use `[[wikilinks]]` on first meaningful mention of:

* people
* projects
* frameworks
* recurring concepts
* rooms
* systems
* major workflows
* durable doctrine
* named tools

Only link the first meaningful mention in each note section unless clarity requires another link.

Do not over-link common words.

Examples:

* `[[MAIN]]`
* `[[JIG]]`
* `[[TCC Tactical Command Center]]`
* `[[FanDuel Integration]]`
* `[[Claude Code]]`
* `[[Web Scraping Utility Skill]]`

---

## Source Handling

### Articles

Capture:

* title
* URL
* author if visible
* publication date if visible
* key people
* key concepts
* summary
* useful claims
* links

### YouTube Links

Capture:

* video title
* channel
* URL
* publish date if visible
* transcript if available
* summary
* key people
* key concepts
* timestamps if provided

If transcript is unavailable, mark:

`Transcript unavailable`

Do not invent transcript content.

### PDFs

Capture:

* document title
* file name or URL
* author/org if visible
* date if visible
* summary
* key sections
* key claims
* page references when available

If extraction fails, mark:

`PDF extraction unavailable`

### Pasted Notes

Capture:

* note title
* source as `pasted note`
* captured date
* cleaned summary
* key concepts
* follow-up actions

---

## Relationship to /web-scraping

Use `/web-scraping` before `/ingest-source` when:

* the source URL needs semantic discovery
* the page is JavaScript-heavy
* Firecrawl is needed for rendered extraction
* Exa is needed to find authoritative source candidates
* the source content is not directly available

Use `/ingest-source` after extraction to place and structure the content in the knowledge base.

---

## Data Integrity Rules

Never fabricate:

* author
* date
* transcript content
* source title
* quotes
* facts
* claims
* people
* metadata
* project status

If missing, use:

`--`

or:

`DATA GAP`

Clearly label:

* unavailable transcript
* blocked page
* unreadable PDF
* partial extraction
* unknown author/date
* uncertain routing

---

## MLB HR ENGINE Boundaries

This skill is documentation/knowledge-base only.

It must not modify:

* `config.py`
* `pipeline.py`
* MAIN probability
* JIG scoring
* HVY logic
* calibration
* routing
* session state
* cache ownership
* frontend production behavior
* deployment configuration

This skill may create notes under:

* `MLB HR ENGINE/knowledge/`
* `MLB HR ENGINE/projects/`

It may create Obsidian wikilinks, but it must not rewrite doctrine unless explicitly authorized.

---

## Recommended Output Format

```md
## /ingest-source Result

### Source
...

### Route
`knowledge/` or `projects/`

### Created Note
`path/to/note.md`

### Summary
...

### Key People
- ...

### Key Concepts
- ...

### Related Notes
- [[...]]

### Data Gaps
- ...

### Follow-Up Actions
- ...
```
