# Production Extraction Readiness & Controlled Deployment Doctrine v1

**Division:** 09 — Controlled Modularization Planning  
**Owner:** Claude  
**Status:** FINAL — GOVERNANCE ONLY  
**Date:** 2026-05-23  
**Scope:** Authorization framework for production modularization deployment

---

## Cross-Reference: Prior Governance Chain

This doctrine is the terminal link in the governance chain. It depends on and enforces all prior doctrines:

| Doctrine | File | Role |
|---|---|---|
| Controlled Modularization | `controlled_modularization_doctrine_v1.md` | Architecture targets |
| Dependency Audit | `modularization_dependency_audit_doctrine_v1.md` | Dependency governance |
| Extraction Execution | `extraction_execution_governance_doctrine_v1.md` | Extraction rules |
| Runtime Isolation Boundary | `runtime_isolation_boundary_doctrine_v1.md` | Protected zone law |
| Validation & Runtime Verification | `validation_runtime_verification_doctrine_v1.md` | Validation sequencing |
| Phase 1 Extraction Prioritization | `phase1_extraction_prioritization_doctrine_v1.md` | Extraction ordering |

**This doctrine adds:** when extraction may begin, how deployment is governed, who authorizes advancement, when extraction must stop.

---

## Section 1 — Purpose of Production Readiness Governance

### 1.1 Why Extraction Readiness Matters

Modular architecture exists to reduce long-term coupling debt. But premature extraction — moving code before the runtime is stable, before dependencies are audited, before rollback paths are verified — does not reduce risk. It transfers runtime risk into structural risk where failures are harder to detect and harder to reverse.

Production readiness governance exists to enforce a mandatory gap between "planning complete" and "extraction authorized." That gap is not bureaucratic delay. It is the period during which the operator confirms the runtime is actually trustworthy, not merely assumed to be.

### 1.2 Why Governance Must Precede Deployment

Every prior doctrine in this chain is a planning artifact. Planning establishes intent. Governance establishes authorization. Without explicit authorization governance:

- Extraction may begin while the runtime is still experiencing residual instability
- Multiple extraction operations may contaminate each other's attribution
- Rollback paths may be assumed but never verified
- "Safe" declarations may be made based on absence of failures rather than confirmed stability

This doctrine closes that gap. No extraction deployment may proceed without satisfying the authorization workflow defined here.

### 1.3 Why Stabilization Trust Matters More Than Extraction Speed

Speed of modularization has zero value if the runtime degrades during extraction. A monolithic stable runtime is operationally superior to a partially modular unstable runtime. Every extraction must leave the runtime in equal or better condition than it found it. This is non-negotiable.

Stabilization trust is earned through observation, not declared by intent. The runtime must demonstrate stability over time before extraction is authorized. A runtime that "seems fine" is not the same as a runtime confirmed stable through observation windows.

### 1.4 Why "Technically Possible" ≠ "Operationally Safe"

An extraction may be technically straightforward — isolated module, no circular imports, clean interface — and still be operationally unsafe if:

- The runtime baseline was measured during an unstable period
- The validation scaffold has not been run against current code
- The rollback procedure has not been dry-run
- The operator has not confirmed current state

Technical possibility answers "can this be moved?" Operational safety answers "is this the right moment to move it?" This doctrine governs the second question.

---

## Section 2 — Production Readiness Philosophy

### 2.1 Core Laws

**LAW 1 — Stabilization Before Extraction**  
No extraction begins until the runtime has completed a confirmed stability window. Stability windows are defined in Section 5. This law has no exceptions.

**LAW 2 — Rollback-First Deployment**  
Every extraction must have a verified rollback path before deployment begins. "We can undo it if needed" is not a verified rollback path. The rollback procedure must be documented and confirmed executable before extraction starts.

**LAW 3 — One-Extraction Authority**  
Only one extraction operation may be active at any time across all protected zones. This is not a recommendation. See Section 6.

**LAW 4 — Runtime Trust Over Modular Purity**  
If an extraction improves architectural purity but introduces runtime uncertainty, runtime trust wins. The extraction is deferred. Purity goals are secondary to operational continuity.

**LAW 5 — Operator-Confirmed Deployment Safety**  
AI may recommend extraction readiness. Only the operator may authorize deployment. This authority is non-delegable. See Section 4.

**LAW 6 — Extraction Pacing Over Extraction Speed**  
Extraction waves are bounded. Cooldown periods are mandatory. Observation windows are required between deployments. The goal is not to extract everything quickly. The goal is to extract safely, with full runtime trust preserved throughout.

