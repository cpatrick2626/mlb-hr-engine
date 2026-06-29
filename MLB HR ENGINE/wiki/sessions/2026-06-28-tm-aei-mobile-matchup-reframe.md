# Session: TM Score, Arsenal Edge Intel, Mobile Card View, Matchup Reframe — 2026-06-28

Date: 2026-06-28
Agent: Claude (PM) + Claude Code (execution)
Owner: Operator (Kylar)
Project: MLB HR ENGINE - OPERATIONS
Risk Class: MIXED (frontend LOW; one authorized additive API-layer change MEDIUM)
Phase: Multi-feature build session — frontend surfaces + True Matchup composite
Status: COMPLETE / SHIPPED

## Scope

A multi-feature build session. All work shipped to `origin/main`; Vercel auto-deploys frontend on push; API change deployed via `flyctl deploy` + `gh workflow run daily_pipeline.yml` (cache rebuild).

Protected scoring/model surfaces (`engine/`, `pipeline.py` scoring, `config.py`, `probability.py`, `_jig_score`, MAIN/JIG ordering, HVY, tickets) were NOT modified. The single backend change (`true_matchup_score` in `api/main.py`) is an additive, serialization-only display field — operator-authorized, inert, never fed into scoring/ordering.

---

## Commits (chronological, this session)

| Commit | Summary |
|--------|---------|
| `a10cfe9` | HR/9 + PITCHER TIER fix (alias `pitcher_hr9` into leaderboard row) |
| `e987e39` | Pitcher Card stat-rail label correction ("PITCHER SEASON STATS") |
| `9514a4d` | TCC GAME CONTEXT fake toggles → honest read-only lineup-status panel |
| `10425bd` | Full-slate cap: default `maxPlayers` 75 → 999 (per-browser localStorage) |
| `4dadb60` / `cdd3993` | Pitcher Card Step 1: Arsenal Command HUD on pitcher side, HUNT THIS on exploit pitch |
| `585681f` | Arsenal Edge Intel three-panel matchup view replaces FsmPitchMix (preserved unrouted); HUNT THIS badge fix |
| `e2360fa` | AEI verdict reframe: edge-score headline, confidence as %, OVERALL EXPLOIT CONFIDENCE card, EXPLOIT CONF chip; removed single-pitch raw-rate card |
| `c12adc9` | Full Slate mobile portrait card view (stacked labeled-tile cards, 6-col grid + expand) at ≤768px |
| (mobile fix) | Mobile card CSS: flex-wrap → CSS grid (uniform tiles, clean header, no floating HR cell); removed portrait orientation gate |
| `6e77936` | Main Slate matchup cell reframe Phase 1: HR PROB headline, BATTER EDGE (raw 0–10), SIGNAL; removed matchup text + key pitch from slate |
| (TM Step 1) | `true_matchup_score` added in `api/main.py` (40/30/20/10 composite), serialization-only, inert |
| `c438312` | TM Step 2: matchup gauge wired to real `true_matchup_score` — TM label, fixed band colors, honest 0–100 arc; single source of truth (no client fallback) |
| `6957315` | Full Slate: TM/HR PROB role-style filter toggles (TM≥60, HR≥15%, AND-intersection); RANK = sort/default |

---

## Key features shipped

### Arsenal Edge Intel (AEI)
Three-panel matchup-gauge detail view (PITCHER ARSENAL | ARSENAL EDGE VERDICT | BATTER DAMAGE PROFILE) replacing `FsmPitchMix` (preserved unrouted as rollback). Verdict headlines the engine's arsenal-edge read; raw per-pitch HR/PA demoted to per-pitch table; OVERALL EXPLOIT CONFIDENCE sourced from `arsenal_edge_confidence`. All values real; no invented numbers; scoring untouched. 146 `aei-*` refs.

### True Matchup Score (TM)
New 0–100 composite (`true_matchup_score`) — see `doctrine/true-matchup-score.md`. Computed in `api/main.py` serialization only; 40% HR prob / 30% batter edge / 20% signal / 10% pitcher vulnerability; inert (never feeds MAIN/JIG/HVY/tickets). Gauge wired with honest scale + fixed bands (ELITE 60+/STRONG/AVG/WEAK/COLD). Distribution checked before banding (tuning slate: 13–72, median 34; live slate ran to 81).

### Mobile portrait card view (Full Slate)
At ≤768px the Full Slate table becomes stacked per-player cards (tier+roles | name | TM gauge header, then a 6-column labeled stat-tile grid via CSS grid + `data-label`, with `+N MORE STATS` expander). Follows the established `-desktop`/`-mobile` convention. Desktop table unchanged.

### Matchup cell reframe (Phase 1)
Slate matchup cell → HR PROB (headline) / BATTER EDGE (raw `arsenal_edge_score` 0–10, unsigned) / SIGNAL (`arsenal_edge_confidence` %). Removed Elite/Strong matchup text and key pitch from the slate (key pitch remains in AEI modal).

### Sort + filter controls
RANK / TM / HR PROB controls. RANK = sort/default (reuses existing `onSort`/`sortState`). TM & HR PROB = role-style filter toggles (TM≥60, HR≥15%, AND-intersection when both on). View-only; MAIN ranking untouched.

---

## Invariants Preserved
- Model/scoring/probability formulas unchanged
- MAIN ordering (`model_tier_rank`) and JIG ordering (`jigScore`) unchanged
- `true_matchup_score` is serialization-only and inert — confirmed not referenced by any scoring/ordering path
- MAIN/JIG separation intact; HVY untouched; tickets untouched
- Data discipline: `model_prob` decimal 0–1, `hrprob` ×100, `jigScore` 0–100, `true_matchup_score` 0–100 — no confusion; no invented numbers

---

## Known follow-ups (see doctrine/known-gaps.md)
- TM band + filter-cutoff tuning after observing several live slates (display-only, trivial)
- Mobile role badges: `.fsm-roles` clustering beside tier chip (small JSX) for exact mockup fidelity
- Landscape: wide landscape phones (>768px) still hit the table
- AEI Phase 2: expose per-pitch confidence (protected backend, authorized-when-ready)
- Pitcher Card (standalone): needs backend data contract (bulk lineup+BvP, pitcher profile fields)
- `engine/arsenal_edge.py` git-tracked confirmation (API imports it)

---

## Files Touched By This Documentation Session
- `MLB HR ENGINE/wiki/doctrine/true-matchup-score.md` (new)
- `MLB HR ENGINE/wiki/log.md`
- `MLB HR ENGINE/wiki/doctrine/production-surface-truth.md`
- `MLB HR ENGINE/wiki/doctrine/known-gaps.md`
- `MLB HR ENGINE/wiki/sessions/2026-06-28-tm-aei-mobile-matchup-reframe.md`
- `MLB HR ENGINE/wiki/sessions/_Index_of_sessions.md`

## Post-session maintenance
- Graphify: graph rebuilt to index `api/main.py` TM change (was STALE since 2026-06-22). Re-run `.claude/graphify_freshness.py` to confirm FRESH.
