# /improve-system

## Purpose

`/improve-system` compounds the operating system over time.

It turns recent work, lessons, conflicts, gaps, wins, and repeated friction into cleaner doctrine, better skills, better knowledge structure, and stronger project memory.

This skill uses no external tools by default.

It works from:

- pasted conversation output
- recent Claude Code results
- existing notes
- existing skill files
- project/session logs
- operator-provided stories, wins, issues, or lessons

---

## Tools

None.

Do not use Exa, Firecrawl, browser tools, APIs, scraping, or external services unless the operator separately authorizes another skill.

---

## Modes

`/improve-system` has five modes:

1. Audit
2. Skill Review
3. Experience
4. Historical Review
5. Foundation

Pick the mode from context.

Ask one clarifying question only when the mode is genuinely unclear.

---

## Mode Selection

### Use Audit Mode when the user wants to find problems

Triggers:

- stale notes
- conflicting notes
- duplicate notes
- outdated doctrine
- overlapping files
- confusing structure
- repeated contradictions
- cleanup candidates

Goal:

Find issues without rewriting unless authorized.

---

### Use Skill Review Mode when the user wants to improve a skill

Triggers:

- recent back-and-forth showed a skill needs adjustment
- a skill was confusing
- a skill missed a step
- a skill produced too much output
- a skill needs new boundaries
- a skill needs better examples
- a skill needs mode/routing refinement

Goal:

Recommend focused updates to an existing skill.

Do not edit the skill unless explicitly authorized.

---

### Use Experience Mode when the user shares a story, win, failure, lesson, or pattern

Triggers:

- "this worked"
- "this failed"
- "remember this lesson"
- "we learned"
- "next time"
- "good workflow"
- "bad workflow"
- "this saved time"
- "this caused confusion"

Goal:

Capture the lesson into reusable operating knowledge.

Route stable lessons to `knowledge/`.

Route active project lessons to `projects/`.

---

### Use Historical Review Mode when the user wants to mine recent Claude Code sessions

Triggers:

- recent Claude Code sessions
- missed learnings
- repeated issues
- repeated validation failures
- unrecorded discoveries
- lessons from implementation
- extract patterns from past execution results

Goal:

Review recent session/log material and identify reusable lessons, doctrine gaps, skill improvements, and follow-up notes.

Do not rewrite history. Produce findings and recommended captures.

---

### Use Foundation Mode when the user wants missing foundational content filled in

Triggers:

- brand
- audience
- offers
- positioning
- voice
- principles
- operating standards
- recurring workflows
- product foundations
- customer/user definitions
- content pillars

Goal:

Identify missing foundational notes and create a proposed structure or draft when authorized.

---

## Default Behavior

When invoked:

1. Identify the mode from context.
2. State the selected mode.
3. State the input used.
4. Produce a focused improvement output.
5. Mark uncertain or missing data as `--`.
6. Recommend one next action.
7. Do not modify files unless explicitly authorized.

---

## Mode Outputs

### Audit Mode Output

```md
## /improve-system Result

Mode: Audit

### Scope Reviewed
- ...

### Findings
| Issue | Type | Location | Severity | Recommendation |
|---|---|---|---|---|

### Duplicate / Conflicting Notes
| Note A | Note B | Conflict | Recommended Owner |
|---|---|---|---|

### Stale Content
| Note | Reason | Suggested Action |
|---|---|---|

### Recommended Next Action
...
```

---

### Skill Review Mode Output

```md
## /improve-system Result

Mode: Skill Review

### Skill Reviewed
`/<skill-name>`

### Recent Friction / Learning
- ...

### Recommended Skill Updates
| Area | Current Issue | Proposed Update |
|---|---|---|

### Safe Patch Scope
- ...

### Do Not Change
- ...

### Recommended Next Action
...
```

---

### Experience Mode Output

```md
## /improve-system Result

Mode: Experience

### Experience Captured
...

### Lesson
...

### Reusable Principle
...

### Suggested Route
`knowledge/` or `projects/`

### Suggested Note Title
...

### Suggested Wikilinks
- [[...]]

### Recommended Next Action
...
```

---

### Historical Review Mode Output

```md
## /improve-system Result

Mode: Historical Review

### Sessions / Logs Reviewed
- ...

### Missed Learnings
| Learning | Evidence | Recommended Capture |
|---|---|---|

### Repeated Patterns
- ...

### Doctrine Gaps
- ...

### Skill Improvements
- ...

### Recommended Next Action
...
```

---

### Foundation Mode Output

```md
## /improve-system Result

Mode: Foundation

### Foundation Area
...

### Missing Content
| Area | Missing Piece | Why It Matters |
|---|---|---|

### Proposed Foundation Notes
- ...

### Draft Structure
...

### Recommended Next Action
...
```

---

## Knowledge Base Routing

Use:

`MLB HR ENGINE/knowledge/`

for stable, evergreen operating knowledge:

* frameworks
* lessons
* principles
* voice
* brand foundations
* audience definitions
* people processes
* durable workflows

Use:

`MLB HR ENGINE/projects/`

for active work:

* current implementation lessons
* launch work
* videos
* newsletters
* campaigns
* active project retrospectives
* production validation lessons

---

## Relationship to Other Skills

Use `/web-scraping` before `/improve-system` only if fresh external source discovery is needed.

Use `/ingest-source` when a specific source must be captured into the knowledge base.

Use `/improve-system` when the goal is to improve the operating system itself.

Typical sequence:

1. `/web-scraping` finds or extracts source material.
2. `/ingest-source` captures the source into the knowledge base.
3. `/improve-system` converts patterns, lessons, and gaps into better doctrine or skill improvements.

---

## Data Integrity Rules

Never fabricate:

* historical events
* session results
* file contents
* operator intent
* lessons not supported by input
* people
* claims
* dates
* decisions
* implementation status

If unknown, use:

`--`

or:

`DATA GAP`

Clearly separate:

* confirmed findings
* inferred patterns
* proposed improvements
* open questions

---

## MLB HR ENGINE Boundaries

This skill is knowledge-system improvement only.

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

It must preserve:

* MAIN / JIG separation
* HVY display-only doctrine
* TCC orchestration-only doctrine
* no hidden scoring
* no fabricated model inputs
* protected-surface review rules

It may recommend doctrine or skill updates, but actual edits require operator authorization.

---

## Clarification Rule

If the mode is unclear, ask:

```text
Which /improve-system mode should I use: Audit, Skill Review, Experience, Historical Review, or Foundation?
```

Do not ask if context clearly implies the mode.
