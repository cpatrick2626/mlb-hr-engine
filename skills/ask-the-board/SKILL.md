# /ask-the-board

## Purpose

`/ask-the-board` helps the operator make stronger decisions by running the question through a focused Board of Advisors.

It is built for decisions involving:

- sports betting judgment
- edge quality
- model trust
- product direction
- app design
- engineering tradeoffs
- UX clarity
- project prioritization
- MLB HR ENGINE tactical/product decisions

This skill does **not** impersonate real people.

It uses expert-inspired advisory lenses based on public fields of expertise, ingested source material, known bodies of work, and decision principles.

---

## 4-Step Workflow

### Step 1 — Identify the Experts

Select the right board members for the operator's situation.

Default board:

1. Billy Walters — Sharp Betting Discipline / Market Attack
2. Bill Benter — Quant Edge / Probability Model Design
3. Marty Cagan — Product Strategy / What to Build
4. John Carmack — Engineering Systems / Simplicity / Performance
5. Jakob Nielsen / Nielsen Norman Group — UX / Usability / Decision Clarity

---

### Step 2 — Ingest Their Training Data

Use `/ingest-source` to capture public content into:

`MLB HR ENGINE/knowledge/advisory-board/`

Suggested folders:

- `MLB HR ENGINE/knowledge/advisory-board/billy-walters/`
- `MLB HR ENGINE/knowledge/advisory-board/bill-benter/`
- `MLB HR ENGINE/knowledge/advisory-board/marty-cagan/`
- `MLB HR ENGINE/knowledge/advisory-board/john-carmack/`
- `MLB HR ENGINE/knowledge/advisory-board/nngroup-ux/`

Each ingested source should capture:

- source
- source type
- date
- key people
- key concepts
- decision principles
- useful frameworks
- direct relevance to `/ask-the-board`
- related `[[wikilinks]]`

Do not fabricate missing source data.

If transcript, date, author, or source details are unavailable, mark:

`--`

or:

`DATA GAP`

---

### Step 3 — Create the /ask-the-board Skill

When the operator asks a decision question, automatically select the relevant advisors, give each advisor-style take, flag where they agree and disagree, identify hidden risk, and synthesize what the operator should actually do.

Use expert-inspired advisory lenses.

Do not fabricate direct quotes, exact opinions, or personal advice from real people.

---

### Step 4 — Ask the Board a Question

The operator can invoke:

```text
/ask-the-board
```

or:

```text
Use /ask-the-board.

Decision:
<decision or question>

Context:
<relevant context>

Priority:
<speed | safety | product quality | betting edge | engineering stability | UX clarity>
```

The skill returns selected advisor lenses, agreement, disagreement, hidden risk, synthesis, and one next action.

---

## Default Board Seats

### 1. Billy Walters-Inspired Market Discipline Lens

Use this lens for:

* bet/pass discipline
* market timing
* price sensitivity
* bankroll caution
* emotional betting control
* syndicate-style decision pressure
* avoiding overconfidence
* separating strong signals from playable edges

Core questions:

* Is this a real edge or just an exciting signal?
* Is the price still playable?
* Did the market already move?
* Is the operator chasing or deploying?
* What would make this a pass?
* Is the stake size disciplined?

---

### 2. Bill Benter-Inspired Quant Edge Lens

Use this lens for:

* model quality
* probability logic
* public market comparison
* signal weighting
* overfitting risk
* data quality
* expected value structure
* model-to-betting translation

Core questions:

* Is the model structurally sound?
* Are we separating prediction from edge?
* Are we comparing model probability to market-implied probability correctly?
* Is the input data reliable enough?
* Are we overfitting to short-term signals?
* What is the cleanest measurable edge?

---

### 3. Marty Cagan-Inspired Product Strategy Lens

Use this lens for:

* roadmap discipline
* product value
* user problem clarity
* feature prioritization
* product discovery
* operator workflow
* what to cut
* what to test before building

Core questions:

* What user problem does this solve?
* Is this a product capability or just a feature idea?
* What evidence says users need it?
* What should be cut or delayed?
* What is the smallest useful version?
* Does this improve decision-making?

---

### 4. John Carmack-Inspired Engineering Clarity Lens

Use this lens for:

* architecture clarity
* system complexity
* technical debt
* performance
* reliability
* debugging
* implementation realism
* removing unnecessary abstraction

Core questions:

* What is the simplest working version?
* What part of this system is fragile?
* Where is complexity hiding?
* What can be measured directly?
* What should be deleted or simplified?
* What will break under real usage?

---

### 5. Jakob Nielsen / NNGroup-Inspired UX Lens

Use this lens for:

* usability
* operator comprehension
* information hierarchy
* friction reduction
* mobile/tablet readability
* decision speed
* labeling
* error prevention

Core questions:

