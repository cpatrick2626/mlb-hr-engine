# Odds / CLV — Doctrine

> **STATUS: LIVE (CLV engine + Streamlit surface) — with one critical flag.**
> The odds source (The Odds API), opening/closing line capture, CLV computation, and CLV display in Streamlit are all real and operational.
> **FLAG: the production frontend/ board (Vercel) ODDS column is SYNTHETIC — derived from model HR probability (`full-slate-matrix.js:1500`: `980 - hrprob*31`), NOT real market odds. The board does NOT show real odds or CLV. Do not describe the production board as displaying market odds.**

---

## Summary

The Odds/CLV system fetches real market odds from The Odds API, captures opening and closing lines at pick time and after settlement, and computes closing line value — all surfaced in the Streamlit dashboard. The production React board (Vercel `frontend/`) does **not** consume this data; its ODDS column is a synthetic model-derived placeholder that resembles a betting line but is not one.

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

## CRITICAL FLAG — Production Board Odds Are Synthetic (NOT Real)

**`frontend/assets/js/full-slate-matrix.js:1500`:**

```js
"+" + Math.round(Math.max(150, Math.min(1200, 980 - o.hrprob * 31)))
```

The ODDS column on the production board is computed from model HR probability. It is **not** fetched from The Odds API or any market source. It is a placeholder-style value that visually resembles a betting line but carries no market information.

**Consequences:**
- The production board does **not** display real odds.
- The production board does **not** display CLV at all.
- Any value shown in the ODDS column is a deterministic transform of model output, not a market price.

This is a mock-in-production concern, consistent with the Ticket Slip overlay SAMPLE analytics issue documented in `ticket-slip-system.md`. Per honesty doctrine, displayed values must trace to real data or be clearly labeled as model-derived.

---

## To Fix (Backlog)

1. **Wire real odds** — pipe `data/odds_cache.json` real prices into the board's ODDS column via the FastAPI service (an existing `/api/picks` endpoint or new odds endpoint).
2. **Or label clearly** — if real odds are not wired, relabel the column (e.g., "Model Line") so its synthetic origin is explicit to users.
3. **Optionally surface CLV on the board** — currently Streamlit-only; could be added as a column once real odds are wired.

---

## Note on Surfaces

Streamlit (`app.py`) and the production React board (`frontend/`) are separate surfaces with no runtime cross-dependency. Real odds/CLV live in Streamlit. The production board does not consume them. See `production-surface-truth.md` for the authoritative surface map.

---

## Cross-References

- `production-surface-truth.md` — canonical surface map (which board is live, which is Streamlit)
- `ticket-slip-system.md` — parallel mock-in-production concern (overlay SAMPLE analytics)
- `main-model-doctrine.md` — model HR probability (`hrprob`) that feeds the synthetic ODDS formula
- Calibration / feedback loop doctrine (deferred; requires settled picks at scale)
- `clients/odds_api.py` — The Odds API client
- `tracking/clv.py` — CLV computation and line capture
- `data/odds_cache.json` — real odds cache
- `tracking/clv_log.csv` — CLV log (opening + closing + `clv_pp`)
