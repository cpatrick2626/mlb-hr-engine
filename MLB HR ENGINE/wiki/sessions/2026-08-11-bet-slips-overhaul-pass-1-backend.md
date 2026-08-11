---
date: 2026-08-11
agent: Codex
task: Bet Slips overhaul Pass 1 backend
code_commit: 3187b8d
status: implemented and locally validated; not deployed
---

# Bet Slips Overhaul — Pass 1 Backend

## Boundary

This pass adds derived advisory math and community publication lifecycle controls only. It reads frozen, calibrated `legs.model_prob` plus stored odds. It does not write to or alter MAIN probability, JIG scoring, HVY, tiers, ranking, calibration, `config.py`, `pipeline.py`, or the slate payload.

## Honest ticket analysis

`GET /api/tickets/{ticket_id}/analysis` is JWT-gated and owner-only. Public community slip payloads also receive the same allowlisted `analysis` object without exposing email or auth user ID.

Per leg:

- positive American odds implied probability: `100 / (odds + 100)`
- negative American odds implied probability: `abs(odds) / (abs(odds) + 100)`
- edge: `model_prob - implied_prob`
- EV per $1: `model_prob * decimal_profit - (1 - model_prob)`

Combined:

- probability: product of every active leg's frozen calibrated `model_prob`
- odds: actual stored ticket odds when present; otherwise product of leg decimal odds
- EV: `combined_probability * combined_decimal_odds - 1`
- explicit assumption: independent-leg probability product; not correlation-adjusted

Grade is driven only by combined EV:

- A: EV at least +10%
- B: EV at least +5% and below +10%
- C+: EV above 0% and below +5%
- C: EV exactly 0%
- D: EV from -10% through below 0%
- F: EV below -10%

Positive EV is `GOOD`/green, zero EV is `NEUTRAL`/amber, and negative EV is `POOR`/red. Leg count, probability, tiers, and qualitative signals never boost the grade. Missing odds leave the affected leg, combined EV, and grade pending; no price or grade is fabricated.

`honest_read.singles_would_be_better` is true when combined EV is below the best available single-leg EV. Confidence is explicitly data reliability, not win probability: missing/invalid odds, missing sample evidence, invalid model probability, or a sample under 10 PA produces LOW confidence; complete 10–29 PA evidence produces MEDIUM; complete 30+ PA evidence produces HIGH.

## Hand-verified control

Two-leg negative-EV fixture:

- Leg 1: model 20%, +350; implied 22.22%, edge -2.22pp, EV -10.00%
- Leg 2: model 16%, +500; implied 16.67%, edge -0.67pp, EV -4.00%
- Combined probability: `0.20 * 0.16 = 3.20%`
- Combined decimal odds: `4.5 * 6.0 = 27.0`
- Combined EV: `3.20% * 27.0 - 1 = -13.60%`
- Grade: F / POOR / red
- Best single EV: -4.00%; singles would be better: true

Positive-single control: model 20% at +450 produces 18.18% implied probability, +1.82pp edge, +10.00% EV, and A / GOOD / green.

## Slip lifecycle reset

`POST /api/tickets/complete` continues moving the submitted ticket out of `building` state and now returns:

```json
{
  "reset_slip": true,
  "active_ticket_id": null
}
```

The backend does not create an empty replacement ticket. Pass 2 must consume `reset_slip`, clear client state immediately after success, and let the next add create a fresh ticket ID.

## Community removal

`DELETE /api/community/posts/{post_id}` requires authentication and verifies ownership from JWT `sub`. It deletes only the `community_posts` publication row. The underlying ticket and legs remain intact. Public `GET /api/community/posts` remains open; POST and DELETE remain authenticated.

No Supabase migration is required for this pass.

## Validation

- Focused ticket/community/read-model suite: 23 passed
- Hand-check output: combined probability 0.032, combined EV -13.6%, grade F/POOR/red, LOW data confidence, singles-better true
- Route inspection: analysis GET, community DELETE, and ticket-complete POST registered
- `git diff --check`: passed
- Full backend suite: 58 passed, 1 unrelated pre-existing failure in `test_pitcher_detail.py`; the same failure reproduces in isolation on unchanged pitcher/Savant code
- Protected systems touched: no
- Migration applied: no
- Fly deploy: not performed; operator check required first

## Remaining Pass 2

Wire the frontend to send real per-leg odds and frozen sample evidence, render analysis/grade/confidence, consume `reset_slip`, auto-post on submit, add the owner remove button, and complete the remaining slip interaction/copy work.
