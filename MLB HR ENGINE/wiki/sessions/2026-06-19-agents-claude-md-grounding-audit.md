# 2026-06-19 — AGENTS.md Grounding Update: CLAUDE.md vs AGENTS.md Audit

## Task
Read-only verification of CLAUDE.md against AGENTS.md to finalize operating-system entrypoint hierarchy. No writes, no commits, no push to repo.

## Files Examined
- `CLAUDE.md` (repo root, 356 lines, 16 sections)
- `AGENTS.md` (repo root, 526 lines)

## Section Classification

| § | Title | Class | Key Finding |
|---|-------|-------|-------------|
| 1 | Project Overview | CLAUDE-SPECIFIC | Pipeline description, versioning. Absent from AGENTS.md. |
| 2 | Current Production Version | CLAUDE-SPECIFIC | "v4 active, don't touch v1-v3." Absent from AGENTS.md. |
| 3 | Quick Setup | CLAUDE-SPECIFIC | pip install commands. Absent from AGENTS.md. |
| 4 | Common Commands | CLAUDE-SPECIFIC | All run/backtest/analysis/ops commands + Windows vs cross-platform note. Absent. |
| 5 | Version / Directory Map | CLAUDE-SPECIFIC | Feature matrix per version. Absent. |
| 6 | Architectural Invariants | MIXED | Poisson formula, surface independence, versioned-dir isolation = CLAUDE-SPECIFIC. config.py + pipeline.py source-of-truth bullets = DUPLICATE of AGENTS.md §101-102. |
| 7 | MAIN vs JIG Doctrine | DUPLICATE + POINTER | States "Authoritative source: AGENTS.md." Condensed restatement of AGENTS.md content. Safe to slim to one-line pointer. |
| 8 | Deployment Summary | CLAUDE-SPECIFIC | Fly.io config, volume mount, Dockerfile, secrets list. Zero counterpart in AGENTS.md. |
| 9 | Module Map | CLAUDE-SPECIFIC | Full mlb_hr_engine_v4/ directory listing. Absent. |
| 10 | Frontend Surface | CLAUDE-SPECIFIC | Next.js isolation rules, archived component audit trail, surface separation confirmations. Absent. |
| 11 | Environment Variables | CLAUDE-SPECIFIC | load_dotenv() cwd-sensitivity behavior — critical for script invocation correctness. Entirely absent from AGENTS.md. |
| 12 | Reference Docs | POINTER | Index of doctrine docs. No conflict. |
| 13 | Validation / Safety Rules | MIXED | "Never fabricate Statcast" = DUPLICATE (AGENTS.md Pitch Mix Rules). Analysis-script re-run rule + n<200 calibration rule = CLAUDE-SPECIFIC. |
| 14 | What Not To Do | MIXED | Don't merge MAIN/JIG + don't duplicate constants = DUPLICATE. Don't assume py -3.12 + don't rewrite runtime for docs + don't invent deployment behavior + don't commit .env = CLAUDE-SPECIFIC. |
| 15 | WIKI SYSTEM | CLAUDE-SPECIFIC | Vault path, directory map, log format, agent routing by tool type, protected zones, session protocol. AGENTS.md has room routing only — not vault/wiki protocol. |
| 16 | graphify | CLAUDE-SPECIFIC | Knowledge graph usage rules. Entirely absent from AGENTS.md. |

## Conflicts Found

**None.** Two soft notes:
1. AGENTS.md Rule 17 (Tool Action Permission Policy) has no counterpart in CLAUDE.md. Not a conflict — targets Claude App rooms; Claude Code uses harness permission model.
2. AGENTS.md routes by room name. CLAUDE.md §15 routes by tool type (Claude Code / ChatGPT / Playwright). Complementary, not contradictory.

## Verdict

**PRESERVE-CONTENT**

CLAUDE.md holds unique operational doctrine AGENTS.md entirely lacks:
- Repo setup + all run commands
- Version capability matrix
- Poisson pipeline sequence description
- Fly.io deployment specifics (Docker, secrets, volume)
- Full module map
- Frontend isolation rules + audit trail
- load_dotenv() cwd-sensitivity (critical — wrong cwd silently breaks env)
- Wiki/vault session protocol
- graphify rules
- n<200 calibration change rule
- Windows vs cross-platform invocation notes

Duplicate content (MAIN/JIG summary, config.py/pipeline.py rules, no-fabrication) is small relative to unique content and serves as quick-reference for Claude Code.

## Safe Slim Candidates (do not execute without operator authorization)

| Target | Action | Risk |
|--------|--------|------|
| §7 MAIN vs JIG | Reduce to one-line pointer to AGENTS.md | LOW |
| §6 config.py + pipeline.py bullets | Remove (duplicates AGENTS.md §101-102) | LOW |
| §13 "Never fabricate Statcast" bullet | Remove (duplicates AGENTS.md Pitch Mix Rules) | LOW |
| §14 "Don't merge MAIN/JIG" + "don't duplicate constants" bullets | Remove (duplicates AGENTS.md) | LOW |

All other sections must stay until migrated into AGENTS.md or vault doctrine.

## Agent
Claude Code (Sonnet 4.6)

## Git Status
No writes to repo. Read-only audit only.
