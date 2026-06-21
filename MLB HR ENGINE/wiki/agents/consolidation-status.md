---
created: 2026-06-20
phase: 1-complete
next-phase: 2
---

# Agent/Skill Consolidation Status

Ground-truth audit completed 2026-06-20. This file tracks consolidation progress across phases. Do not reconcile or delete anything until operator approves each phase.

---

## Phase 1 — Completed 2026-06-20

**Fix: `to-issues` GitHub conflict resolved.**

Both copies (`.agents/skills/to-issues/SKILL.md` and `.claude/skills/to-issues/SKILL.md`) updated to write issues as local markdown files under `.scratch/<feature-slug>/issues/` per `MLB HR ENGINE/wiki/agents/issue-tracker.md`. `gh issue create` is explicitly prohibited in both copies. The `/setup-matt-pocock-skills` pointer (which configured GitHub as the tracker) replaced with local protocol pointer.

---

## Phase 2 — Pending operator decision

### Overlap pairs (flag only — do not resolve yet)

| Matt Pocock skill | Project-native equivalent | Overlap |
|---|---|---|
| `diagnosing-bugs` | `root-cause-investigator` (LOOPS.md §1) | HIGH — same job; root-cause-investigator gates on Loop 1 + requires evidence; Matt Pocock version is generic with HITL shell script, no Loop 1 gate |
| `git-guardrails-claude-code` | `git-hygiene` (.agents/skills/) + LOOPS.md §3 | HIGH — three things enforce git safety; Loop 3 is doctrine authority |
| `handoff` | Loop 8 (via `mlb-hr-engine-architect`) | MEDIUM — Loop 8 is MLB-specific handoff packet structure; Matt Pocock `handoff` is generic context pass |
| `improve-codebase-architecture` | `mlb-hr-engine-architect` + `improve-system` (skills/) | MEDIUM — Matt Pocock version is generic; project versions are MLB-specific with doctrine gates |
| `grill-with-docs` | `doctrine-sweep` (skills/) | MEDIUM — both validate implementation vs docs; `doctrine-sweep` is wiki-rooted and MLB-specific |

**Decision needed for Phase 2:** Convert Matt Pocock overlaps to pointer-skills (pointing to project-native equivalents + LOOPS.md), or remove. No action until operator authorizes.

### Loader directory structure (flag only)

Three independent loader contexts exist:

| Directory | Loader | Origin |
|---|---|---|
| `skills/` | Claude Code | Project-native, MLB-specific, LOOPS.md pointer pattern |
| `.claude/skills/` | Claude Code | Matt Pocock generic skills (10 skills, committed edf0d10) |
| `.agents/skills/` | Codex runtime | Hybrid: 8 project-native Codex skills (a5810aa) + 10 Matt Pocock duplicates (edf0d10) |

Matt Pocock skills are registered in `skills-lock.json` and duplicated into both `.agents/skills/` and `.claude/skills/`. The dual-registration was not intentional by design — artifact of setup script. Decision needed: keep dual-registration, collapse to one dir, or remove duplicates from `.agents/skills/`.

---

## Phase 3 — Pending

**Gap: PROJECT_MISSION.md does not exist.**

No project-objectives / north-star document exists at repo root or in `MLB HR ENGINE/wiki/`. CLAUDE.md §1 has a two-paragraph descriptive overview but no structured mission with success criteria or strategic priorities. Build `PROJECT_MISSION.md` in Phase 3.

---

## Phase 4 — Read-only review first

**Hook: graphify-first enforcer exists — review before any hook design.**

`.claude/settings.json` has one `PreToolUse` hook block:
- Matcher `Bash`: fires when command contains grep/rg/find/fd/ack/ag AND `graphify-out/graph.json` exists → injects graphify-first advisory
- Matcher `Read|Glob`: fires when reading source files AND graph exists → same advisory

Do NOT edit or remove this hook before a read-only review of its behavior in Phase 4. No new hook automation until that review completes.
