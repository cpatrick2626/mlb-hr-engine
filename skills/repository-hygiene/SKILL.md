---
name: repository-hygiene
description: "Use to verify git working-tree/HEAD/production sync, check for uncommitted-but-deployed code, find orphaned or dead paths, detect flag-game contamination, and run pre-deploy repo verification."
---

# /repository-hygiene

PURPOSE: Working tree, HEAD, and production stay in sync; no orphaned or contaminated paths.

## PROCEDURE

Implements **Loop 7 — Repository Hygiene** (path invariants, surface assignments, contamination checks) and **Loop 3 — Commit Before Deploy** (commit/push/deploy sequence) — see LOOPS.md §7 and §3 for the authoritative steps, gates, and rules. Do not duplicate the procedure here.

## Trigger notes

- §7 contamination rule applies: flag-game path references in this repo must be removed — see LOOPS.md §7.
- §3 deploy gate applies — see LOOPS.md §3.
