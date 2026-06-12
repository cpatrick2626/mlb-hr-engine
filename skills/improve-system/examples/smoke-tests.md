# /improve-system Smoke Tests

## Test 1 — Audit Mode

Prompt:

```text
Use /improve-system.

Find stale, conflicting, or duplicate notes across the recent doctrine files.
Read-only only. Do not edit files.
```

Expected behavior:

* Selects Audit mode.
* Reports stale/conflicting/duplicate candidates.
* Does not rewrite notes.

---

## Test 2 — Skill Review Mode

Prompt:

```text
Use /improve-system.

Review the /ingest-source skill based on our recent back-and-forth.
Find anything that should be clearer or more efficient.
Do not edit the skill yet.
```

Expected behavior:

* Selects Skill Review mode.
* Produces targeted improvement recommendations.
* Separates confirmed friction from proposed changes.

---

## Test 3 — Experience Mode

Prompt:

```text
Use /improve-system.

Experience: We learned that adding all skills first and committing once is cleaner than making six tiny commits.
Capture this as an operating lesson.
```

Expected behavior:

* Selects Experience mode.
* Captures the story/win/lesson.
* Suggests route and note title.

---

## Test 4 — Historical Review Mode

Prompt:

```text
Use /improve-system.

Review the last few Claude Code session outputs and find missed learnings that should become doctrine or skill improvements.
Read-only only.
```

Expected behavior:

* Selects Historical Review mode.
* Identifies repeated patterns and missed captures.
* Recommends one next action.

---

## Test 5 — Foundation Mode

Prompt:

```text
Use /improve-system.

Foundation: Identify missing foundational content for brand, audience, offers, and voice.
Do not draft everything yet. Just show the gaps and proposed note structure.
```

Expected behavior:

* Selects Foundation mode.
* Lists missing foundation areas.
* Proposes note structure.