* Can the operator understand this immediately?
* Is the interface showing the right thing at the right time?
* Are labels clear?
* Is there too much cognitive load?
* Does the design support fast action?
* What user mistake does this prevent?

---

## Panel Selection

Do not always use all five seats.

Pick the smallest useful panel from context.

### Betting Decision Panel

Use for betting, odds, props, edge, bankroll, or picks:

* Billy Walters-inspired market discipline lens
* Bill Benter-inspired quant edge lens

Optional add-on:

* Jakob Nielsen / NNGroup-inspired UX lens if the issue involves app presentation or operator decision clarity.

---

### Product / App Build Panel

Use for app ideas, roadmap, features, UI, UX, or project planning:

* Marty Cagan-inspired product strategy lens
* John Carmack-inspired engineering clarity lens
* Jakob Nielsen / NNGroup-inspired UX lens

Optional add-on:

* Billy Walters-inspired market discipline lens if the product change affects betting behavior.
* Bill Benter-inspired quant edge lens if the product change affects model/probability logic.

---

### MLB HR ENGINE Panel

Use for MLB HR ENGINE decisions:

* Billy Walters-inspired market discipline lens
* Bill Benter-inspired quant edge lens
* Marty Cagan-inspired product strategy lens
* John Carmack-inspired engineering clarity lens
* Jakob Nielsen / NNGroup-inspired UX lens

This full board is appropriate when the decision touches betting logic, model trust, product value, engineering risk, and tactical UI clarity.

---

### Devil's Advocate Panel

Use when the operator asks what could be wrong:

* Billy Walters-inspired market discipline lens
* Bill Benter-inspired quant edge lens
* John Carmack-inspired engineering clarity lens
* Jakob Nielsen / NNGroup-inspired UX lens

---

## Standard Output Format

```md
## /ask-the-board Result

### Decision Under Review
...

### Selected Panel
- ...

### Advisor Takes

#### Walters-Inspired Market Discipline Lens
- ...

#### Benter-Inspired Quant Edge Lens
- ...

#### Cagan-Inspired Product Strategy Lens
- ...

#### Carmack-Inspired Engineering Clarity Lens
- ...

#### NNGroup-Inspired UX Lens
- ...

### Where They Agree
...

### Where They Disagree
...

### Hidden Risk
...

### Final Synthesis
...

### What You Should Actually Do
...

### One Next Action
...
```

Only include lenses that were selected.

---

## Decision Rules

When the board disagrees:

* Betting discipline beats excitement.
* Data integrity beats presentation.
* Source-of-truth boundaries beat convenience.
* Simplicity beats overbuilt architecture.
* Usability beats visual complexity.
* Product value beats feature accumulation.
* Pass is a valid decision.

For MLB HR ENGINE specifically:

* MAIN and JIG must never merge.
* HVY stays display-only on JIG side.
* TCC orchestrates but does not compute.
* `config.py` remains source of truth for thresholds/model constants.
* `pipeline.py` remains canonical data assembly entrypoint.
* Do not invent model confidence or HR probability.
* Do not create hidden composite scoring.
* If data is missing, show `--` or `DATA GAP`.

---

## Betting / Gambling Boundaries

This skill may help evaluate betting logic, edge quality, model confidence, and risk.

It must not:

* guarantee outcomes
* present gambling as risk-free
* encourage chasing losses
* recommend reckless staking
* fabricate odds
* fabricate sportsbook availability
* fabricate model probability
* fabricate injury, lineup, weather, or pitch data

If the user asks for betting deployment, remind that outcomes are uncertain and bankroll discipline matters.

---

## Relationship to Other Skills

Use `/web-scraping` first when:

* public source discovery is needed
* current source material must be verified
* expert content URLs need to be found
* sports data must be checked live

Use `/ingest-source` when:

* an article, YouTube video, transcript, PDF, or note should be captured into the knowledge base
* expert content needs to be saved
* board-source material should become reusable

Use `/improve-system` when:

* the board output reveals a durable lesson
* a skill needs improvement
* the system has a repeated weakness
* project doctrine needs refinement

Typical sequence:

1. `/web-scraping` finds relevant expert/source content.
2. `/ingest-source` captures it into `knowledge/advisory-board/`.
3. `/ask-the-board` uses the advisory lenses to review decisions.
4. `/improve-system` captures lessons from repeated board outputs.

---

## Data Integrity Rules

Never fabricate:

* expert quotes
* source titles
* publication dates
* records
* exact opinions
* current expert positions
* betting results
* odds
* model outputs
* player data
* app status
* implementation status

If unknown, use:

`--`

or:

`DATA GAP`

Clearly separate:

* confirmed information
* inferred lens-based analysis
* assumptions
* recommendations

---

## Clarification Rule

If the decision is unclear, ask:

```text
What decision should the board review?
```

If the panel is unclear but the decision is clear, select the panel automatically.
