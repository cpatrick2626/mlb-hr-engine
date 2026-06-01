# Session: Ranker Doctrine Audit — HIGH Risk Read-Only
Date: 2026-05-26
Agent: Codex (read-only audit)
Risk Class: HIGH (audit only — execution not yet authorized)

## Audit Finding Summary

### Current Live Formula
score = (ev_pct × 0.40 + edge_pct × 0.60) × (0.50 + 0.50 × confidence/100)

Note: weights are NOT the hardcoded 0.55/0.45 defaults.
Auto-learn system (adaptive_weights.py + learned_adjustments.json)
has adjusted ranker_ev_weight to 0.40 at runtime.

### Tier Assignment — Independent of Score
S: confidence >=70 AND edge >=8.0
A: confidence >=55 AND edge >=5.0
B: confidence >=35 AND edge >=2.5
C: otherwise

### All Surfaces Fed by Ranker
- MAIN Deployment Edge — highest impact (hero pick + rank order)
- MAIN Power Profile — low impact (custom sort)
- MAIN Matchup Edge — low impact (HVY sort)
- MAIN Portfolio — medium impact (displayed score changes)
- MAIN Full Slate Qualified — medium impact (inconsistent doctrine risk)
- FanDuel Slip fallback — medium impact (sorts by score)
- Player modal — low impact (display only)
- JIG/HITS — visual badge only
- Parlays — stable (own ranking logic)
- tracking/auto_learn.py — CRITICAL RISK (learns ev_weight from score behavior)

### Impact on 2026-05-26 Logged Slate (29 picks)
Biggest risers under model_prob formula:
  Miguel Vargas 26→12, Ty France 7→2, Shea Langeliers 6→3
Biggest fallers:
  James Wood 2→5, Curtis Mead 3→6, CJ Abrams 5→7

### Critical Hidden Risk
auto_learn.py learns ranker_ev_weight from EV/edge score behavior.
If ranker stops using EV/edge weighting, learning loop becomes
stale/dead logic and continues adjusting a weight that no longer
exists. This is a silent corruption risk.

### Recommended New Formula
rank_score = calibrated_model_prob × reliability_modifier
modifier range: 0.80–1.00
  lineup confirmed:    1.00
  projected/likely:    0.92
  unknown/unconfirmed: 0.85
  data completeness:   1.00–0.85 based on Statcast quality
  book coverage:       1.00–0.95 based on book count

### Execution Scope — Coordinated Package Required
Cannot be single-step. Must touch in order:
  1. output/ranker.py — formula change
  2. tracking/auto_learn.py — retire ev_weight learning
  3. tracking/adaptive_weights.py — retire or redesign
  4. tracking/learned_adjustments.json — reset/archive
  5. pipeline.py — score stamping update
  6. app.py Full Slate Qualified — companion sort fix

### Status
QUEUED — awaiting operator doctrine decision on auto-learn system.
Operator must answer: keep, retire, or redesign auto-learn?
before execution can be authorized.