---

## Section 3 — Production Readiness Requirements

All requirements below must be satisfied before extraction authorization may be granted. Partial satisfaction does not constitute readiness.

### 3.1 Mandatory Prerequisites

| Requirement | Description | Verified By |
|---|---|---|
| R1 — Runtime Stabilization Complete | No rerender amplification, route desync, or startup instability observed in prior 48 hours | Operator |
| R2 — Rerender Baseline Stable | Baseline render counts established, no unexplained spikes | Operator |
| R3 — Validation Doctrines Complete | All validation sequences from `validation_runtime_verification_doctrine_v1.md` passed | AI + Operator |
| R4 — Dependency Audits Complete | Full dependency map from `modularization_dependency_audit_doctrine_v1.md` signed off | AI |
| R5 — Rollback Procedures Verified | Each Phase 1 candidate has a documented and confirmed rollback path | AI + Operator |
| R6 — Extraction Scoring Finalized | Priority scores from `phase1_extraction_prioritization_doctrine_v1.md` confirmed current | AI |
| R7 — Extraction Execution Rules Acknowledged | Operator has read and acknowledged `extraction_execution_governance_doctrine_v1.md` | Operator |
| R8 — Runtime Isolation Boundaries Confirmed | Protected zones from `runtime_isolation_boundary_doctrine_v1.md` confirmed unmodified | AI + Operator |
| R9 — Operator Approval Granted | Explicit sign-off per Section 4 workflow | Operator |

### 3.2 Disqualifying Conditions

Any of the following conditions immediately block readiness determination, regardless of other requirements met:

- Active runtime instability of any kind
- Unresolved prior extraction failure
- Pending structural change to `app.py`, `session_state`, or `active_workspace`
- Unsettled dispute about extraction ordering or scope
- Operator unavailable for observation window coverage
- Prior rollback not yet fully resolved

---

## Section 4 — Extraction Authorization Workflow

### 4.1 Authorization Sequence

The following sequence must be completed in order. Steps may not be skipped or reordered.

**Step 1 — Readiness Assessment Request**  
AI performs readiness assessment against all R1–R8 requirements. Produces written assessment with pass/fail per requirement.

**Step 2 — Operator Readiness Review**  
Operator reviews AI assessment. Operator independently confirms R1, R2, R7, R9. Operator may add disqualifying observations not captured by AI assessment.

**Step 3 — Rollback Path Confirmation**  
For the specific extraction being authorized, operator confirms rollback path is understood and executable. This is per-extraction, not global.

**Step 4 — Extraction Scope Declaration**  
AI declares exact scope: which module, which files affected, which interfaces change, which imports change. No undeclared scope changes permitted post-authorization.

**Step 5 — Operator Authorization Grant**  
Operator issues explicit authorization using Production Sign-Off Template (Appendix E). Authorization covers exactly one extraction operation.

**Step 6 — Pre-Deployment Snapshot**  
AI records current runtime state as deployment baseline before touching any file.

### 4.2 Forbidden Authorization Conditions

Authorization must NOT be granted when:

- AI recommends extraction but operator has not independently confirmed runtime stability
- Authorization is verbal/implied rather than explicit
- Authorization covers multiple extractions rather than one
- Authorization is granted under time pressure ("let's just do it")
- Prior extraction observation window has not completed
- Any disqualifying condition from Section 3.2 is active

### 4.3 Blocked-State Conditions

These conditions place extraction in BLOCKED state. No further authorization workflow may proceed until the block is cleared:

| Condition | Block Trigger | Clear Condition |
|---|---|---|
| Active runtime instability | Any freeze condition from Section 7 fires | 48-hour clean observation window post-resolution |
| Failed extraction in progress | Any extraction rollback initiated | Full rollback complete + runtime restored + operator sign-off |
| Protected zone modification | Any touch to isolated zones | Zone restored + operator confirms integrity |
| Ambiguous extraction attribution | Two modifications active simultaneously | Attribution resolved, single author confirmed |

### 4.4 Emergency Freeze Authority

The operator holds unconditional emergency freeze authority at any time. Emergency freeze:

- Immediately halts any in-progress extraction
- Blocks all pending authorizations
- Requires full recovery sequence (Section 12) before resumption
- May not be overridden by AI recommendation

