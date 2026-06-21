---
created: 2026-06-20
phase: 3-complete
next-phase: 4
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

## Phase 3 — Complete 2026-06-20

**Done: PROJECT_MISSION.md created at repo root.**

`PROJECT_MISSION.md` exists as authoritative north-star doc. Covers mission, priority hierarchy, what engine is/is not, success criteria, known reality (net negative history, ~18% HR hit rate, edge UNRESOLVED, calibration deferred N=4), non-negotiable invariants (linked not restated), cross-references to AGENTS.md/LOOPS.md/CLAUDE.md/feedback-loop-architecture.md/ticket-data-capture-phase1-architecture.md. CLAUDE.md §6/§9 anchor links verified correct. File encoding confirmed clean UTF-8 (no mojibake). Staged; awaiting operator commit authorization.

---

## Phase 2.5 — Complete 2026-06-21

**Done: git-safety enforcement hook activated.**

`block-dangerous-git.sh` deployed to `.claude/hooks/block-dangerous-git.sh` and wired into `.claude/settings.json` as a second `PreToolUse[Bash]` hook entry (alongside the graphify hook — graphify hook not disturbed).

DANGEROUS_PATTERNS enforced (exit 2):
- `push --force` / `push -f` — overwrites remote history
- `reset --hard` — discards uncommitted work
- `clean -f` / `clean -fd` — deletes untracked files/dirs
- `branch -D <name>` — force-deletes a branch
- `checkout .` (literal dot only, not `checkout ./path`) — discards all unstaged changes
- `restore .` (literal dot only) — same via restore syntax

NOT blocked (normal workflow):
- `git push origin main` — authorized pushes pass freely
- `git commit`, `git add`, `git checkout <branch>`, `git checkout ./path`

Convention: no override mechanism. Genuinely intended dangerous commands must be run from a terminal outside Claude Code.

Verify results (all 7 passed):
- `git push origin main` → exit 0 ✓
- `git push --force origin main` → exit 2 ✓
- `git push -f origin main` → exit 2 ✓
- `git reset --hard` → exit 2 ✓
- `git commit -m test` → exit 0 ✓
- `git checkout ./somepath` → exit 0 ✓
- `git add mlb_hr_engine_v4/config.py` → exit 0 ✓

git-hygiene skill (`.agents/skills/git-hygiene/`) now has ACTUAL enforcement (the block script) backing the advisory doctrine. Previously advisory-only.

---

## Phase 4 — Read-only review first

**Hook: graphify-first enforcer exists — review before any hook design.**

`.claude/settings.json` has one `PreToolUse` hook block:
- Matcher `Bash`: fires when command contains grep/rg/find/fd/ack/ag AND `graphify-out/graph.json` exists → injects graphify-first advisory; also now runs `block-dangerous-git.sh` on every Bash call
- Matcher `Read|Glob`: fires when reading source files AND graph exists → same advisory

Do NOT edit or remove existing hooks before a read-only review of behavior in Phase 4. No new hook automation until that review completes.
