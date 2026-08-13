---
date: 2026-08-12
agent: Claude Code
task: FSM dashboard reorganization — component hiding, control consolidation, community slip-card work
commits: 4e9743b, 4873b72, 2053751, 7ce8f22, 52bc239, 4cf8e65, b38e256, aa1d5a3, 0fe4dcb, d366e5d (board), f87ab69, 58ee5b1 (slip card)
---

## Summary

Two parallel workstreams shipped Aug 12: FSM dashboard reorganization and Community slip-card enrichment. No scoring, calibration, or pipeline logic was touched.

---

## FSM dashboard reorganization

### PLAYER GROUP and FOCUS controls removed (commit `4e9743b`)

`PLAYER GROUP` and `FOCUS` radio controls are no longer rendered on the slate board. Underlying predicate functions remain in `full-slate-matrix.js` with state pinned to `"all"` / `"ALL"` — no rows are hidden by them. Preserved for possible future re-exposure (e.g. strategy-mode toggle). See [[full-slate-matrix]] for updated doctrine.

### Control consolidation (commit `4873b72`)

Controls regrouped into three labeled sections in `fsm-sortbar`:

| Section | Contents |
|---|---|
| **SORT & FILTER** | RANK, column sort toggles, TM ≥60, HR PROB ≥15% |
| **SCOPE** | ROLE multi-select badges |
| **GAMES** | GAME VIEW / PLAYER VIEW; LIVE readout (relocated here) |

COLUMNS and EDIT controls moved up to the top bar.

### Threat Zone / Pitcher Vulnerability / Escalation Feed hidden (commit `2053751`)

Three component strips — HR Threat Zone, Pitcher Vulnerability Strip, Escalation Feed — are hidden from the MAIN slate. Components (`hr-threat-zone.js`, `pitcher-vulnerability-strip.js`, `escalation-feed.js`) are **preserved** in `frontend/assets/js/` for relocation to a future Strategy surface. No component code was deleted.

### LIVE readout + Columns/Edit relocated (commit `7ce8f22`)

LIVE indicator moved from top bar into the GAMES section. COLUMNS and EDIT moved from sortbar to top bar. Contrast and affordance sweep applied to matrix controls.

### Dead column collapse (commit `52bc239`)

Collapsed a dead empty column between the Signal and Share columns in the matrix grid.

### Search bar (commit `4cf8e65`)

Player/pitcher search bar added to the top bar. Uses `data-fullname` attribute hooks on rows for locate/highlight behavior.

---

## Community slip-card work (same day)

### Per-leg detail in slip card body (commit `f87ab69`)

`CommSlipCard` body now renders per-leg detail rows: player name, tier, pitcher, arsenal edge, and other available fields per audit. Fields not in the payload show `"—"`.

### Verdict line (earlier, commit `e6e9a84`)

Plain-language verdict line added to community slip cards.

### Contrast and tier-coded stats (commit `58ee5b1`)

Slip card stats (rank, scores) are tier-color-coded. Inverted/neutral display where appropriate; rank labeled to avoid misleading directionality.

### Pick card scores + stacked totals (commits `aa1d5a3`, `0fe4dcb`)

Pick card shows TM/JIG, HR%, Signal, Edge, Confidence per picked batter (tier-color-coded). Stacked pick rows with honest combined-ticket totals: product HR%, gated EV.

---

## Protected surfaces

- No model probability, EV, tier ranking, or `pipeline.py` logic touched.
- No schema change.
- MAIN/JIG separation upheld throughout.
- Hidden components retained on disk; no deletion.
