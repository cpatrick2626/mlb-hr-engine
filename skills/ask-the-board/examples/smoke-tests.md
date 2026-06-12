# /ask-the-board Smoke Tests

## Test 1 — Betting Decision

Prompt:

```text
Use /ask-the-board.

Decision:
Should I bet this HR prop if MLB HR ENGINE shows strong signal but the sportsbook price has already moved?

Context:
The model likes the player, but the line is worse than earlier.

Priority:
betting edge
```

Expected behavior:

* Selects Walters + Benter.
* Emphasizes price sensitivity and model-vs-market edge.
* Does not guarantee outcome.
* Gives one next action.

---

## Test 2 — Product Decision

Prompt:

```text
Use /ask-the-board.

Decision:
Should we add another dashboard panel to the TCC home screen?

Context:
It may add useful information but could increase clutter.

Priority:
UX clarity and product quality
```

Expected behavior:

* Selects Cagan + Carmack + NNGroup.
* Evaluates user value, complexity, and cognitive load.
* Recommends build/cut/test decision.

---

## Test 3 — MLB HR ENGINE Decision

Prompt:

```text
Use /ask-the-board.

Decision:
Should TCC compute its own deployment score?

Context:
TCC currently orchestrates and displays model/tactical signals.

Priority:
system safety and product clarity
```

Expected behavior:

* Selects full MLB HR ENGINE panel.
* Preserves TCC orchestration-only doctrine.
* Rejects hidden scoring.
* Gives one safe next action.

---

## Test 4 — Devil's Advocate

Prompt:

```text
Use /ask-the-board.

Decision:
What could go wrong if we add a new JIG volatility rank?

Context:
It might help targeting but could confuse MAIN/JIG separation.

Priority:
risk
```

Expected behavior:

* Selects Devil's Advocate panel.
* Flags model/data/UX/architecture risk.
* Preserves MAIN/JIG separation.
