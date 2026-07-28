# TCC — Tactical Command Center Doctrine

> **STATUS: LIVE — three surfaces.** See mock/partial flags per surface below.

**Last Updated:** 2026-07-24
**Authoritative root doc:** `MASTER_TCC_DOCTRINE.md` (Streamlit layer — see scope note)

---

## Summary

TCC (Tactical Command Center) is the operator's filter and overview layer — it orchestrates what is shown and filtered; it does not compute scores or alter model probabilities. Three separate TCC surfaces exist across two deployment targets (Streamlit dashboard and production frontend). They share the same doctrine philosophy but are independent implementations.

The full filter architecture, preset philosophy, engine-scope isolation rules, and contamination anti-patterns are specified in **`MASTER_TCC_DOCTRINE.md`**. This wiki page is a live-surface summary and index only — do not duplicate the root doc here.

---

## Surface Map

| Surface | File | Scope | Status |
|---------|------|-------|--------|
| Streamlit filter controls | `mlb_hr_engine_v4/app.py` + `filter_controls.py` | MAIN + JIG threshold filters, preset bars | LIVE |
| Frontend — CommandCenter overlay | `frontend/assets/js/fa8fdb8f-2a92-4a2c-acfe-e38e50d6e9f4.js` + `0ead2d7a-98fd-4c05-9412-e8c9b12b1861.js` | 9-panel filter UI and room-filter predicates | LIVE (partially wired — see checkpoint/flags) |
| Frontend — COMMAND tab | `frontend/assets/js/command-tab.js` | 4-panel tactical read-only overview, engine toggle | LIVE |

---

## Surface 1 — Streamlit TCC (`filter_controls.py` / `app.py`)

This is the surface the root doc describes. LIVE in the Streamlit operator dashboard.

- `render_filter_control()` — single threshold control (`st.number_input`)
- `render_preset_bar()` — one-click preset buttons
- MAIN presets: `Operational`, `Selective`, `Elite Only` (namespaced `tac_*`)
- JIG presets: `All Tactical`, `Selective`, `Matchup+` (namespaced `jig_tac_*`)
- `_tac_filter_fp` fingerprint cache prevents redundant filter reruns
- Cross-engine key isolation enforced: MAIN reads `tac_*` only; JIG reads `jig_tac_*` only

See `MASTER_TCC_DOCTRINE.md` §§ 2–4, 9 for filter vocabulary, preset rules, and isolation invariants.

---

## Surface 2 — Production Frontend CommandCenter Overlay

Current overlay UI: `frontend/assets/js/fa8fdb8f-2a92-4a2c-acfe-e38e50d6e9f4.js`
Current defaults/predicates/counters: `frontend/assets/js/0ead2d7a-98fd-4c05-9412-e8c9b12b1861.js`

Opens inside the production board stage. Renders 9 filter panels via `Stepper`, `Dropdown`, and `Toggle` components. `APPLY TO ROOM` stores the active room's filter object in the existing `md_roomFilters` channel; MAIN and JIG retain separate room keys.

### Panels (as coded)

| Panel | Title | Type |
|-------|-------|------|
| 1 | Batter Power & Contact | Steppers: ISO, xSLG, Barrel %, Hard Hit %, Avg EV, HR/FB % |
| 2 | Launch & Contact Shape | Steppers: Pull Air %, Launch Angle, HR Window %, Sweet Spot %, Fly Ball % |
| 3 | Matchup & Splits | Steppers: vs RHP ISO, vs LHP ISO, Pitch Type Damage %, Matchup Modifier %, HVY Score |
| 4 | Pitcher Vulnerability | Steppers: Total HR Allowed, HR/9, Barrel % Allowed, HH % Allowed, FB % Allowed, Pull Damage Allowed % |
| 5 | Environment | Steppers: Park HR Factor, Wind MPH, Temperature, Humidity; Dropdowns: Wind Direction, Air Density |
| 6 | Advanced HR Signals | Steppers: Contact Shape Score, Arsenal Matchup Score, Opposite Field Weakness %, Lifted HH %, EV Trend |
| 7 | Momentum & Recency | Steppers: Recent HRs (7G), Recent HH % (7G), Recent Barrel %, Hot Streak Indicator, Recent EV Trend, LA Trend |
| 8 | Game Context | Read-only status display (see below) |
| 9 | Output Control | Min Projected HR %, Min Confidence %, Max Players, Sort By, Sort Direction |

### 2026-07-24 Environment Filter Checkpoint

Temperature, wind speed, and wind direction are now wired through the live slate as display/filter-only fields:

- Pipeline game records emit numeric `temp_f`, `wind_mph`, and meteorological `wind_deg`, keyed by MLB `game_pk`.
- `/api/slate` joins the game record to each MAIN/JIG player row by `game_pk` with frontend `gameId` fallback and also keeps the fields on `slate_games`.
- Temperature and wind controls are minimum thresholds. Rows with missing weather pass rather than being silently dropped.
- Wind Direction is categorical: frontend buckets `wind_deg` into `N / NE / E / SE / S / SW / W / NW`.
- The three controls participate in draft state, defaults, `APPLY TO ROOM`, active-filter counts, reopen persistence, and RESET.
- Air Density remains dead: there is no source and no density formula was introduced.
- The passthrough is additive only. Raw fields do not feed `model_prob`, `jigScore`, `hrFactor`, ranking, tiers, EV, or any scoring formula.

