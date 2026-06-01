# AI Workforce & Orchestration Doctrine
## MLB HR ENGINE — Room 08

**Version:** 1.0  
**Date:** 2026-05-23  
**Status:** ACTIVE GOVERNANCE  
**Owner:** Claude (doctrine, sequencing, governance architecture)  
**Codex scope:** runtime implementation only — no workforce rule changes without Claude review  
**Phase:** 3A Step 05/10  
**Cross-references:** `cross_engine_command_surface_doctrine.md`, `full_slate_parent_orchestrator_doctrine.md`, `post_stabilization_implementation_sequence.md`, `escalation_jump_doctrine.md`, `deployment_trust_hierarchy.md`

---

## Contents

1. [AI Ownership Hierarchy Doctrine](#1-ai-ownership-hierarchy-doctrine)
2. [Room Governance Doctrine](#2-room-governance-doctrine)
3. [Stabilization Governance Doctrine](#3-stabilization-governance-doctrine)
4. [Command System Doctrine](#4-command-system-doctrine)
5. [AI Sequencing Doctrine](#5-ai-sequencing-doctrine)
6. [Validation Governance Doctrine](#6-validation-governance-doctrine)
7. [Audit & Recovery Doctrine](#7-audit--recovery-doctrine)
8. [Runtime Protection Doctrine](#8-runtime-protection-doctrine)
9. [Workforce Escalation Doctrine](#9-workforce-escalation-doctrine)
10. [Obsidian Governance Doctrine](#10-obsidian-governance-doctrine)
11. [Validation Checklist](#11-validation-checklist)
12. [Runtime Contamination Risks](#12-runtime-contamination-risks)
13. [Workforce Orchestration Hierarchy Summary](#13-workforce-orchestration-hierarchy-summary)

---

---

# 1. AI Ownership Hierarchy Doctrine

## 1.1 Core Principle

Every task has exactly one AI owner. Ownership determines who makes decisions, who executes, and who validates. Ambiguous ownership produces architecture drift, contamination, and regression.

**Doctrine:**
```
ASSIGN → ISOLATE → VALIDATE → REPORT → STABILIZE
```

No step may be skipped. No AI may self-assign to another AI's domain without operator authorization.

---

## 1.2 Claude — Governance & Architecture Owner

**Domain:** Everything before code is written and everything after code is merged.

| Responsibility | Scope |
|---|---|
| Doctrine authorship | All governance docs, specs, room definitions |
| Tactical UX architecture | Visual hierarchy, operational rhythm, information hierarchy |
| Escalation hierarchy | Defining tiers, severity, response sequences |
| Operational pacing | Step sequencing, blocking/unblocking rules |
| Workflow architecture | Cross-engine context rules, investigation flow |
| Orchestration planning | Room ordering, phase dependencies, parallel rules |
| Governance systems | Command definitions, audit structures, recovery protocols |
| Post-implementation review | Validating Codex output against doctrine before step close |

**Claude does NOT:**
- Write runtime code (Python, TypeScript, CSS)
- Submit patches or diffs to app.py or any engine module
- Merge or approve code without operator confirmation
- Modify session_state ownership, routing, or cache logic directly

**Claude's authority scope:** Doctrine is binding. If Codex output violates doctrine, Claude flags it before the step is marked complete. Operator has final authority on all disputes.

---

## 1.3 Codex — Runtime Implementation Owner

**Domain:** Everything inside the runtime boundary — bounded, isolated, testable patches.

| Responsibility | Scope |
|---|---|
| Runtime implementation | Python patches, React components, CSS changes |
| Bounded patches | Single-file or tightly scoped changes defined by Claude doctrine |
| Validation support | Running audit scripts, reporting output to operator |
| Rerender stabilization | Lazy gate insertion, widget minimization, rerender reduction |
| Cache-safe changes | Changes that respect session_state ownership rules |
| Regression repair | Fixing defects introduced by prior implementation |
| Implementation isolation | Never touching systems outside the defined task boundary |

**Codex does NOT:**
- Author doctrine or governance documents
- Redefine room scope or escalation hierarchy
- Make architectural decisions about cross-engine context
- Self-extend scope beyond the step definition without Claude review
- Perform parallel implementations across multiple protected systems

**Codex's authority scope:** Bounded to the task as defined by Claude. No scope extension without explicit operator authorization.

---

## 1.4 Playwright — Validation Authority

**Domain:** Browser-observable behavior — what the operator sees and touches.

| Responsibility | Scope |
|---|---|
| Browser validation | End-to-end rendering, navigation, interaction flow |
| Rerender validation | Confirming rerender count, lazy gate effectiveness |
| Hover/click validation | Button states, hover behaviors, interactive feedback |
| Navigation validation | Breadcrumb accuracy, engine switching, backtrack behavior |
| Mobile degradation testing | Layout integrity at narrow viewports |
| Escalation pacing validation | Tier badge rendering, escalation indicator accuracy |

**Playwright does NOT:**
- Make doctrine decisions
- Flag non-visual bugs (logic errors, probability calculations)
- Determine whether a feature is complete — that requires operator confirmation

**Playwright's authority scope:** Browser layer only. A passing Playwright suite does not mean a step is complete — it means browser behavior is verified. Operator confirmation still required for step close.

---

## 1.5 Ownership Conflict Resolution

When ownership is ambiguous or contested:

1. Claude reviews the task against doctrine definitions above
2. Claude assigns ownership in writing (in the step or task doc)
3. Operator confirms or redirects
4. No implementation begins until ownership is confirmed

**Forbidden patterns:**
- Codex modifying doctrine without Claude review
- Claude writing runtime code to unblock a step
- Playwright deciding a feature is "complete" without operator confirmation
- Any AI self-assigning to a domain owned by another AI

---

---

# 2. Room Governance Doctrine

## 2.1 Room Definition

A **room** is an isolated, owned domain of the system. Rooms have:
- A single primary owner (the AI responsible for governance of that domain)
- A defined scope boundary (what belongs and what does not)
- A lifecycle (PLANNING → ACTIVE → COMPLETE)
- An escalation path (who to escalate to when the room is blocked)

---

## 2.2 Room Registry

| Room | Domain | Primary Owner | Codex Role | Status |
|---|---|---|---|---|
| 01 — Data Pipeline | MLB API, Odds API, Statcast, Weather | Claude (doctrine) | Implementation | COMPLETE |
| 02 — Probability Engine | Poisson model, adjustment factors, calibration | Claude (doctrine) | Implementation | COMPLETE |
| 03 — EV / Market | EV%, Edge%, vig, no-vig probability | Claude (doctrine) | Implementation | COMPLETE |
| 04 — Filters & Sizing | 7-rule filter, quarter-Kelly | Claude (doctrine) | Implementation | COMPLETE |
| 05 — Output Layer | CLI tables, ranking, parlay builder | Claude (doctrine) | Implementation | COMPLETE |
| 06 — Streamlit Shell | app.py, routing, session_state | Claude (doctrine) | Implementation | STABILIZING |
| 07 — Operations | ops_daily, monitoring, CLV, tracking | Claude (doctrine) | Implementation | ACTIVE |
| 08 — AI Workforce | Orchestration doctrine, governance | Claude | N/A | ACTIVE |
| 09 — Modularization | Controlled modularization planning | Claude (doctrine) | Planning support | NEXT |
| 10 — Validation | Playwright, AppTest, audit scripts | Claude (doctrine) | Execution | BLOCKED on 08 |

---

## 2.3 Room Sequencing Rules

**Hard rule:** Rooms progress sequentially unless explicitly unblocked for parallel work.

Sequential enforcement:
- A room cannot enter ACTIVE state until all upstream blocking rooms are COMPLETE
- BLOCKED rooms stay BLOCKED until the blocking condition is resolved in writing
- No implementation begins in a BLOCKED room — planning documents may be written

**Parallel work rules:**
- Doctrine rooms (08) and runtime rooms (07) may run in parallel only when they do not share session_state ownership
- Validation rooms (10) may run passive validation in parallel with any room
- Never: concurrent implementation in two rooms that share routing, cache, or session_state namespace

---

## 2.4 Room Lifecycle

```
PLANNING       → ACTIVE          → COMPLETE
  ↓                ↓                 ↓
Doc authoring   Implementation    Completion report
Spec writing    Step execution    Operator confirmation
Dependency      Validation        Known-good baseline
  resolution    Step close        archived
```

A room is COMPLETE only when:
1. Completion report is posted
2. Operator confirms completion
3. Known-good baseline is archived (if room touched runtime)

---

## 2.5 Cross-Room Reference Rules

- Any room may **reference** another room's doctrine
- No room may **modify** another room's doctrine without operator authorization
- Cross-room references use doc filenames as canonical pointers (not informal descriptions)
- If a cross-room dependency is discovered mid-implementation, escalate before proceeding — do not silently absorb

---

---

# 3. Stabilization Governance Doctrine

## 3.1 Core Rule

**A stabilization step is ONLY complete when:**
1. A completion report is posted, OR
2. The operator explicitly confirms completion

Neither AI may mark a step complete unilaterally.

---

## 3.2 Stabilization Sequencing

Steps progress strictly sequentially. No step N+1 begins until step N is confirmed complete.

```
Step N [IN PROGRESS]
    ↓
Implementation complete
    ↓
Validation run (audit scripts, Playwright if applicable)
    ↓
Completion report posted
    ↓
Operator confirmation
    ↓
Step N [COMPLETE] → Step N+1 [ACTIVE]
```

**Exception:** If operator explicitly authorizes skipping a step (documented in the step record), that step may be marked SKIPPED and the sequence resumes at N+1.

---

## 3.3 Blocked/Unblocked Rules

**A step is BLOCKED when:**
- A prerequisite step is not yet COMPLETE
- A protected system required by the step has not been validated
- An open contamination risk is unresolved
- The operator has explicitly blocked it

**A step is UNBLOCKED when:**
- All prerequisites confirmed COMPLETE
- Operator explicitly lifts the block in writing

**Blocked step rules:**
- No implementation in a BLOCKED step
- Planning and doctrine documents may be written while blocked
- A blocked step must have its blocking condition documented

---

## 3.4 !cms Rules (Completion Marking System)

`!cms` marks a step complete.

**Governs:**
- Step N progress record is updated to COMPLETE
- Completion timestamp recorded
- Known-good baseline archived (if applicable)
- Next step is activated
- Operator receives completion notification

**Valid only when:**
- Completion report exists OR operator confirms explicitly
- No open FAIL validation items
- Protected systems unchanged (or changes validated)

**Invalid use:**
- Auto-triggering after implementation without validation
- Marking complete while validation is in progress
- Marking complete if Playwright/audit scripts have not been run (when required)

---

## 3.5 !xms Rules (Exit Master Stabilization)

`!xms` signals exit from a stabilization phase.

**Governs:**
- All active steps confirmed COMPLETE
- Stabilization phase officially closed
- Known-good baseline committed to Obsidian
- Operator confirms phase closeout
- Next phase unlocked (per `post_stabilization_implementation_sequence.md`)

**Valid only when:**
- All steps in the phase are COMPLETE
- No open contamination risks
- Baseline archived

---

## 3.6 !msn Rules (Master Stabilization Next)

`!msn` advances to the next step in the active stabilization phase.

**Governs:**
- Activates step N+1
- Posts step N+1 brief (scope, owner, validation requirements)
- Does NOT close step N — step N must be marked COMPLETE separately

**Valid only when:**
- Step N is confirmed COMPLETE

---

## 3.7 Active-Step Governance

At any moment, exactly one step is ACTIVE per active phase.

**Active step rules:**
- Only the active step may receive implementation work
- Implementation on a non-active step is a governance violation
- If scope creep is discovered (work needed outside active step), escalate to operator before proceeding

---

---

# 4. Command System Doctrine

## 4.1 Command Registry

### `!mp` — Master Progress
**Purpose:** Report full stabilization phase progress.  
**Output:** All steps with status (COMPLETE / ACTIVE / BLOCKED / PENDING), current active step, phase completion percentage.  
**Owner:** Claude  
**Sequencing:** Can be called at any time, does not advance state.  
**Escalation:** N/A — read-only status report.  
**Blocked state:** Reports full blocked state with blocking conditions.

---

### `!rp` — Room Progress
**Purpose:** Report progress within a specific room.  
**Output:** Room name, owner, active task, step status, next action.  
**Owner:** Claude  
**Sequencing:** Can be called at any time.  
**Escalation:** N/A — read-only.  
**Blocked state:** Reports block condition and required resolution.

---

### `!c` — Continue
**Purpose:** Advance the active step by executing the next defined action.  
**Output:** Next action taken, result, updated step status.  
**Owner:** Claude (orchestration) / Codex (if action is implementation)  
**Sequencing:** Only valid when a step is ACTIVE and an action is pending.  
**Escalation:** If next action requires protected-system access, escalate before executing.  
**Blocked state:** If step is BLOCKED, `!c` reports block condition — does not attempt to proceed.

---

### `!x` — Execute
**Purpose:** Trigger a specific bounded implementation action.  
**Output:** Action executed, validation result, success/fail.  
**Owner:** Codex (execution) / Claude (doctrine confirmation before execution)  
**Sequencing:** Requires confirmed step scope before execution.  
**Escalation:** If execution touches a protected system, Claude reviews before Codex executes.  
**Blocked state:** Does not execute if step is BLOCKED.

---

### `!p` — Pause
**Purpose:** Pause the active step without marking it complete or failed.  
**Output:** Current step state preserved, pause reason recorded.  
**Owner:** Operator  
**Sequencing:** Freezes active step. No further actions until operator resumes.  
**Escalation:** N/A — operator-only pause.  
**Blocked state:** Records pause as distinct from BLOCKED (blocked = dependency; paused = operator hold).

---

### `!cms` — Complete Step
**Purpose:** Mark the active step COMPLETE.  
**Output:** Step status → COMPLETE, completion timestamp, next step activated.  
**Owner:** Operator (authorization) / Claude (orchestration)  
**Sequencing:** Valid only after completion report posted or operator explicit confirmation.  
**Escalation:** If open FAIL items exist, `!cms` prompts escalation before accepting.  
**Blocked state:** Cannot be called on a BLOCKED step.

---

### `!xms` — Exit Master Stabilization
**Purpose:** Close the current stabilization phase entirely.  
**Output:** Phase status → COMPLETE, baseline archived, next phase unlocked.  
**Owner:** Operator (authorization) / Claude (orchestration)  
**Sequencing:** Valid only when ALL steps in phase are COMPLETE.  
**Escalation:** If any step is not COMPLETE, `!xms` reports the gap and does not close.  
**Blocked state:** Blocked until all steps COMPLETE.

---

### `!msn` — Master Stabilization Next
**Purpose:** Activate the next step after current step is COMPLETE.  
**Output:** Next step brief posted (scope, owner, validation requirements, success criteria).  
**Owner:** Claude  
**Sequencing:** Valid only after current step is confirmed COMPLETE.  
**Escalation:** If next step requires protected-system access, brief includes escalation requirements.  
**Blocked state:** Cannot activate next step if current step is not COMPLETE.

---

### `!ca` — Claude Action
**Purpose:** Trigger a Claude-owned action (doctrine, governance, analysis, review).  
**Output:** Varies by action type. Always produces a written artifact or decision.  
**Owner:** Claude  
**Sequencing:** Can be called at any time for Claude-domain work.  
**Escalation:** If action requires Codex execution downstream, hands off with documented scope.  
**Blocked state:** Claude actions run even in BLOCKED steps (planning/doctrine work continues).

---

### `!xa` — Codex Action
**Purpose:** Trigger a Codex-owned implementation action.  
**Output:** Implementation complete, validation result.  
**Owner:** Codex (execution) / Claude (doctrine compliance check)  
**Sequencing:** Requires active step and confirmed scope.  
**Escalation:** Claude reviews before Codex executes on any protected system.  
**Blocked state:** Does not execute if step is BLOCKED.

---

### `!add` — Add to Queue
**Purpose:** Add a task or item to the active step's work queue.  
**Output:** Item added, queue updated, operator notified.  
**Owner:** Operator  
**Sequencing:** Can be called at any time. Items queued for active or future steps.  
**Escalation:** If item requires scope extension, Claude flags before adding to active step.  
**Blocked state:** Items added to blocked steps are queued, not executed.

---

### `!list` — List Queue
**Purpose:** List all items in the active step's work queue.  
**Output:** Ordered list of queued items with status (pending / in-progress / complete).  
**Owner:** Claude  
**Sequencing:** Read-only. Can be called at any time.  
**Escalation:** N/A.  
**Blocked state:** Reports queue regardless of step state.

---

---

# 5. AI Sequencing Doctrine

## 5.1 Workflow Type Definitions

### Doctrine-First Workflow
**When:** New room initialization, new governance layer, cross-system architectural decisions.  
**Sequence:**
1. Claude authors doctrine (room spec, governance rules, escalation hierarchy)
2. Operator reviews and approves doctrine
3. Codex receives bounded implementation scope from doctrine
4. Codex implements
5. Playwright/audit validates
6. Claude reviews output against doctrine
7. Operator confirms step complete

**Rule:** Implementation never begins before doctrine is approved.

---

### Implementation-First Workflow
**When:** Bug fix, regression repair, display-only patch within an already-doctrined system.  
**Sequence:**
1. Claude confirms task is within existing doctrine scope (or escalates if not)
2. Codex receives bounded task definition
3. Codex implements
4. Audit scripts / Playwright validates (if touching render layer)
5. Claude confirms output is doctrine-compliant
6. Operator confirms step complete

**Rule:** Only valid for tasks already within an existing governance boundary.

---

### Stabilization-First Workflow
**When:** Rerender regression, session_state contamination, cache corruption.  
**Sequence:**
1. Claude defines containment boundary (what is affected, what is safe)
2. Codex executes containment (lazy gates, ownership locks, cache isolation)
3. Playwright validates rerender count and render stability
4. Audit scripts confirm no regression
5. Claude posts stabilization completion report
6. Operator confirms baseline

**Rule:** No new features added during stabilization. Containment only.

---

### Validation-First Workflow
**When:** Starting a new phase, auditing after a contamination event, confirming a known-good baseline.  
**Sequence:**
1. Claude defines validation scope (which systems, which scripts, which Playwright suites)
2. Playwright runs defined suites
3. Audit scripts run (`audit_pitch_mix.py`, `monitoring_dashboard.py`, etc.)
4. Claude reviews all outputs
5. Operator confirms baseline status
6. Phase or implementation begins only after baseline confirmed

**Rule:** Baseline must be confirmed before any implementation in the phase.

---

## 5.2 Parallelization Rules

**Permitted parallel work:**
- Claude doctrine authorship + Codex implementation (in separate, non-overlapping rooms)
- Playwright passive monitoring + active implementation (Playwright does not write to app.py)
- Operations room (07) data pipeline work + frontend room (06) display changes (if no shared session_state keys)

**Forbidden parallelization:**
- Two Codex implementations touching the same file simultaneously
- Codex touching routing + session_state in the same step
- Claude authoring doctrine for a room while Codex is implementing in that room without a confirmed handoff
- Playwright suite updates + Codex implementation in the same render path simultaneously
- Any parallel work touching hydration, routing, or cache ownership

---

## 5.3 Orchestration Authority

Claude has final say on sequencing. If Codex or Playwright output conflicts with the defined sequence, Claude pauses and documents the conflict before proceeding.

Operator has override authority on all orchestration decisions.

---

---

# 6. Validation Governance Doctrine

## 6.1 Validation Hierarchy

```
Level 1: Compile / Type Check
Level 2: Unit / Audit Script
Level 3: Runtime Smoke Test
Level 4: Playwright Browser Validation
Level 5: Operator Confirmation
```

All five levels are required for changes touching session_state, routing, or protected systems. Lower-risk display-only changes may skip Level 4 with operator approval.

---

## 6.2 What Requires Each Level

### Compile / Type Check (always required)
- All Python changes
- All TypeScript/React changes
- Required before any commit

### Audit Script Validation (required for model and render changes)
- `audit_pitch_mix.py` — all 7 tests must pass after any pitch-related change
- `monitoring_dashboard.py Phase 4` — after calibration bucket changes
- `analyze_calibration.py --analyze-only` — after any model signal weight change
- `analyze_live_roi.py` — after schema or pick_tracker changes

### Runtime Smoke Test (required for app.py changes)
- `streamlit run app.py` must render without exception
- All 3 engine views must load
- Sidebar must initialize without session_state error
- No rerender loop on cold load

### Playwright Browser Validation (required for protected systems)
- Any routing change
- Any navigation continuity change
- Any session_state ownership change
- Any breadcrumb or escalation jump change
- Any mobile degradation risk
- Any deployment panel change

### Operator Confirmation (always required for step close)
- No step is COMPLETE without operator confirmation
- Playwright passing alone does not close a step
- Audit scripts passing alone do not close a step

---

## 6.3 AppTest vs Playwright

**AppTest:**
- Headless, fast, CI-friendly
- Tests widget rendering, session_state mutations, filter logic
- Does NOT test visual hover states, animation timing, or mobile layout
- Use for: session_state ownership assertions, widget registration counts, filter output correctness

**Playwright:**
- Browser-driven, full visual environment
- Tests hover states, click feedback, navigation flow, rerender visual artifacts
- Slower — use for complete interaction flows, not per-change regression
- Use for: escalation jump validation, breadcrumb accuracy, deployment panel flow, mobile layout

**Rule:** AppTest runs on every PR. Playwright runs on every step completion for protected system changes.

---

---

# 7. Audit & Recovery Doctrine

## 7.1 Audit Workflow

**Standard audit (run monthly or after any multi-file change):**
1. Run `py -3.12 monitoring_dashboard.py` — 6-phase health check
2. Run `py -3.12 audit_pitch_mix.py` — 7 pitch mix tests
3. Run `py -3.12 analyze_live_roi.py` — ROI and calibration status
4. Run `py -3.12 ops_daily.py --report-only` — operational health
5. Claude reviews all outputs
6. Operator confirms audit complete

**Architecture audit (run after any protected system change):**
1. Identify all files changed in the protected system
2. Claude reviews each change against doctrine in the relevant room doc
3. Flag any doctrine violation (not just bugs — pattern violations too)
4. Operator resolves each flag before step close

**Contamination audit (run after any suspected cross-system contamination):**
1. Identify the contamination boundary (which files, which session_state keys)
2. Claude traces all downstream effects of the contamination
3. Codex executes rollback if needed (bounded to contaminated files only)
4. Re-run all audit scripts
5. Playwright validation of affected render paths
6. Operator confirms clean state

---

## 7.2 Rollback Doctrine

**Rollback is bounded.** Never roll back more than the contaminated scope.

**Rollback sequence:**
1. Identify the last known-good baseline (from `known_good_baseline_definition.md`)
2. Claude defines the rollback boundary (exactly which files are in scope)
3. Operator authorizes rollback in writing
4. Codex executes rollback (git revert or targeted file restore — never `git reset --hard` without operator authorization)
5. Audit scripts confirm clean state
6. Playwright validates protected systems
7. Operator confirms rollback complete

**Hard rule:** Never roll back a file that was not in the contamination boundary. Contamination is not a license for broad cleanup.

---

## 7.3 Known-Good Baseline

Maintained in `known_good_baseline_definition.md`.

**Baseline is updated when:**
- A stabilization phase closes (`!xms`)
- A validated clean state is confirmed after a recovery event
- A major room completes and all audit scripts pass

**Baseline contents:**
- Git commit hash
- Date
- List of protected systems confirmed stable
- Audit script outputs (summary)
- Playwright suite status

---

## 7.4 Recovery Hierarchy

```
Level 1: Config rollback
    (CALIBRATION_ENABLED=False, CONTEXT_MODERATION_ENABLED=False, etc.)
    Zero code change. Instant. Use first.

Level 2: Single-file revert
    (Revert specific model or app.py edit)
    Targeted. Low blast radius.

Level 3: Module revert
    (Revert a full module — engine/calibration.py, portfolio/optimizer.py)
    Confirm no downstream dependencies before executing.

Level 4: Baseline restore
    (Restore to last known-good commit)
    Operator authorization required. Full audit after restore.
```

---

---

# 8. Runtime Protection Doctrine

## 8.1 Protected Systems Registry

| System | Owner | Modification Authority | Stabilization Requirement |
|---|---|---|---|
| Routing (`app.py` engine dispatch) | Claude (doctrine) / Codex (impl) | Claude review required | Playwright validation |
| session_state ownership | Claude (doctrine) | Claude review + operator sign-off | Playwright + AppTest |
| Hydration systems | Claude (doctrine) | Claude review required | Playwright |
| Cache ownership | Claude (doctrine) / Codex (impl) | Claude review required | AppTest |
| Navigation continuity | Claude (doctrine) | Cross-engine context doc approval | Playwright |
| Trust-state systems | Claude (doctrine) | Operator sign-off | Playwright |
| Full Slate orchestration | Claude (doctrine) / Codex (impl) | `full_slate_parent_orchestrator_doctrine.md` compliance | Playwright |
| Deployment lifecycle | Claude (doctrine) / Codex (impl) | `deployment_trust_hierarchy.md` compliance | Playwright |

---

## 8.2 Protected-Zone Rules

1. **No modification without doctrine review.** Any change to a protected system requires Claude to confirm doctrine compliance before Codex executes.

2. **No scope creep into protected zones.** If a non-protected task touches a protected system, escalate immediately — do not proceed silently.

3. **One protected system per step.** A step may not modify two protected systems simultaneously.

4. **Protected systems require Playwright validation.** Audit scripts alone are not sufficient.

5. **Protected systems require operator confirmation.** Claude + Playwright passing does not close a step touching a protected system.

---

## 8.3 Escalation Rules for Protected Systems

If implementation must touch a protected system:
1. Claude documents exactly what is being changed and why
2. Claude identifies all downstream effects
3. Operator authorizes in writing before Codex proceeds
4. Codex executes the minimum necessary change
5. Playwright validates
6. Claude confirms doctrine compliance
7. Operator confirms step complete

---

---

# 9. Workforce Escalation Doctrine

## 9.1 Escalation Severity Levels

| Level | Trigger | Response Time | Owner |
|---|---|---|---|
| INFO | Minor deviation, no runtime impact | Next step | Claude log |
| WARNING | Doctrine violation detected, no immediate regression | Before step close | Claude + operator review |
| CRITICAL | Runtime regression, rerender loop, protected system contamination | Immediate | Claude containment → operator authorization → Codex repair |
| EMERGENCY | Data loss risk, deployment corruption, baseline destroyed | Immediate halt | Operator authorization required before any action |

---

## 9.2 Implementation Escalation

**Trigger:** Codex discovers that the task as defined requires touching a protected system not in scope.

**Response:**
1. Codex halts immediately — does not proceed
2. Codex reports exact discovery to Claude
3. Claude reviews and determines: (a) scope extension authorized, (b) scope must be narrowed, or (c) blocked pending operator decision
4. Operator decides
5. Implementation resumes (or blocked)

**Hard rule:** Codex does not self-authorize scope extensions touching protected systems. Ever.

---

## 9.3 Runtime Emergency Response

**Trigger:** App fails to render, rerender loop detected, exception on load.

**Response sequence:**
1. Claude identifies blast radius (which systems affected)
2. Config rollback attempted first (Level 1 recovery)
3. If config rollback insufficient: single-file revert (Level 2)
4. Playwright runs to confirm clean state
5. Operator confirms recovery before next step begins

---

## 9.4 Rerender-Loop Response

**Trigger:** Rerender audit shows > 2 rerenders per filter change, or Playwright detects spinner/flicker loop.

**Response:**
1. Claude identifies the widget causing the loop (via AppTest widget registration count)
2. Codex inserts lazy gate at the identified widget
3. Rerender audit re-run
4. Playwright validates stable render
5. Operator confirms before proceeding

---

## 9.5 Contamination Handling

**Trigger:** A change in system A causes unexpected behavior in system B (cross-system contamination).

**Response:**
1. Claude defines contamination boundary precisely
2. All implementation halts in both systems
3. Contamination audit runs (Section 7.1)
4. Claude determines if rollback is needed
5. Operator authorizes rollback scope
6. Codex executes rollback
7. Full audit confirms clean state
8. Operator confirms before resuming

---

## 9.6 Blocked-State Handling

**Trigger:** A required dependency is not yet complete, or operator has paused a step.

**Allowed while blocked:**
- Doctrine authorship
- Spec writing
- Analysis scripts (read-only)
- Planning for the blocked step

**Not allowed while blocked:**
- Implementation in the blocked step
- Proceeding to the next step
- Running Playwright validation for the blocked step's features

---

---

# 10. Obsidian Governance Doctrine

## 10.1 Role Definition

Obsidian is the operational memory and governance layer for MLB HR ENGINE.

**Obsidian is:**
- Operational memory (all doctrine, specs, decisions, audit history)
- Governance layer (room registry, baseline history, escalation records)
- Architecture brain (cross-room linking, decision audit trail)

**Obsidian is NOT:**
- Runtime source of truth (GitHub/repo owns that)
- A scratchpad or temporary notes system
- A substitute for in-code documentation

---

## 10.2 Vault Structure

```
MLB HR ENGINE Vault/
├── 00_INDEX/
│   ├── master_room_registry.md
│   ├── active_step_status.md
│   └── known_good_baseline.md
├── 01_DOCTRINE/
│   ├── ai_workforce_orchestration_doctrine_v1.md  ← this doc
│   ├── cross_engine_command_surface_doctrine.md
│   ├── full_slate_parent_orchestrator_doctrine.md
│   ├── escalation_jump_doctrine.md
│   ├── deployment_trust_hierarchy.md
│   └── [all other doctrine docs]
├── 02_SPECS/
│   ├── [all spec_*.md files]
├── 03_DECISIONS/
│   ├── [decision records by date]
├── 04_AUDIT_HISTORY/
│   ├── [timestamped audit outputs]
├── 05_VALIDATION_HISTORY/
│   ├── [Playwright results, AppTest results by step]
├── 06_BASELINE_ARCHIVE/
│   ├── [known-good baselines with git hash + date]
├── 07_AI_COORDINATION/
│   ├── [step handoff records, escalation logs]
└── 08_OPERATIONAL_LOGS/
    ├── [ops_daily.py reports, monitoring dashboard outputs]
```

---

## 10.3 Indexing Rules

- Every doctrine document added to vault must have an entry in `master_room_registry.md`
- All cross-references use exact filenames (not informal descriptions)
- Decision records include: date, decision, reasoning, who authorized
- Baseline archive entries include: git hash, date, systems confirmed stable, audit summary

---

## 10.4 AI Coordination Documents

Stored in `07_AI_COORDINATION/`.

Contents:
- Step handoff records (Claude → Codex): scope definition, doctrine references, success criteria
- Escalation logs: trigger, response, resolution, duration
- Contamination records: affected systems, rollback executed, resolution confirmed

**Purpose:** These records let a future Claude instance reconstruct the decision history without re-deriving it from the codebase.

---

## 10.5 Cross-Linking Standards

- Every doctrine document links to its upstream dependencies in the header `Cross-references:` block
- Every spec links to the room it belongs to
- Every decision record links to the doctrine it affected
- Every audit result links to the step it was run during

**Standard link format:** `[[filename_without_extension]]` (Obsidian wiki-link syntax)

---

## 10.6 Obsidian vs GitHub

| Item | Lives in | Reason |
|---|---|---|
| Runtime code | GitHub | Source of truth for execution |
| Doctrine docs | Both (Obsidian primary, Docs/ in repo as secondary) | Obsidian for linked memory; repo for version control |
| Audit outputs | Obsidian | Not part of runtime — operational history only |
| Known-good baselines | Obsidian + CLAUDE.md | Must survive repo changes |
| Specs | Both | Same as doctrine docs |
| Decisions | Obsidian only | Not code — governance history |

---

---

# 11. Validation Checklist

## Step Completion Validation Checklist

Use this checklist before calling `!cms` on any step.

### Always Required
- [ ] Implementation matches the bounded scope defined for this step
- [ ] No files modified outside the defined scope
- [ ] Compile check passes (no Python errors, no TypeScript errors)
- [ ] Audit scripts relevant to this step have been run and results reviewed
- [ ] Claude has confirmed doctrine compliance for all changes
- [ ] Completion report has been posted

### Required for Model Changes
- [ ] `analyze_calibration.py --analyze-only` run and reviewed
- [ ] `monitoring_dashboard.py Phase 4` shows no new critical drift
- [ ] Config rollback flags tested (feature can be disabled without runtime error)
- [ ] Brier score improvement confirmed on held-out data

### Required for App.py Changes
- [ ] `streamlit run app.py` renders without exception
- [ ] All 3 engine views load (MAIN, JIG, FULL SLATE)
- [ ] `audit_pitch_mix.py` — all 7 tests pass
- [ ] Rerender count for filter change ≤ 2 seconds
- [ ] No session_state key added to a namespace owned by another system

### Required for Protected System Changes
- [ ] Playwright suite run and results reviewed
- [ ] Operator has explicitly authorized the protected system change
- [ ] Cross-system contamination audit complete
- [ ] Known-good baseline updated

### Always Required for Step Close
- [ ] Operator has confirmed step complete (not AI-only confirmation)

---

---

# 12. Runtime Contamination Risks

## 12.1 High-Risk Contamination Patterns

### Pattern 1: session_state Namespace Collision
**Risk:** Two systems writing to the same session_state key.  
**Signature:** Intermittent state reset, unexpected filter resets on engine switch.  
**Prevention:** Every session_state key is owned by exactly one system. New keys require namespace declaration before use.  
**Detection:** AppTest widget registration count spike; `st.session_state` key audit.

### Pattern 2: Routing Logic Leak
**Risk:** Engine dispatch logic modified to accommodate a display change.  
**Signature:** One engine rendering another engine's components; breadcrumb mismatch.  
**Prevention:** Routing changes require Claude review and operator authorization. Display changes never modify routing.  
**Detection:** Playwright breadcrumb validation; engine-switch context persistence test.

### Pattern 3: Cache Ownership Violation
**Risk:** A module writes to a cache key owned by another module.  
**Signature:** Stale data in one engine after refresh in another; hydration state mismatch.  
**Prevention:** Cache keys declared in ownership registry. No module writes to another module's cache key.  
**Detection:** `audit_pitch_mix.py`; manual cache inspection after multi-engine session.

### Pattern 4: Scope Creep During Bug Fix
**Risk:** A bounded bug fix touches a protected system to "clean up" adjacent code.  
**Signature:** Unexpected behavior in unrelated system after a targeted fix.  
**Prevention:** Surgical-change doctrine enforced (see global CLAUDE.md). Every changed line traces to the task.  
**Detection:** Git diff review by Claude before step close.

### Pattern 5: Parallel Implementation Contamination
**Risk:** Two Codex implementations running simultaneously modify the same file.  
**Signature:** Merge conflicts; overlapping logic; duplicated session_state keys.  
**Prevention:** One active step per phase. No parallel implementations in shared files.  
**Detection:** Git conflict detection; step-overlap check.

### Pattern 6: Doctrine Drift Under Implementation Pressure
**Risk:** Codex deviates from doctrine to "make it work" under time pressure.  
**Signature:** Implementation that works functionally but violates ownership or namespace rules.  
**Prevention:** Claude reviews all implementation against doctrine before step close.  
**Detection:** Doctrine compliance review in step completion checklist.

---

## 12.2 Contamination Risk by Phase

| Phase | Highest Risk Area | Mitigation |
|---|---|---|
| Phase 1 (Shell Enhancements) | session_state namespace (new lazy gates) | AppTest widget count check |
| Phase 2 (Validation Expansions) | Calibration param drift (model changes from re-fit) | Config rollback flags always present |
| Phase 3 (Tactical Rendering) | JIG → MAIN render bleed | Filter isolation test |
| Phase 4 (Scroll Restoration) | session_state namespace (new restoration stack) | Namespace pre-declaration required |
| Phase 5+ (Modularization) | Cross-file import contamination | One module per step; audit after each |

---

---

# 13. Workforce Orchestration Hierarchy Summary

## 13.1 Authority Hierarchy

```
OPERATOR
    │
    │ (final authority — all decisions)
    │
CLAUDE
    │
    │ (doctrine authority — governance, sequencing, scope)
    │
    ├── CODEX
    │       │
    │       │ (implementation authority — bounded runtime)
    │
    └── PLAYWRIGHT
            │
            (validation authority — browser-observable behavior)
```

---

## 13.2 Workflow Orchestration Sequence

```
OPERATOR assigns task
    ↓
CLAUDE reviews against doctrine
    ↓
CLAUDE defines scope boundary + success criteria
    ↓
OPERATOR confirms scope (or redirects)
    ↓
CODEX executes bounded implementation
    ↓
PLAYWRIGHT validates (if protected system)
AUDIT SCRIPTS validate (always)
    ↓
CLAUDE reviews implementation against doctrine
    ↓
CLAUDE posts completion report
    ↓
OPERATOR confirms step complete
    ↓
!cms → next step activates
```

---

## 13.3 Escalation Flow

```
Discovery of issue
    ↓
CODEX halts + reports to CLAUDE
    ↓
CLAUDE assesses severity (INFO / WARNING / CRITICAL / EMERGENCY)
    ↓
CLAUDE defines containment boundary
    ↓
OPERATOR authorizes response
    ↓
CODEX executes containment (bounded)
    ↓
PLAYWRIGHT validates clean state
    ↓
CLAUDE confirms recovery
    ↓
OPERATOR confirms before resuming
```

---

## 13.4 The Governing Principle

The workforce system is not a productivity tool. It is a stability system.

Its purpose is to ensure that the operator always has:
- **Clarity** — who owns what, who is doing what, what the current state is
- **Control** — nothing happens without authorization
- **Predictability** — sequencing is deterministic, not emergent
- **Recovery** — any regression can be identified and reversed within one step

The workforce system succeeds when the operator feels **confident, not surprised**.

---

*Document Owner: Claude*  
*Next Room: 09 — Controlled Modularization Planning*  
*Phase: 3A Step 05/10 → COMPLETE pending operator confirmation*
