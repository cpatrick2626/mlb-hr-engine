# Odds / CLV — Doctrine

> **STATUS: LIVE.**
> The odds source (The Odds API), opening/closing line capture, CLV computation, and Streamlit CLV display are operational. The production Vercel board now displays the selected real sportsbook quote and its bookmaker when a quote exists. It does not display CLV.

---

## Summary

The Odds/CLV system fetches real market odds from The Odds API, captures opening and closing lines at pick time and after settlement, and computes closing line value in the Streamlit dashboard. The production React board consumes the selected sportsbook quote through `/api/slate` and shows ODDS, BOOK, implied probability, EDGE, and EV when a real quote exists. Missing quotes remain null.

---

## LIVE — Real (DOCTRINE)

### Odds source

- **Client:** `clients/odds_api.py:154` — fetches `batter_home_runs` market from The Odds API in American odds format.
- **Cache:** `data/odds_cache.json` — populated with 100+ real props.
- **Fallback:** `manual_odds.csv` — a stub file where all values are `"?"`. This is a fallback only; it does not carry real odds.

### Opening line capture

- `tracking/clv.py:81` — `log_opening_lines()` captures opening odds at pick time.
- Called from `app.py:375` (Streamlit dashboard) and `main.py:71` (CLI runner).

### Closing line capture + CLV computation

- `tracking/clv.py:148` — `fetch_and_compute_clv()` fetches closing odds and computes the delta.
- `tracking/clv.py:235` — CLV formula: `clv_pp = (close_nvp - open_nvp) * 100`.
- Same-day closing lines populate after the cron runs at 12:30 PM / 6:30 PM ET (`main.py:154`).

### CLV storage

- `tracking/clv_log.csv` — stores real opening + closing no-vig prices and `clv_pp` per pick.
- Example (2026-06-06): 45/46 picks logged; Isaac Paredes +750 → +850 `clv_pp −1.132`.

### CLV surface — Streamlit only

- `app.py:10376` — Closing Line Value section: avg CLV, beat-close %, SHARP / NEUTRAL / SOFT verdict.
- `app.py:10466` — table with open/close no-vig prices and `clv_pp` per pick.
- `scripts/analysis/analyze_clv.py` — offline CLV report by tier, book, and EV bucket.

---

## Production board market fields

`api/main.py` prefers a FanDuel HR quote when present and otherwise publishes the best available bookmaker quote. The payload includes `odds`, `odds_bookmaker`, `implied_prob`, `edge`, and `ev_pct`. These values stay null when no real quote exists.

Early-Day Decision Intelligence adds deterministic FAIR and BUY prices derived from model probability. Those prices are not sportsbook quotes and are labeled separately. Current EDGE/EV continues to use `model_prob` against the selected real quote. Projected EDGE/EV uses `model_prob_projected` against that same quote and does not replace the current fields.

`market_observed_at` is the selected quote's `last_update`. It is not a generated runtime timestamp. BetRivers Beta remains deferred: no trained Beta artifact or projected BetRivers range is shipped.

CLV remains a separate Streamlit/tracking surface and is not displayed on Full Slate.

---

## Note on Surfaces

Streamlit (`app.py`) and the production React board (`frontend/`) are separate surfaces. Streamlit owns CLV display. The production board consumes selected real market quotes from `/api/slate` but does not display CLV. See `production-surface-truth.md` for the authoritative surface map.

---

## Cross-References

- `production-surface-truth.md` — canonical surface map (which board is live, which is Streamlit)
- `ticket-slip-system.md` — parallel mock-in-production concern (overlay SAMPLE analytics)
- `main-model-doctrine.md` — model probability, ranking boundaries, and market-context rules
- `2026-09-16-early-day-decision-intelligence.md` — fair/buy pricing and decision semantics
- Calibration / feedback loop doctrine (deferred; requires settled picks at scale)
- `clients/odds_api.py` — The Odds API client
- `tracking/clv.py` — CLV computation and line capture
- `data/odds_cache.json` — real odds cache
- `tracking/clv_log.csv` — CLV log (opening + closing + `clv_pp`)