AI also holds advisory freeze authority: AI must immediately flag any freeze-condition symptom detected. Operator retains final decision authority on whether to execute the freeze.

---

## Section 5 — Extraction Deployment Sequencing

### 5.1 Deployment Order Rules

1. Phase 1 candidates extracted in priority order per `phase1_extraction_prioritization_doctrine_v1.md`
2. Lower-risk, lower-dependency extractions precede higher-risk ones regardless of perceived urgency
3. Shared utilities extracted before consumers of those utilities
4. Display-layer modules extracted before data-pipeline modules
5. No extraction skips its position in priority order without operator-approved re-scoring

### 5.2 Extraction Grouping Rules

- **Permitted grouping:** Multiple files that form a single logical module with no external consumers may be extracted together as one atomic operation
- **Forbidden grouping:** Modules with different dependency chains may not be grouped even if adjacent in priority order
- **Grouping requires:** Explicit scope declaration for all files in the group before authorization is granted

### 5.3 Extraction Scheduling

- Extractions must be scheduled during periods of operator availability for observation
- No extraction may begin within 2 hours of a production use session (pick generation, live betting activity)
- No extraction may begin if the operator cannot monitor for the full observation window
- Extractions scheduled but not started within 4 hours must be re-authorized before starting

### 5.4 Extraction Cooldown Periods

| Extraction Type | Minimum Cooldown Before Next Extraction |
|---|---|
| Low-risk utility module | 24 hours |
| Mid-risk display module | 48 hours |
| High-risk pipeline module | 72 hours |
| Any extraction requiring rollback | Full recovery sequence + 48 hours post-recovery |

Cooldown begins after observation window completes, not after extraction completes.

### 5.5 Observation Windows

| Extraction Type | Observation Window |
|---|---|
| Low-risk utility module | 4 hours post-deployment |
| Mid-risk display module | 8 hours post-deployment |
| High-risk pipeline module | 24 hours post-deployment |

During observation window:
- Runtime monitoring is active
- No other extractions may begin
- Operator must be available to respond within 30 minutes if freeze condition detected
- AI observes for freeze triggers (Section 7) and escalates immediately upon detection

### 5.6 Freeze Intervals

Between extraction waves (groups of related extractions):
- Minimum 72-hour freeze before beginning a new extraction wave
- Wave transition requires fresh readiness assessment (Section 3) and new authorization (Section 4)
- Freeze intervals are non-negotiable regardless of apparent runtime health

---

## Section 6 — Extraction Concurrency Doctrine

### 6.1 One Extraction at a Time

Only one extraction operation may be active at any moment. An extraction is "active" from the first file modification until the observation window completes. This is an absolute rule with no exceptions.

**Rationale:** Concurrent extractions make regression attribution impossible. If two modules are extracted simultaneously and a runtime failure occurs, it is impossible to determine which extraction caused it. Attribution clarity is required for safe rollback. Without it, rollback becomes destructive guesswork.

### 6.2 Forbidden Parallel Extraction Zones

The following zone pairs may never have simultaneous active extractions, regardless of claimed independence:

- Any two modules sharing `session_state` read/write paths
- Any two modules in the `Full Slate` rendering chain
- Any two modules sharing `@st.cache_data` decorators or cache keys
- Any module adjacent to `active_workspace` + any other module
- Any module adjacent to `active_route` + any other module
- Any display module + any pipeline module

### 6.3 Allowed Isolated Parallel Domains

These domain pairs may potentially run extractions in close sequence (not simultaneously — One-Extraction Authority still applies) with reduced cooldown between them, subject to operator judgment:

- Standalone utility modules with no shared imports and no shared state
- Documentation-only restructuring (no `.py` file changes)

Note: "Isolated parallel domains" does not mean concurrent. It means the cooldown between them may be shortened to 12 hours if both modules are confirmed fully isolated. Operator must confirm isolation explicitly.

### 6.4 Attribution Clarity Requirements

Every extraction must maintain clear attribution:

- Exactly one AI owns one extraction at a time
- The owning AI declares scope before touching any file
- No second extraction may begin until the owning AI's observation window completes and the owning AI explicitly declares the operation closed
- Closed declaration must include: outcome (success/rollback), files modified, runtime status confirmed

---

## Section 7 — Runtime Freeze Conditions

Any of the following conditions, when detected during or after extraction, triggers an immediate extraction freeze. Freeze means: stop all extraction activity, do not start rollback without operator confirmation, alert operator immediately.

### 7.1 Freeze Trigger Matrix