Local real-slate proof on 2026-07-24: 389 MAIN + 389 JIG rows across 15 games; every player weather tuple matched its game. Hunter Goodman (`COL-MIL`, `game_pk=823759`) matched `78.4°F`, `13.5 mph`, `122°`. Browser proof on a 389-row local slate: Temperature `>=85°F` produced 18 rows, Wind `>=10 mph` produced 15, Direction `E` produced 15, values persisted on TCC reopen, and RESET restored 389.

Production remains gated: the backend changes require a Fly deploy and then a fresh pipeline run before the production cache and player rows carry the numeric fields.

### Panel 8 — Game Context (honest after commit 9514a4d, 2026-06-27)

Previously contained fake Toggle components with hardcoded on/off states. Replaced with honest read-only key-value rows:

| Key | Value (hardcoded) |
|-----|-------------------|
| LINEUP MODE | Confirmed lineups |
| POOL EXPANSION | Not active |
| REASON | Projected lineup source unavailable |
| FALLBACK | Active roster used only when an official lineup is missing |

This is a status display, not interactive controls. These values are hardcoded strings, not API-driven.

### ⚠ Mock / Unconfirmed in this surface

- **CommandHeader status bar:** "ACTIVE SLATE: 8 GAMES", "SYSTEM LOAD: 14%", "CURRENT PRESET: DEFAULT TACTICAL", "Active Filters: 12" — hardcoded strings, not pulled from real state.
- **Footer:** "UPDATE TIMER: 28s", "ACTIVE FILTERS: 12", "TACTICAL MODE: ENGAGED" — hardcoded.
- **VisibilityPanel:** Toggles have hardcoded `on` values; "LYAR TREKRM MODE" appears to be a garbled placeholder label. Buttons are decorative.
- **Remaining unwired controls:** Controls not named in the checkpoint above or prior scoped wiring phases may still be decorative. Do not infer a live predicate from the presence of a `Stepper` or `Dropdown`.
- **Panel 8 values:** Strings are hardcoded, not API-driven. Accurate as a static description of current system behavior, but not reactive.

---

## Surface 3 — Production Frontend COMMAND Tab

`frontend/assets/js/command-tab.js`

The "COMMAND" nav tab. Four-panel read-only tactical overview. Engine toggle: MAIN (red) / JIG (cyan). Reads from live window globals: `window.LEADERBOARD_ROWS`, `window.LEADERBOARD_ROWS_JIG`, `window.SLATE_GAMES`, `window.SLATE_GENERATED_AT`. No mock data.

### Panels

**P1 — Slate Command Strip [NEUTRAL]**
DATE, GAMES, BATTERS, CRITICAL (APEX count), ELEVATED (ELITE+EDGE count), ACTIVE (non-COLD). SYNCED shows time-ago from `SLATE_GENERATED_AT`; turns warning color if stale (>720 min).

**P2 — Primary HR Threat Zone [MAIN red / JIG cyan]**
Top 6 picks from the active engine, sorted by HR prob (MAIN) or JIG score (JIG). Per-card: rank, name, team, opponent, game time, HR PROB or JIG IDX + MATCHUP quality, BARREL %, HH %, ENV (hrFactor), TIER, add-to-slip button. HVY flag shown when `opphr ≥ 1.3`. Add-to-slip wired for both MAIN and JIG boards.

**P3 — Pitcher Vulnerability Strip [NEUTRAL]**
Top 7 pitchers from MAIN rows, deduped by pitcher, sorted by `opphr` descending then `pitcher_barrel_allowed`. Per-card: name, HR/9, bar fill, badge (EXPLOITABLE ≥1.3 / ELEVATED ≥0.9 / STANDARD / PENDING).

**P4 — Escalation Feed [MAIN — shown in both engine modes]**
Up to 8 MAIN rows with a recognized tier (APEX/ELITE/EDGE/SIGNAL/WATCH), sorted by priority then `hrprob`. Shows tier level label, player name, team, LIVE flag if `gameStatus === "Live"`. Rows 4–8 dimmed.

### Real vs mock

All panels source from `window.LEADERBOARD_ROWS` / `window.SLATE_GAMES` / `window.SLATE_GENERATED_AT` — live API data. No mock blocks detected. "NO DATA" is shown when the source arrays are empty.

---

## Root Doc Scope Note

`MASTER_TCC_DOCTRINE.md` (dated 2026-05-21) describes the **Streamlit TCC only** — `filter_controls.py`, `st.number_input`, `session_state` namespacing, MAIN/JIG preset dicts. It does not mention the production frontend surfaces (CommandCenter overlay or COMMAND tab). Those are separate production implementations that post-date the root doc.

The filter philosophy, engine isolation rules, and anti-patterns in the root doc apply by doctrine to all surfaces, but the frontend implementations were not specifically covered when the root doc was written.

---

## Cross-References

- [`MASTER_TCC_DOCTRINE.md`](../../../../MASTER_TCC_DOCTRINE.md) — authoritative filter architecture, preset philosophy, engine isolation rules
- [`production-surface-truth.md`](production-surface-truth.md) — which frontend surfaces are live vs prototype
- [`full-slate-matrix.md`](full-slate-matrix.md) — Full Slate filter behavior and TCC filter scope for the slate view
- [`main-jig-separation.md`](main-jig-separation.md) — MAIN/JIG engine isolation doctrine
