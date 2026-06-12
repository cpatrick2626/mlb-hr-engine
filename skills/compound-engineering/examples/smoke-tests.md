# Compound Engineering Smoke Tests

## Test 1 — Brainstorm

Prompt:

```text
Use /ce-brainstorm.

I want to improve the TCC dashboard so it is easier to decide what to do next.
```

Expected behavior:

- explores options
- does not jump to code
- recommends one direction

---

## Test 2 — Plan

Prompt:

```text
Use /ce-plan.

Plan a safe LOW-risk docs update for a new utility skill.
```

Expected behavior:

- defines scope
- defines done
- includes validation
- marks risk

---

## Test 3 — Work

Prompt:

```text
Use /ce-work.

Authorized: create a docs-only skill file and Obsidian reference note.
No runtime changes.
```

Expected behavior:

- keeps scope tight
- lists allowed files
- includes validation
- no commit/push unless authorized

---

## Test 4 — Code Review

Prompt:

```text
Use /ce-code-review.

Review this claimed result:
Files changed: skills/example/SKILL.md and wiki/log.md.
Validation: git diff --check clean.
```

Expected behavior:

- checks scope
- checks done criteria
- accepts/revises/rejects

---

## Test 5 — Debug

Prompt:

```text
Use /ce-debug.

The app shows 0 players after data loads.
```

Expected behavior:

- treats as runtime instability
- isolates hydration/data path
- does not suggest random UI polish