| Trigger ID | Condition | Detection Signal | Severity |
|---|---|---|---|
| FZ-01 | Rerender Amplification | Render count increases >2x baseline without UI interaction | CRITICAL |
| FZ-02 | Route Desync | `active_route` and displayed workspace diverge | CRITICAL |
| FZ-03 | Startup Instability | App fails to reach operational state within normal startup sequence | CRITICAL |
| FZ-04 | Cache Identity Corruption | `@st.cache_data` returns stale data or wrong data for known inputs | CRITICAL |
| FZ-05 | Tactical Flow Degradation | Full Slate picks fail to render or render incomplete | HIGH |
| FZ-06 | Shell Instability | Navigation shell fails to respond, shows wrong state, or disappears | HIGH |
| FZ-07 | Unexplained State Mutation | `session_state` values change without user action or explicit write | HIGH |
| FZ-08 | Hydration Loop Signature | Repeated identical render cycles with no state change between them | HIGH |
| FZ-09 | Modal Containment Failure | Modal appears outside expected trigger path or fails to dismiss | MEDIUM |
| FZ-10 | Startup Sequence Disorder | Initialization order changes detectably from established baseline | MEDIUM |

### 7.2 Freeze Response By Severity

| Severity | Response |
|---|---|
| CRITICAL | Immediate halt + operator alert + do not touch files until operator responds |
| HIGH | Halt extraction + alert operator + await operator confirmation before rollback |
| MEDIUM | Pause extraction + log condition + operator review before next step |

### 7.3 False Positive Protocol

Not every anomaly is extraction-caused. Before attributing a freeze condition to an extraction:
- Confirm the condition did not exist in pre-extraction baseline
- Confirm no external change occurred (API outage, data feed issue, browser state)
- If causal link to extraction is ambiguous: treat as extraction-caused until proven otherwise

---

## Section 8 — Tactical Runtime Protection

During any extraction operation, the following tactical systems must remain fully operational and unmodified:

### 8.1 Protected Tactical Systems

| System | Protection Requirement |
|---|---|
| Full Slate Readability | Pick tables must render completely with correct data throughout extraction |
| Escalation Hierarchy | All escalation signals must function; no signal may be suppressed by extraction side-effects |
| Shell Continuity | Navigation shell must remain stable; workspace switching must function |
| Command Pacing | All operator commands must execute within normal response time |
| Investigation Flow | All diagnostic tools (backtest, calibration analysis, pick tracking) must remain accessible |
| Tactical Density | Display density and information hierarchy must not shift during extraction |
| Modal Continuity | All modals must open, display correctly, and dismiss correctly |
| Deployment Tracking Continuity | Pick logging, CLV capture, settlement must not be interrupted |

### 8.2 Tactical Degradation = Extraction Halt

Any measurable degradation in the systems listed in 8.1, regardless of whether a freeze trigger (Section 7) has formally fired, is grounds for extraction halt. The operator does not need a formal freeze trigger to stop extraction. Observed tactical degradation is sufficient.

---

## Section 9 — Deployment Rollback Governance

### 9.1 Rollback Authority

Rollback authority is held jointly by operator and AI. Either party may initiate rollback recommendation. Only the operator may authorize rollback execution. AI may not self-initiate file restoration without operator instruction.

Exception: If a CRITICAL freeze condition fires and the operator is unreachable, AI must halt all file modification activity immediately. AI must not attempt rollback unilaterally. AI waits for operator.

### 9.2 Rollback Timing

| Scenario | Rollback Timing |
|---|---|
| CRITICAL freeze fires during extraction | Halt immediately; rollback after operator confirms |
| CRITICAL freeze fires post-extraction (within observation window) | Rollback within 30 minutes of detection |
| HIGH freeze fires during extraction | Pause; operator decides rollback or continue monitoring |
| Extraction produces wrong output (no freeze) | Rollback at operator discretion; document before rollback |
| Extraction completes but cooldown observation reveals degradation | Rollback; reopen observation window post-rollback |

### 9.3 Rollback Escalation

If standard rollback (file restoration) does not resolve the freeze condition:

1. **Level 1 — File Restoration:** Restore modified files to pre-extraction state
2. **Level 2 — Import Map Restoration:** Verify all import paths match pre-extraction baseline
3. **Level 3 — Session State Reset:** Clear session state and restart app; verify baseline behavior
4. **Level 4 — Cache Purge:** Clear all `@st.cache_data` cached values; restart; re-verify
5. **Level 5 — Full Branch Rollback:** Revert to last known stable commit on current branch

