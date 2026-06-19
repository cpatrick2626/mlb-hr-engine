# LOOPS.md

> **AUTHORITATIVE.** Claude Skills, account memory, and chat history are secondary consumers and must point here, not redefine these loops. Portable across Claude PM, Claude Code, ChatGPT, Gemini, and future agents. One-source-of-truth: each loop has ONE home — this file.

Last updated: 2026-06-19

---

## Loop 1 — Root-Cause Investigation

**Purpose:** Find the true cause before any fix.

1. Reproduce the failure in a known-good state.
2. Observe exact symptoms; record precise error text, file, and line.
3. Trace execution path from entrypoint to failure site.
4. List all candidate causes — do not prune early.
5. Gather evidence for and against each candidate (read-only).
6. ⛔ **GATE:** Do not write code until root cause is confirmed and operator has reviewed the diagnosis.
7. Confirm root cause with evidence.
8. Recommend the smallest safe fix: fewest files touched, existing behavior preserved, no scope expansion beyond the confirmed cause.
9. Implement only the confirmed fix.
10. Verify the fix resolves the original failure and introduces no regressions.

**Safe Production Engineer rule (lives here, not as a separate skill):** Minimum scope. Fewest files. Preserve existing behavior. Never patch symptoms. Never assume cause.

---

## Loop 2 — Validation Before Deploy

**Purpose:** No change ships unvalidated.

1. Review the change diff in full.
2. Identify all affected files and surfaces.
3. Review validation evidence — test output, manual verification, log confirmation.
4. Assess deploy risk: which surfaces are touched, what can silently regress.
5. Document any unverified areas explicitly. Evidence over assumption.
6. ⛔ **GATE:** Binary readiness decision — READY or BLOCKED (with stated reason). Do not deploy a BLOCKED change.

---

## Loop 3 — Commit Before Deploy

**Purpose:** Production must never run uncommitted code.

**Rule:** `flyctl deploy` and frontend deploys ship the **working tree**, not HEAD. Deploying uncommitted code leaves production ahead of git; a clean checkout silently regresses.

Required sequence:

1. Commit all changes.
2. Push to remote.
3. Deploy (`flyctl deploy`).
4. Flush pipeline cache (`POST /api/pipeline/run` with `X-Cron-Secret` header).
5. Verify production reflects the deployed state.

⛔ **GATE:** Do not run `flyctl deploy` while uncommitted changes exist in the working tree.

**Worked example:** Commit `371e071` (2026-06-18) — matchup fix and board blank fix committed and pushed before `flyctl deploy` ran.

**Fly.io specifics:** → See [CLAUDE.md §8 Deployment Summary](CLAUDE.md).

---

## Loop 4 — Production Error Sweep

**Purpose:** Eliminate silent failures, especially on data paths.

1. Grep for bare `except: pass` and `except Exception: print(...)` across all production paths.
2. Classify each finding:
   - **HIGH** — wraps a write, log, or persist operation
   - **MED** — wraps a fetch or parse operation
   - **LOW** — demonstrably benign
3. Fix all HIGH findings: replace with `logger.error(...)` + traceback + operator-visible surface (dashboard warning or API error response).
4. Report MED and LOW findings to operator for decision.

⛔ **GATE:** Every persistence path must fail loudly. Silent swallow on a write path is never acceptable.

**Why this matters:** This pattern caused silent data loss three times — cloud-capture loop, `app.py` (×4 instances), `api/cron.py:62`. Each was invisible to the operator until a downstream calibration or tracking audit exposed it.

---

## Loop 5 — Data Integrity / Capture

**Purpose:** Verify writes land AND that captured data is the intended data.

1. Confirm write operations complete — check return values, row counts, or Supabase response bodies.
2. Distinguish **engine-qualified picks** (model output, pre-operator review) from **operator-deployed picks** (what was actually bet).
3. Calibration and CLV runs operate on the **deployed-state sample only**, never on the engine-qualified pool.

⛔ **GATE:** Before running any calibration or accuracy audit, verify the tracker holds deployed picks, not engine-qualified picks.

**Why this matters:** The 2026-06-18 calibration audit was invalidated — the tracker held qualified picks, not deployed picks, and writes were silently failing. The audit result was meaningless against real performance.

---

## Loop 6 — Documentation Sweep

**Purpose:** Keep repo doctrine matching reality.

1. Read current doctrine — [CLAUDE.md](CLAUDE.md), [AGENTS.md](AGENTS.md), and relevant wiki pages.
2. Compare doctrine claims against current codebase state.
3. Flag contradictions (e.g., a handoff doc asserting shipped work as still-open, or doctrine referencing a surface that moved).
4. Update the affected doc or flag for operator decision.

⛔ **GATE:** Do not propagate a stale doctrine claim into new files or agent packets.

**Vault update triggers:** → See [MLB HR ENGINE/wiki/doctrine/OBSIDIAN_GOVERNANCE_DOCTRINE.md](MLB%20HR%20ENGINE/wiki/doctrine/OBSIDIAN_GOVERNANCE_DOCTRINE.md). Do not restate its trigger list here.

---

## Loop 7 — Repository Hygiene

**Purpose:** Working tree, HEAD, and production stay in sync.

1. Verify no uncommitted-but-deployed code exists — run Loop 3 sequence before any deploy.
2. Verify no orphaned, dead, or contaminated paths are present in the working tree.
3. Confirm all surface assignments match the invariants below.

**Path invariants (hard):**

| Surface | Canonical path |
|---------|---------------|
| Production frontend | `ROOT/frontend/` (repo root) |
| Engine code | `mlb_hr_engine_v4/` |
| Repo root | `C:\MLB HR Engine\mlb-hr-engine-master` |

**NEVER** reference `C:\flag game` or `C:\ronans-flag-game` in this repo — those are unrelated projects. Any such reference in files, paths, or agent packets is contamination and must be removed.

---

## Loop 8 — PM → Claude Code Handoff

**Purpose:** Define the two-Claude operating model and the packet interface between them.

**Roles:**
- **Claude PM (chat):** Plans, architects, audits, routes, and writes copy-ready execution packets. Does not execute code.
- **Claude Code:** Executes, tests, commits, and deploys. Does not plan scope. Executes what the packet specifies and reports back.

**The packet is the interface.** Every execution packet carries:

| Field | Content |
|-------|---------|
| Room routing | Which room owns this work |
| Owner | Which agent executes |
| Model | Which model (Sonnet / Opus / etc.) |
| Risk | LOW / MEDIUM / HIGH |
| Surface | Files and surfaces in scope |
| Protected surfaces | Surfaces that must not be modified |
| Git safety | DO NOT COMMIT / DO NOT PUSH unless explicitly authorized in the packet |
| Obsidian update | Whether a vault update is required on completion |
| Completion report | Format for reporting back to PM |

⛔ **GATE:** Claude Code must not expand scope beyond the packet. Scope questions go back to PM before execution begins.

**Operating rules 1–16:** → See [AGENTS.md](AGENTS.md). Do not restate here.

---

*Cross-references: [AGENTS.md](AGENTS.md) · [CLAUDE.md](CLAUDE.md) · [MLB HR ENGINE/wiki/doctrine/OBSIDIAN_GOVERNANCE_DOCTRINE.md](MLB%20HR%20ENGINE/wiki/doctrine/OBSIDIAN_GOVERNANCE_DOCTRINE.md)*
