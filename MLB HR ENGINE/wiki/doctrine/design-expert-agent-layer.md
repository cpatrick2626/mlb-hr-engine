# AI Expert-Agent Layer — Design Spec

Status: DESIGN / PLANNING ONLY. Risk: MEDIUM (analyst agents) to HIGH (anything touching scoring/modal). Core principle: Expertise = methods + data + rules + validation. Not impersonation.

Cross-references: [[wiki/doctrine/ticket-roles|ticket-roles]] · [[wiki/doctrine/main-jig-separation|main-jig-separation]] · [[wiki/doctrine/ask-the-board-skill|ask-the-board-skill]]

## Relationship to existing systems
Not greenfield. Extends /ask-the-board (existing advisory-lens skill) and the CC/CX execution workflow — does not duplicate them. New value = the baseball/betting analyst bench + user-facing explainability. The Product/Build/Ops agents mostly formalize the existing CC/CX process and should be board lenses, not standalone builds.

## Operator decisions (locked 2026-06-15)
1. Naming: Option A. /ask-the-board stays operator-only decision lens (named public-method lenses, behind the scenes). In-product agents are ROLE-BASED ONLY — no person names, voices, or quotes.
2. First build: Explainability Agent.
3. Rule-based / template-driven first. v1 fills templates with real row field values — grounded by construction, cannot hallucinate, no LLM. Add LLM only for narrative summaries after grounding proven.
4. Lives inside existing surfaces (tooltips, batter card, ticket review, pitch-mix modal). No separate advisor panel yet.

## Recommended roster (trimmed from 24 to a sharp bench)
Tier 1 (new high-value): Power Profile Scout, Matchup/Pitch-Mix Analyst, Risk Analyst, Parlay/Ticket Construction Analyst, Explainability/Clarity Agent, Data Quality Agent.
Tier 2 (later): Sabermetric Analyst, Park/Weather Analyst, Platoon/Splits Analyst, Odds/Value Analyst (display-only).
Tier 3 (formalize as board lenses, do not build standalone): Product Director, Systems Architect, Engineers, QA, Deploy/Ops, UX/Design agents.

## Per-agent spec (Tier 1)
Each agent defined by: domain, inputs (existing row fields), outputs, boundaries (read-only, no scoring changes, no fake certainty, no fabrication — show "--" on missing data), user-facing flag, and how it becomes expert (fixed reasoning framework + config thresholds + validation on real slates).
- Power Profile Scout: why a hitter is dangerous (barrel/HH/maxEV/pull-air/xSLG/HR-PA). User-facing.
- Matchup/Pitch-Mix Analyst: why a matchup is exploitable (arsenal/vulnerability/splits). User-facing.
- Risk Analyst: what is wrong with a pick/ticket (volatility/sample/spot). User-facing.
- Parlay/Ticket Analyst: combine roles into sound tickets. User-facing. Ticket logic is operator-strategy, not a model output. See [[wiki/doctrine/ticket-roles|ticket-roles]] for role definitions.
- Explainability/Clarity Agent: plain-language translation of tier/role/metrics. User-facing.
- Data Quality Agent: flag stale/missing/low-sample data (silent-1.0 pitchers, stale odds). Behind-scenes + confidence badge.

## Build order
First: Explainability Agent (tooltips) — DONE 2026-06-15 (template-grounded tier/role badge tooltips, v1 shipped).
Then: Data Quality flags → Power Profile Scout → Matchup/Pitch-Mix Analyst → Risk/Parlay Analyst → in-product agent debate. Each phase: calibrate → build read-only → operator review → ship.

## Guardrails
No impersonation, no voice/identity cloning, no scraping, no copyrighted reproduction, no fake certainty, no scoring changes, market data display-only, MAIN/JIG separation preserved. Biggest technical risk = hallucination: every claim must trace to real row data or doctrine, cite the metric, show "--" rather than invent.

---

## Domain Validation / Governance Agents (LATER PHASE — Phase 7+, not Phase 1)

A second agent class: domain agents that REVIEW proposed changes before implementation or deployment. ADVISORY gates only — they output PASS / CONCERNS / STRONG-CAUTION, operator retains final approval, they never block autonomously or modify anything. Would have caught the WILDCARD <=2 cap bug; formalize the human calibrate→audit→review discipline used in this session.

**Distinction:** Explainability agents explain existing values to the user. Governance agents review proposed changes before build/deploy.

Build only after explainability + analyst agents are proven useful and reliable. Five candidates:

### (1) Tier Agent
- Domain: tier threshold changes (ELITE/PREMIUM/STANDARD/FRINGE boundaries + gauge).
- Reviews: proposed threshold changes, resulting tier distribution, inflation/deflation vs historical baselines, downstream role impact (what role counts shift), doctrine alignment with [[wiki/doctrine/tier-vocabulary|tier-vocabulary]].
- Outputs: PASS / CONCERNS / STRONG-CAUTION + distribution delta, affected pick counts.

### (2) Role Agent
- Domain: PRIME / EXPLOSIVE / ADVANTAGE / WILDCARD role logic. See [[wiki/doctrine/ticket-roles|ticket-roles]].
- Reviews: role filter changes, qualifying-count outputs, overlap between roles, JIG-only restrictions, tier-vs-role separation (MAIN/JIG).
- Flags: if PRIME or EXPLOSIVE counts fall to zero or inflate beyond baseline; if tier-vs-role separation breaks.
- Outputs: PASS / CONCERNS / STRONG-CAUTION + role counts, overlap matrix, separation status.

### (3) Scoring Agent
- Domain: MAIN model probability + JIG tactical scoring.
- Reviews: changes to probability construction, signal weights, calibration constants, regression anchors. Checks for unintended rank/probability shifts on a reference slate, HVY contamination of MAIN (MAIN/JIG contamination = hard flag), source-of-truth violations (constants in config.py vs duplication elsewhere).
- Outputs: PASS / CONCERNS / STRONG-CAUTION + rank delta table, probability shift histogram, contamination flag.
- See [[wiki/doctrine/main-jig-separation|main-jig-separation]].

### (4) Data Quality Agent
- Domain: stat fields, null handling, sample size, stale data, odds freshness.
- Reviews: null/missing stat handling, stale pitcher pitch-mix, low-sample batters, cache age, odds staleness. Confirms display-only market data is not affecting scoring.
- Outputs: PASS / CONCERNS / STRONG-CAUTION + data quality report (field-level null counts, staleness flags, sample-size warnings).

### (5) Ticket Construction Agent
- Domain: parlay/ticket composition logic.
- Reviews: parlay role logic, ticket templates, risk balance across roles, WILDCARD overuse, HR-variance honesty. See [[wiki/doctrine/ticket-roles|ticket-roles]].
- Flags: WILDCARD overuse (more than 1 per ticket by default), correlated legs, undisclosed variance.
- Outputs: PASS / CONCERNS / STRONG-CAUTION + ticket risk profile, correlation warnings.

---

## Phase 1 (current) — explicitly unchanged

Explainability Agent v1 shipped 2026-06-15: template-grounded tier/role badge tooltips, read-only, no LLM, no governance gate. No other agents active. No scoring changes. No governance review gates deployed. Phase 1 scope is closed; all governance agent work is deferred to Phase 7+.