Each level must be verified before escalating. Do not skip levels.

### 9.4 Contaminated Runtime Handling

A runtime is "contaminated" when rollback does not restore baseline behavior. Contaminated runtime protocol:

1. Cease all further extraction attempts immediately
2. Document current observable state in full
3. Identify last known clean state (commit, branch, or snapshot)
4. Restore to last known clean state via Level 5 rollback
5. Re-run full readiness assessment (Section 3) before any future extraction
6. Operator must explicitly re-authorize after contamination recovery

### 9.5 Stabilization Restoration Sequencing

After any rollback, restoration must follow this sequence before extraction resumes:

1. Confirm all modified files match pre-extraction state
2. Confirm app starts cleanly with normal startup sequence
3. Confirm Full Slate renders completely
4. Confirm `active_workspace` routing functions
5. Confirm `session_state` values match expected baseline
6. Run validation sequence from `validation_runtime_verification_doctrine_v1.md`
7. Observe 48-hour clean window
8. Issue new readiness assessment
9. Obtain new operator authorization

---

## Section 10 — Extraction Observation Ownership

### 10.1 Operator Responsibilities

During extraction and observation window:

- Monitor application behavior for freeze triggers (Section 7)
- Confirm tactical systems (Section 8) remain intact after extraction
- Report any anomaly to AI immediately, even if not formally a freeze trigger
- Remain available for response within 30 minutes throughout observation window
- Issue close declaration (success or rollback) at observation window end
- Maintain deployment log entries for each extraction

### 10.2 AI Responsibilities

During extraction and observation window:

- Monitor code state for attribution drift (unauthorized changes)
- Flag any freeze trigger detection immediately with trigger ID and evidence
- Do not make additional file modifications during observation window (unless rollback required)
- Produce extraction summary at observation window end: files modified, interfaces changed, runtime status
- Maintain extraction log with scope, authorization reference, and outcome

### 10.3 Runtime Monitoring Ownership

Runtime behavior monitoring (freeze triggers, rerender counts, route sync, startup sequence) is **operator-owned**. AI cannot directly observe Streamlit runtime behavior. AI monitors code artifacts only.

### 10.4 Rerender Observation Ownership

Rerender baseline measurement and rerender amplification detection is **operator-owned**. Operator must report rerender observations to AI if anomalies detected.

### 10.5 Stabilization Sign-Off Ownership

Stabilization sign-off (confirming the runtime is stable and the extraction is clean) is **operator-owned**. AI may recommend sign-off when observation window conditions appear met. Operator decides.

---

## Section 11 — Production Advancement Gates

### 11.1 Phase 1 → Phase 2 Advancement

Phase 2 extraction (higher-risk, deeper modules) may not begin until all Phase 1 gates are satisfied:

| Gate | Requirement |
|---|---|
| G1 — Phase 1 Complete | All Phase 1 priority candidates successfully extracted and observation-window-closed |
| G2 — Stability Window | 72-hour clean stability window after last Phase 1 extraction |
| G3 — Runtime Trust Confirmed | No freeze triggers fired during entire Phase 1 wave |
| G4 — Rollback-Free Record | No Phase 1 extraction required rollback |
| G5 — Calibration Stable | No model calibration drift introduced by Phase 1 changes (if any pipeline modules extracted) |
| G6 — Operator Re-Authorization | Fresh operator sign-off using Production Sign-Off Template (Appendix E) |
| G7 — Phase 2 Readiness Assessment | New full readiness assessment completed and passed |

### 11.2 Advancement-Blocking Conditions

Any of these conditions blocks Phase 2 advancement regardless of all other gates passing:

- Any unresolved rollback from Phase 1
- Any contaminated-runtime incident not fully recovered
- Any freeze trigger that fired and was not root-cause explained
- Operator expressing reservations about runtime trust (subjective signal is valid)
- Insufficient operational data to verify extraction did not introduce subtle degradation

### 11.3 Mandatory Stability Windows

| Transition | Mandatory Stability Window |
|---|---|
| Pre-extraction authorization | 48 hours clean |
| Post-extraction (low-risk) | 24 hours clean |
| Post-extraction (mid-risk) | 48 hours clean |
| Post-extraction (high-risk) | 72 hours clean |
| Phase 1 → Phase 2 | 72 hours clean after last Phase 1 close |
| Post-contamination recovery | 48 hours clean after recovery complete |

