# /internal-focus-group Smoke Tests

## Test 1 — Full Panel Launch Review

Prompt:

```text
Use /internal-focus-group.

Test this before launch:
We are adding a new TCC panel that summarizes the top HR deployment candidate, the strongest JIG exploit, and current FanDuel link status.

Context:
The screen is already dense.

Priority:
operator clarity
```

Expected behavior:

* Selects available panel agents.
* Marks missing source folders as DATA GAP.
* Flags cognitive load and launch risk.
* Gives one next action.

---

## Test 2 — Ask One Person

Prompt:

```text
Use /internal-focus-group.

Ask JIG user what they think about:
Renaming JIG Top Targets to Exploit Targets.
```

Expected behavior:

* Checks for `knowledge/focus-group/jig-user/`.
* If missing, marks DATA GAP.
* Returns only that agent's lens and recommendation.

---

## Test 3 — Copy Review

Prompt:

```text
Use /internal-focus-group.

Test this copy before launch:
"APEX HR DEPLOYMENT LOCKED."

Priority:
trust and clarity
```

Expected behavior:

* Flags overconfidence/gambling-risk language.
* Recommends safer wording.
* Does not guarantee outcomes.

---

## Test 4 — Missing Agent

Prompt:

```text
Use /internal-focus-group.

Ask Sarah what she thinks about the mobile layout.
```

Expected behavior:

* If Sarah has no folder, return DATA GAP.
* Explain how to add Sarah using `/ingest-source`.
