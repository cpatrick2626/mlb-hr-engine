# Compound Engineering

## Purpose

Compound Engineering is a reusable engineering workflow suite.

It helps the operator move from idea to validated completion through clear planning, phased delivery, review, debugging, and done-state confirmation.

It includes five commands:

- `/ce-brainstorm`
- `/ce-plan`
- `/ce-work`
- `/ce-code-review`
- `/ce-debug`

---

## Core Workflow

1. Plan what you're building.
2. Define what "done" actually looks like.
3. Work through clear delivery phases.
4. Review the work and troubleshoot if needed.
5. Mark as done only after validation passes.

---

## Command Summary

### `/ce-brainstorm`

Use when the operator has an idea, problem, feature, bug, workflow improvement, or vague goal.

Output:

- possible approaches
- risks
- easiest version
- better version
- what not to build
- recommended path

---

### `/ce-plan`

Use when the operator is ready to define execution.

Output:

- objective
- scope
- non-goals
- protected surfaces
- definition of done
- phases
- validation
- rollback plan
- recommended code AI/model/effort/risk
- copy-ready execution prompt if needed

---

### `/ce-work`

Use when implementation has been authorized.

Output:

- phase-by-phase work plan
- exact files allowed
- forbidden zones
- validation commands
- deliverables
- no commit/no push unless authorized

This command should not be used to bypass MLB HR ENGINE protected-surface governance.

---

### `/ce-code-review`

Use after work is complete or claimed complete.

Output:

- scope check
- diff review checklist
- definition-of-done check
- regression risk
- validation evidence
- unresolved issues
- accept/revise/reject recommendation

---

### `/ce-debug`

Use when something breaks, fails validation, behaves unexpectedly, or becomes confusing.

Output:

- observed symptom
- likely failure class
- reproduction path
- isolation steps
- suspected cause
- safe fix options
- validation plan
- escalation risk

---

## Definition of Done Rule

No task is done until:

- scope matches authorization
- expected files changed only
- protected surfaces untouched unless explicitly authorized
- validation passes
- known regressions are checked
- unresolved issues are documented
- git status is understood
- commit/push status is explicit

Use:

`DONE`

only when all criteria are met.

Use:

`NOT DONE`

when validation is missing, partial, blocked, or failed.

---

## MLB HR ENGINE Risk Classification

### LOW

Docs, skills, Obsidian notes, read-only audits, file placement, housekeeping.

### MEDIUM

Narrow single-file frontend/runtime/UI fixes with clear regression boundary.

### HIGH

Any work touching:

- `config.py`
- `pipeline.py`
- engine logic
- calibration
- MAIN probability
- JIG scoring
- HVY logic
- scoring composites
- routing
- session state
- cache ownership
- hydration
- modal architecture
- deployment config
- API payload shape

HIGH work must be audit-first, then separately authorized execution.

---

## MLB HR ENGINE Protected Surfaces

Do not modify or recommend direct execution on these without explicit operator authorization:

- `mlb_hr_engine_v4/config.py`
- `mlb_hr_engine_v4/pipeline.py`
- MAIN probability
- JIG scoring
- HVY logic
- calibration
- scoring composites
- routing
- session state
- cache ownership
- hydration
- modal architecture
- deployment configuration
- protected production frontend behavior

---

## Output Rules

For Claude Code / Codex prompts, include:

- ROOM Deployed From
- Update Room
- Update Room With Results
- TASK TYPE
- RECOMMENDED CODE AI
- MODEL
- EFFORT
- RISK
- PURPOSE
- repo path
- allowed files
- forbidden zones
- validation
- deliverables
- git safety
- DO NOT COMMIT unless authorized
- DO NOT PUSH unless authorized

Use one action per prompt.

---

## Relationship to Other Skills

Use `/ask-the-board` before Compound Engineering when a decision needs strategic review.

Use `/internal-focus-group` before shipping user-facing changes.

Use `/web-scraping` when current external research is needed.

Use `/ingest-source` when reference material should be captured.

Use `/improve-system` when repeated engineering lessons should become durable doctrine.

---

## Standard Output Format

```md
## Compound Engineering Result

### Command
`/<command>`

### Objective
...

### Scope
...

### Definition of Done
...

### Risk
...

### Plan / Findings
...

### Validation
...

### Status
`DONE` or `NOT DONE`

### One Next Action
...
```
