# 2026-06-19 — Skills as LOOPS.md Pointers

## Session summary

Converted 6 existing MLB HR Engine skills into formal SKILL.md pointer files and created 3 new pointer skills. All skills point into LOOPS.md as the one-source-of-truth for procedure; no loop steps are duplicated into skill files.

## Converted skills (existing → pointer)

| Skill | File | Points to |
|-------|------|-----------|
| Root Cause Investigator | `skills/root-cause-investigator/SKILL.md` | LOOPS §1 |
| Production Auditor | `skills/production-auditor/SKILL.md` | LOOPS §2 + §3 |
| MLB HR Engine Architect | `skills/mlb-hr-engine-architect/SKILL.md` | LOOPS §7 + §8 |
| UX Command Center | `skills/ux-command-center/SKILL.md` | Domain lens + §8 |
| Stats Engineer | `skills/stats-engineer/SKILL.md` | Domain lens + §5 (ref only) |
| AI Systems Architect (Hermes) | `skills/ai-systems-architect/SKILL.md` | §5 + §8; not load-bearing yet |

## New skills created

| Skill | File | Points to |
|-------|------|-----------|
| Data Integrity Auditor | `skills/data-integrity-auditor/SKILL.md` | LOOPS §4 + §5 |
| Repository Hygiene | `skills/repository-hygiene/SKILL.md` | LOOPS §7 + §3 |
| Doctrine Sweep | `skills/doctrine-sweep/SKILL.md` | LOOPS §6 |

## Key decisions

**One-source rule enforced:** No loop procedure steps duplicated into any skill file. Skills carry domain lens content (UX Command Center, Stats Engineer) only where that judgment is not a loop — and even then, calibration constraint points to §5 rather than restating it.

**Flag-game exclusion:** Banana Design Authority and Ronan Game Experience Reviewer were explicitly excluded. Those skills belong to the Ronan Flag Game project. Creating them here would contaminate the MLB context — a §7 violation. Repository Hygiene skill (§7) now enforces this at the skill level.

**"Safe Production Engineer" consolidated:** Not a separate skill. Lives in LOOPS §1 step 8 per LOOPS.md. Root Cause Investigator references it there.

**Hermes marked not load-bearing:** AI Systems Architect skill carries clear NOT YET BUILT status. Phase 2 capture layer is not built; skill governs design when work begins.

## AGENTS.md changes

Added 3 new skill rows to the Global Utility Skill Library registry table. Existing rows untouched.

## Files created/modified

- `skills/root-cause-investigator/SKILL.md` (created)
- `skills/production-auditor/SKILL.md` (created)
- `skills/mlb-hr-engine-architect/SKILL.md` (created)
- `skills/ux-command-center/SKILL.md` (created)
- `skills/stats-engineer/SKILL.md` (created)
- `skills/ai-systems-architect/SKILL.md` (created)
- `skills/data-integrity-auditor/SKILL.md` (created)
- `skills/repository-hygiene/SKILL.md` (created)
- `skills/doctrine-sweep/SKILL.md` (created)
- `AGENTS.md` (3 rows added to registry table)

## Cross-references

- [[LOOPS]] — authoritative loop procedures; all skills point here
- [[AGENTS]] — skill registry; 3 new rows added
- [[OBSIDIAN_GOVERNANCE_DOCTRINE]] — vault update triggers (§6 references this)

## Git status

DO NOT COMMIT. DO NOT PUSH until operator reviews.
