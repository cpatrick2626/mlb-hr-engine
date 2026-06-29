# True Matchup Score (TM)

## Summary

True Matchup (TM) is a **display/alignment composite score, 0–100**, surfaced on the Main Slate matchup cell as a labeled gauge. It expresses overall HR-matchup alignment by blending the model's HR probability with the arsenal-edge exploit read, its support confidence, and pitcher vulnerability.

TM is **NOT** HR probability, and it is **NOT** a model input. It is computed at the API serialization layer from values already present on each row, is inert (never fed back into any scoring/ranking), and exists only to give the operator a single fast "how aligned is this matchup" read distinct from raw HR probability.

TM is intentionally **distinct from HR Prob**: HR Prob keeps its own column as the actual predictive percentage; TM represents the fuller matchup picture (probability + exploit + signal + vulnerability).

## Key Points

### What TM is
- A 0–100 composite, emitted per row as `true_matchup_score`.
- Computed **only** in `mlb_hr_engine_v4/api/main.py` at row serialization, after MAIN and JIG ordering are complete.
- Built from fields already on the row — no new data sourcing, no pipeline/engine computation.
- A display value: it drives the matchup gauge and two filter toggles. Nothing more.

### What TM is NOT (invariants — never break without operator authorization)
1. **Not HR probability.** Do not label TM as HR prob, HR%, or a chance-to-homer. HR Prob (`hrprob`, ×100) is a separate displayed value.
2. **Not a model input.** TM must never feed `model_prob`, MAIN ordering (`model_tier_rank`), JIG scoring/order (`jigScore`), HVY, ticket probability, or tier assignment. It is read-only output.
3. **Not computed in the engine/pipeline.** TM lives at the API serialization boundary only. Moving its computation into `pipeline.py`, `engine/`, or any scoring path is contamination and requires a doctrine update.
4. **Not visually rescaled.** The gauge shows the raw TM value on an honest 0–100 arc (`arc = TM/100`). Do not stretch/rescale TM to make the gauge reach the 80s/90s. Band strength is communicated by color, not by inflating the number.
5. **Single source of truth.** The frontend reads `row.true_matchup_score` directly. No client-side recomputation/fallback of the TM formula (a prior fallback was removed precisely to avoid dual-source drift).

### Formula (operator-approved 2026-06-28)

```
true_matchup_score = round(100 × (0.40·hrProbN + 0.30·edgeN + 0.20·conf + 0.10·vulnN)), clamped 0–100
```

Component normalization (each to 0–1):
- `hrProbN = clamp(model_prob / 0.25, 0, 1)`            — model_prob is decimal 0–1; ~0.25 ≈ realistic HR-prob ceiling
- `edgeN   = clamp(arsenal_edge_score / 10.0, 0, 1)`     — arsenal_edge_score is 0–10, neutral ≈ 3.0, never negative
- `conf    = clamp(arsenal_edge_confidence, 0, 1)`       — already 0–1
- `vulnN`  = average of available pitcher-vulnerability components:
  - `clamp(pitcher_hr9 / 2.0, 0, 1)` and `clamp(pitcher_barrel_allowed / 0.12, 0, 1)`
  - if one null, use the other; if both null, `vulnN = 0.5` (neutral)

Null handling:
- `model_prob` null → TM = null (HR prob is core; gauge shows "—").
- `arsenal_edge_score` / `arsenal_edge_confidence` null → that component = 0 (no edge demonstrated), TM still computed.

Weighting rationale: HR Prob is capped at 40% deliberately so TM does not collapse into a second HR-prob number. Edge (30%) + Signal (20%) + Vulnerability (10%) make TM a fuller alignment read that surfaces different players than raw HR prob (e.g. a high-edge / high-confidence batter with moderate HR prob can outrank a high-HR-prob batter with a weak arsenal edge).

### Bands (operator-approved, fixed thresholds — display only)

| Band   | TM range | Notes |
|--------|----------|-------|
| ELITE  | ≥ 60     | top treatment |
| STRONG | 50–59    | |
| AVG    | 38–49    | |
| WEAK   | 25–37    | |
| COLD   | < 25     | |

Bands are display-only and were tuned to the real distribution (see below). They are trivially retunable without any formula change. Null TM → neutral treatment, "—".

### Observed distribution (reference, not a guarantee)
- On the 374-row tuning slate (2026-06-28): min 13, max 72, mean 34.5, median 34. ~2% ≥ 60.
- Live slates have run higher (a same-day live slate showed max 81, ~36 rows ≥ 60). **Watch live distributions; if `ELITE 60+` catches too wide a top tier, retune the bands (display-only).**

### Filter toggles (Main Slate)
TM and HR PROB are role-style filter toggles on the Full Slate (independent on/off; AND-intersection when both on). Fixed thresholds (operator-approved 2026-06-28):
- TM toggle ON → rows with `true_matchup_score ≥ 60`
- HR PROB toggle ON → rows with `hrprob ≥ 15` (×100, i.e. 15%)
- Both ON → intersection (the dual-threat shortlist)
- RANK button is a separate sort/default control, not a filter.

These cutoffs are display/filter-only and retunable. On a weak slate the intersection may be small or empty — this is honest (no dual-threats), handled by an empty state, not a bug.

## Data discipline reminders
- `model_prob` = decimal 0–1. `hrprob` = ×100. `jigScore` = 0–100. `true_matchup_score` = 0–100. Do not confuse them.
- TM reads these; it never writes any of them.

## Enforcement
Any proposed change that would move TM computation into the engine/pipeline, feed TM into MAIN/JIG/HVY/tickets/ranking, or rescale the gauge is **HIGH risk** and requires:
1. Read-only audit first
2. Operator review
3. A doctrine update to this file

Retuning bands or filter cutoffs (display-only) is LOW risk and does not require an audit, only a note here when changed.

## Cross-References
- [MAIN/JIG Separation Rules](main-jig-separation.md)
- [MAIN Model Doctrine](main-model-doctrine.md)
- [Production Surface Truth](production-surface-truth.md)
- [Tier Vocabulary](tier-vocabulary.md)
- Source: `mlb_hr_engine_v4/api/main.py` (`_true_matchup_score` helper, post-AEE serialization loop)
