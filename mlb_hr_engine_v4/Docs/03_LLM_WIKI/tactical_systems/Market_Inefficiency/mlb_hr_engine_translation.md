---
title: Market Inefficiency - MLB HR Engine Translation
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# Market Inefficiency — MLB HR Engine Translation

## MAIN Impact

`clients/odds_api.py` — fetches HR prop lines for all qualifying players. Fuzzy name matching to model player rows. Falls back to `manual_odds.csv` when API key absent or limit reached. Returns American odds per sportsbook.

`engine/market.py` — American ↔ decimal conversion, no-vig probability calculation.

`engine/ev.py` — computes `ev_pct` and `edge_pct`:
```python
ev_pct = (model_prob * decimal_odds) - 1.0
edge_pct = model_prob - no_vig_market_prob
```

`engine/vig.py` — `no_vig_prob_for_book(book_name, american_odds)` applies book-specific vig corrections.

`engine/filters.py` — applies `MIN_EV_PCT = 3.0` and `MIN_EDGE_PCT = 2.0` gates. Both must pass for pick to reach output.

## JIG Impact

JIG reads `ev_pct` and `edge_pct` from player row. Applies danger layer logic:
- `ev_pct ≥ 5.0` → +1 danger layer
- `ev_pct ≥ 8.0` → +2 danger layers
- `edge_pct ≥ 4.0` → additional confirmation flag (not separate layer)

JIG also reads `market_prob_pct` and `model_prob` to compute implied edge ratio. When odds drift is available (from `line_snapshots.csv`), JIG evaluates drift direction — converging toward model = positive confirmation.

## STRATEGY Impact

STRATEGY uses market signals for:
1. Deployment timing: opening line vs current line comparison
2. Tier downgrade trigger: if `current_no_vig_prob` has moved ≥ 15% relative toward model_prob, edge may be priced in → downgrade one tier
3. Book priority selection: STRATEGY selects deployment book from vig tier ranking
4. CLV posture: STRATEGY flags early deployment recommendation when CLV history shows compression pattern

## Player Card Impact

Player cards display:
- `EV: [pct]%` — expected value percentage
- `EDGE: [pct]%` — model vs market probability gap
- `ODDS: [American]` @ [book]` — best available line
- `NO-VIG: [pct]%` — book's true probability after vig removal
- `CLV: [pp]` — closing line value when available from `clv_log.csv`
- `DRIFT: [direction]` — line movement indicator (opening → current)
- `STALE LINE` flag when book hasn't repriced for confirmed lineup/weather

## Escalation State Impact

Market signals feed [[HR_Threat_Escalation/overview]] as the 5th primary danger layer input:
- `ev_pct ≥ 5.0` → +1 layer
- `ev_pct ≥ 8.0` → +2 layers
- EV below `MIN_EV_PCT` → BLOCK condition (hard filter, pick never reaches output)

CLV impact on escalation:
- Positive CLV trend → confirms signal is persistent, not sample → supports tier maintenance
- Negative CLV trend → suggests edge is illusory → trigger tier downgrade

## Deployment Decision Impact

Market inefficiency is the final gate in the deployment chain:
```
barrel quality → environmental context → pitch mix → fatigue → EV/Edge gate
```

All prior signals can confirm but deployment is blocked if EV% < 3.0% or Edge% < 2.0%.

Deployment timing rules per doctrine:
1. Deploy at opening line when barrel-based edge identified before sharp money moves
2. Run `capture_closing_lines.py` 30 min pre-game for CLV capture
3. Run `ops_daily.py` morning after games for settlement and drift monitoring
4. Run `analyze_live_roi.py` weekly for real-vs-synthetic ROI comparison

## Operational Workflow

```bash
# daily workflow (from root)
py -3.12 main.py                          # generate picks
py -3.12 optimize_daily.py                # filter to optimized slate
py -3.12 capture_closing_lines.py         # pre-game CLV capture
py -3.12 ops_daily.py                     # morning settlement + drift
py -3.12 analyze_live_roi.py              # weekly ROI validation
py -3.12 monitoring_dashboard.py          # weekly health check
```

## Config Parameters

```python
# config.py
MIN_EV_PCT = 3.0         # minimum EV% filter gate
MIN_EDGE_PCT = 2.0       # minimum edge% filter gate

# engine/ev.py / engine/market.py (no config knobs — formula fixed)
# ev_pct = (model_prob * decimal_odds) - 1.0
# edge_pct = model_prob - no_vig_market_prob

# tracking/clv.py
# clv_pp = (close_no_vig - open_no_vig) * 100
# clv_pct_rel = clv_pp / (open_no_vig * 100) * 100
# SHARP: avg > 1.0pp | SLIGHTLY SHARP: > 0 | NEUTRAL: > -1pp | SOFT: < -1pp
```

## Related Doctrine Links

- [[Barrel_Quality/mlb_hr_engine_translation]] — barrel ≥ 8% required for EV to represent real edge
- [[HR_Threat_Escalation/mlb_hr_engine_translation]] — EV/Edge fire danger layers
- [[Confidence_Tiering/mlb_hr_engine_translation]] — odds movement triggers tier downgrade
- [[Environmental_Leverage/mlb_hr_engine_translation]] — weather not priced → structural market edge source
