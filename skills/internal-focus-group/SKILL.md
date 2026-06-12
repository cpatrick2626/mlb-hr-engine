# /internal-focus-group

## Purpose

`/internal-focus-group` tests ideas before launch.

It creates a reusable focus-group panel from real people or explicitly named internal personas whose notes, interviews, transcripts, feedback, or history have been ingested into the knowledge base.

It helps the operator evaluate:

- product ideas
- app changes
- MLB HR ENGINE UX changes
- dashboard/workflow changes
- copy
- launch plans
- feature priorities
- confusion risks
- adoption risk
- operator trust

This skill is different from `/ask-the-board`.

- `/ask-the-board` gives expert-inspired decision advice.
- `/internal-focus-group` gives user/persona feedback before shipping.

---

## Canonical Folder

Focus-group source material lives here:

`MLB HR ENGINE/knowledge/focus-group/{name}/`

Examples:

- `MLB HR ENGINE/knowledge/focus-group/chris-operator/`
- `MLB HR ENGINE/knowledge/focus-group/jig-user/`
- `MLB HR ENGINE/knowledge/focus-group/mobile-user/`
- `MLB HR ENGINE/knowledge/focus-group/sharp-bettor/`

Do not use `focus-ygroup/`; treat that as a typo.

---

## How to Add a Person

To add a person or named focus-group agent:

1. Gather their notes, interviews, transcripts, feedback, messages, or known history.
2. Run `/ingest-source` or `/ingest-resource`.
3. Save the resulting notes under:

`MLB HR ENGINE/knowledge/focus-group/{name}/`

4. Include:
   - who they are
   - source material
   - voice/tone cues
   - lens
   - history
   - product preferences
   - known frustrations
   - decision criteria
   - evidence level

Do not invent unsupported details.

---

## Agent Types

Allowed agent types:

1. **Real Person**
   - Based on actual notes, interviews, feedback, transcripts, or direct history.
   - Must be source-backed.

2. **Internal Persona**
   - A named internal product persona such as `JIG user`, `mobile operator`, or `sharp bettor`.
   - Must be clearly labeled as a persona, not a real person.

3. **Workflow Lens**
   - A system/user role such as `TCC operator`, `MAIN scanner`, `JIG builder`.
   - Used to test workflow clarity.

---

## Identity Boundary

Do not claim the real person personally reviewed the decision.

Do not fabricate quotes, memories, preferences, or private opinions.

Use language like:

- "Based on ingested material, the Chris Operator lens would likely flag..."
- "JIG User persona feedback:"
- "Source coverage for this agent is thin: DATA GAP"

Avoid language like:

- "Chris said..."
- "JIG thinks..."
- "This person would definitely..."

unless the exact point is present in ingested notes.

---

## Invocation Patterns

Ask the full panel:

```text
Use /internal-focus-group.

Test this before launch:
<idea/change/copy/feature>

Context:
<relevant context>

Priority:
<clarity | conversion | trust | speed | usability | operator confidence>
```

Ask one person:

```text
Use /internal-focus-group.

Ask <name> what they think about:
<idea/change/copy/feature>
```

Ask a subset:

```text
Use /internal-focus-group.

Ask:
- <name 1>
- <name 2>
- <name 3>

Question:
<decision or launch idea>
```

---

## Default Behavior

When invoked:

1. Identify the decision, feature, copy, or launch item being tested.
2. Determine whether the user requested one person, a subset, or the whole panel.
3. Check whether each requested person has source material.
4. If source material is missing, mark `DATA GAP`.
5. Run each selected agent lens independently.
6. Return honest feedback.
7. Synthesize agreements, disagreements, risks, and what to change before launch.
8. Recommend one next action.

---

## Output Format

```md
## /internal-focus-group Result

### Item Being Tested
...

### Selected Focus Group
- ...

### Source Coverage
| Agent | Source Folder | Coverage | Notes |
|---|---|---|---|

### Individual Feedback

#### <Agent Name>
**Lens:** ...
**Likely Reaction:** ...
**What They Like:** ...
**What Confuses Them:** ...
**Objection / Friction:** ...
**Suggested Change:** ...

### Agreements
...

### Disagreements
...

### Launch Risks
...

### What To Change Before Shipping
...

### Final Recommendation
...

### One Next Action
...
```

---

## Feedback Standards

Each agent should return:

* honest feedback
* clarity problems
* trust problems
* friction points
* what they would misunderstand
* what they would like
* what they would ignore
* what would make the feature/copy/workflow stronger

Do not make every agent positive.

A useful focus group should expose friction before launch.

---

## Person / Agent File Expectations

Each focus-group folder should contain one or more markdown notes.

Recommended summary fields:

```md
---
agent_name: "<name>"
agent_type: "<real-person | internal-persona | workflow-lens>"
source: "<source>"
source_type: "<note | transcript | interview | feedback | other>"
captured_date: "YYYY-MM-DD"
evidence_level: "<strong | medium | thin>"
voice_cues:
  - "<tone or phrasing cue>"
lens:
  - "<how this person evaluates things>"
known_frictions:
  - "<known frustration>"
decision_criteria:
  - "<what matters to them>"
---
```

If unknown, use:

`--`

---

## Relationship to Other Skills

Use `/ingest-source` or `/ingest-resource` to add people and source material.

Use `/web-scraping` only when public source discovery or source extraction is required.

Use `/ask-the-board` when the decision needs expert-style strategic advice.

Use `/internal-focus-group` when the decision needs user/persona feedback before launch.

Use `/improve-system` if repeated focus-group findings reveal a durable product, workflow, UX, or skill lesson.

---

## MLB HR ENGINE Usage

Use `/internal-focus-group` to test:

* TCC screen changes
* MAIN/JIG workflow changes
* Full Slate changes
* Top Targets changes
* JIG Builder changes
* FanDuel flow changes
* mobile layout changes
* labels and tier language
* onboarding copy
* launch announcements
* operator workflow clarity

The skill must preserve:

* MAIN / JIG separation
* HVY display-only doctrine
* TCC orchestration-only doctrine
* no hidden scoring
* no fabricated model inputs
* `config.py` as threshold/model constant source of truth
* `pipeline.py` as canonical assembly entrypoint

It must not propose edits to protected surfaces without flagging risk and routing through audit-first workflow.

---

## Data Integrity Rules

Never fabricate:

* person history
* person feedback
* quotes
* source notes
* preferences
* launch results
* app status
* model outputs
* player data
* betting outcomes

If unavailable, use:

`--`

or:

`DATA GAP`

Clearly separate:

* source-backed feedback
* persona-based inference
* speculation
* recommended changes

---

## Clarification Rule

If the item being tested is unclear, ask:

```text
What should the focus group review before launch?
```

If the requested person has no source folder, say:

```text
DATA GAP: I do not have ingested source material for <name>. Add material with /ingest-source into MLB HR ENGINE/knowledge/focus-group/<name>/.
```