"Clean" means: no freeze triggers, no tactical degradation, operator-confirmed.

### 11.4 Runtime Trust Requirements

Runtime trust is not binary. It degrades with each unexplained anomaly and restores with clean observation windows. Advancement requires "high trust" state:

- **High Trust:** Zero freeze triggers in last 72 hours, stable rerenders, operator-confirmed
- **Moderate Trust:** Minor anomalies resolved, no active freeze triggers, operator cautiously positive
- **Low Trust:** Recent unexplained anomaly or unresolved rollback — extraction blocked
- **No Trust:** Active freeze condition or contaminated runtime — all extraction blocked

### 11.5 Extraction Success Requirements

An extraction is "successful" only when:
- Files modified match declared scope exactly
- Runtime behavior matches pre-extraction baseline
- Observation window completed without freeze triggers
- Operator issued explicit close declaration
- No new technical debt introduced by the extraction

---

## Section 12 — Failed Deployment Recovery Doctrine

### 12.1 Failed Extraction Containment

When an extraction fails (rollback required):

1. Halt immediately — do not attempt to "fix forward" with additional changes
2. Declare failed state — AI logs failure with trigger ID, file list, exact failure mode
3. Freeze all extraction activity — no other modules may be touched until recovery complete
4. Preserve evidence — capture current state of all modified files before rollback
5. Notify operator — provide: what was being extracted, what triggered failure, what rollback will do

### 12.2 Contaminated Runtime Recovery Sequence

When standard file rollback does not restore baseline:

**Step 1 — Isolation:** Identify which specific behavior is non-baseline. Do not assume global contamination until confirmed.

**Step 2 — Scope Assessment:** Determine if contamination is isolated to one subsystem or cross-cutting.

**Step 3 — Level Selection:** Select appropriate rollback level from Section 9.3 based on contamination scope.

**Step 4 — Controlled Restoration:** Execute rollback level. Verify after each level before proceeding.

**Step 5 — Baseline Verification:** Run full validation sequence from `validation_runtime_verification_doctrine_v1.md` against restored state.

**Step 6 — Clean Window:** Observe 48-hour clean window post-restoration.

**Step 7 — Root Cause Analysis:** Before any future extraction, document root cause of contamination. This is mandatory, not optional.

**Step 8 — Governance Update:** If contamination reveals a gap in prior governance docs, update affected doctrine before re-authorizing.

### 12.3 Rollback Sequencing (Detailed)

For extraction involving multiple files, rollback must be sequenced in reverse order of modification:

1. Restore last-modified file first
2. Verify import consistency after each file restoration
3. Do not restore all files simultaneously — restore one, verify, continue
4. After all files restored: restart app, verify startup sequence, verify Full Slate, verify routing

### 12.4 Runtime Trust Restoration After Failure

After a failed extraction + full recovery:

- Runtime trust resets to "Moderate Trust" at best
- "High Trust" requires a full 72-hour clean observation window post-recovery
- AI may not declare "High Trust" — operator must confirm
- Phase advancement is blocked until "High Trust" is re-established

### 12.5 Stabilization Reset Conditions

Full stabilization reset (treat runtime as freshly deployed, verify everything from scratch) required when:

- Level 5 branch rollback was executed
- Contamination spread across more than two subsystems
- Operator cannot confirm which behaviors are baseline and which are contamination artifacts
- More than two failed extraction attempts in a single extraction wave

---

## Section 13 — Future Deployment Vision

### 13.1 Safe Continuous Modularization

The long-term target is a codebase where extraction operations are routine, low-risk, and minimally disruptive. This requires:

- **Established extraction patterns:** Repeated successful extractions build operator and AI confidence in the process
- **Shrinking observation windows:** As track record builds and tooling matures, high-risk modules become mid-risk; mid-risk become low-risk
- **Accumulated runtime knowledge:** Each extraction adds to the documented understanding of which systems couple unexpectedly

The current doctrine is conservative by design. As extraction track record accumulates and runtime trust solidifies, specific parameters (cooldown periods, observation windows) may be relaxed via operator-authorized doctrine revision. The core laws (Section 2.1) are permanent.

### 13.2 Bounded Extraction Waves

Rather than continuous rolling extraction, target bounded waves with rest periods:

- **Wave 1 — Phase 1 Utility Extraction:** Low-risk, standalone modules. Establishes extraction competency.
- **Wave 2 — Phase 1 Display Layer:** Display modules with verified isolated interfaces.
- **Wave 3 — Phase 1 Pipeline Modules:** Higher-risk modules; requires Wave 1 + Wave 2 clean record.
- **Phase 2 — After Gate G1–G7 satisfied.** Timeline determined by runtime trust, not calendar.

### 13.3 Automated Extraction Validation

As the project matures:

- **Baseline snapshot tooling:** Automated capture of render counts, session state fingerprints, route state at extraction boundary
- **Regression detection automation:** Automated comparison of pre/post extraction snapshots for drift
- **Import chain validation:** Automated circular import detection after each extraction

These tools reduce observation burden and shorten required observation windows. They do not replace operator judgment.

### 13.4 Runtime Trust Dashboards

Future state: lightweight operational dashboard displaying:

- Current runtime trust level (High/Moderate/Low/None)
- Days since last freeze trigger
- Extraction wave status (active/cooldown/blocked)
- Open observation windows
- Rollback history summary

This visibility converts subjective runtime trust into an observable, trackable metric.

### 13.5 Orchestrated Deployment Governance

As extraction maturity grows:

- **Extraction calendar:** Planned extractions scheduled against operational activity calendar (game days, active betting periods)
- **Pre-extraction briefing pattern:** Standardized pre-extraction checklist (Appendix B) becomes routine rather than exceptional
- **Retrospective review cycle:** Monthly review of extraction history, freeze trigger frequency, rollback rate — feeds back into doctrine refinement

---

## Appendix A — Production Readiness Checklist

Use before initiating authorization workflow (Section 4).

```
PRODUCTION READINESS CHECKLIST
Date: _______________
Extraction Target: _______________
Assessor (AI): _______________
Reviewer (Operator): _______________

RUNTIME STABILITY
[ ] R1 — No rerender amplification in prior 48 hours
[ ] R2 — Rerender baseline documented and stable
[ ] R3 — No route desync observed
[ ] R4 — Startup sequence normal
[ ] R5 — Full Slate renders completely
[ ] R6 — Modal containment functioning

GOVERNANCE PREREQUISITES
[ ] R7 — Validation doctrines complete and passed
[ ] R8 — Dependency audit signed off for this extraction
[ ] R9 — Rollback path documented and confirmed executable
[ ] R10 — Extraction priority score confirmed current
[ ] R11 — Extraction execution rules acknowledged by operator
[ ] R12 — Runtime isolation boundaries confirmed unmodified

DISQUALIFYING CONDITIONS CHECK
[ ] No active runtime instability
[ ] No unresolved prior extraction failure
[ ] No pending structural changes to protected zones
[ ] Operator available for full observation window
[ ] No unsettled scope disputes

RESULT: [ ] READY TO PROCEED TO AUTHORIZATION  [ ] BLOCKED (list blocking items)
```

---

## Appendix B — Extraction Deployment Checklist

Use after authorization granted, before touching any file.

```
EXTRACTION DEPLOYMENT CHECKLIST
Date: _______________
Extraction: _______________
Authorization Reference: _______________
Operator: _______________

PRE-DEPLOYMENT
[ ] Scope declared in full (all files, all imports, all interface changes)
[ ] Rollback path confirmed executable
[ ] Pre-deployment runtime snapshot captured
[ ] No extraction currently in observation window
[ ] Cooldown from prior extraction satisfied

DURING DEPLOYMENT
[ ] One file modified at a time (or atomic group as declared)
[ ] No undeclared scope additions
[ ] Import consistency verified after each file
[ ] No protected zone touched

POST-DEPLOYMENT
[ ] All declared files modified, no extras
[ ] App starts cleanly
[ ] Full Slate renders completely
[ ] Active_workspace routing functions
[ ] Session_state matches expected baseline
[ ] Observation window clock started: _______________

OBSERVATION WINDOW CLOSE
[ ] Observation window duration completed
[ ] No freeze triggers detected during window
[ ] Tactical systems confirmed intact
[ ] Operator close declaration issued
[ ] Extraction logged as: [ ] SUCCESS  [ ] ROLLBACK

ROLLBACK (if required)
[ ] Files restored in reverse modification order
[ ] Import consistency verified post-rollback
[ ] App restarted and baseline confirmed
[ ] Root cause documented
[ ] Contamination scope assessed
```

---

## Appendix C — Runtime Freeze Trigger Matrix

| ID | Trigger | Signal | Severity | Response |
|---|---|---|---|---|
| FZ-01 | Rerender Amplification | Render count >2x baseline without interaction | CRITICAL | Halt + Alert |
| FZ-02 | Route Desync | `active_route` ≠ displayed workspace | CRITICAL | Halt + Alert |
| FZ-03 | Startup Instability | App fails normal startup | CRITICAL | Halt + Alert |
| FZ-04 | Cache Identity Corruption | `@st.cache_data` wrong output for known input | CRITICAL | Halt + Alert |
| FZ-05 | Tactical Flow Degradation | Full Slate fails to render or renders incomplete | HIGH | Halt + Alert |
| FZ-06 | Shell Instability | Navigation shell fails or shows wrong state | HIGH | Halt + Alert |
| FZ-07 | Unexplained State Mutation | `session_state` changes without user action | HIGH | Halt + Alert |
| FZ-08 | Hydration Loop Signature | Repeated identical render cycles | HIGH | Halt + Alert |
| FZ-09 | Modal Containment Failure | Modal outside expected trigger path | MEDIUM | Pause + Log |
| FZ-10 | Startup Sequence Disorder | Init order changes from baseline | MEDIUM | Pause + Log |

**All triggers pause extraction. CRITICAL triggers require operator confirmation before rollback.**

---

## Appendix D — Failed Deployment Recovery Example

**Scenario:** Module `output/ranker.py` extracted to `modules/ranker.py`. Post-extraction, Full Slate renders but picks display with wrong sort order (FZ-05 — Tactical Flow Degradation, HIGH).

**Step 1 — Halt:** AI halts. No further changes. Freeze declared.

**Step 2 — Alert:** AI reports to operator: "FZ-05 detected. Full Slate renders but sort order incorrect. Trigger: likely import path change in `pipeline.py` referencing old `output/ranker.py` location not updated. Rollback recommended."

**Step 3 — Operator Confirms Rollback.** Operator authorizes Level 1 rollback.

**Step 4 — Restore:**
1. Restore `pipeline.py` import to `output/ranker.py`
2. Verify import consistency
3. Restart app
4. Verify Full Slate sort order correct

**Step 5 — Baseline Verified.** Full Slate renders with correct sort order. Baseline confirmed.

**Step 6 — Root Cause:** Import path in `pipeline.py` not updated in declared scope. Scope declaration was incomplete — only `ranker.py` moved, but `pipeline.py` import not included in scope.

**Step 7 — Governance Update:** Add to extraction execution governance: "Import updates in consumers must be included in extraction scope declaration, not treated as post-extraction follow-up."

**Step 8 — Trust Reset.** Moderate Trust. 48-hour clean window required before re-authorization. Re-authorization must include `pipeline.py` import in declared scope.

---

## Appendix E — Production Sign-Off Template

```
PRODUCTION EXTRACTION SIGN-OFF
================================
Date: _______________
Time: _______________
Operator: _______________
AI Session: _______________

EXTRACTION BEING AUTHORIZED
Module: _______________
Files to be modified:
  - _______________
  - _______________
Import changes:
  - _______________
Interface changes:
  - _______________

READINESS CONFIRMATION
[ ] Completed Production Readiness Checklist (Appendix A) — PASS
[ ] Rollback path confirmed: _______________
[ ] No disqualifying conditions active
[ ] Prior extraction observation window complete (or first extraction)
[ ] Cooldown period satisfied

OPERATOR DECLARATIONS
[ ] I have independently verified runtime stability in the prior 48 hours
[ ] I understand the rollback path and can execute it
[ ] I am available for the full observation window
[ ] I have read the extraction scope declaration and it is complete

AUTHORIZATION
This sign-off authorizes exactly one extraction operation as declared above.
It does not authorize any undeclared scope, any additional modules, or any
modifications to protected runtime zones.

Operator Signature (name): _______________
Authorization Time: _______________
Observation Window End (scheduled): _______________

POST-EXTRACTION CLOSE DECLARATION
[ ] SUCCESS — extraction complete, observation window clean
[ ] ROLLBACK — extraction failed, rollback complete, root cause documented

Close Declaration Time: _______________
Runtime Trust Level at Close: [ ] High  [ ] Moderate  [ ] Low
```

---

*Doctrine Version 1 — Production Extraction Readiness & Controlled Deployment*  
*Governance Only — No Production Modifications*  
*Next Review: After Phase 1 Wave 1 completion or 90 days, whichever comes first*
