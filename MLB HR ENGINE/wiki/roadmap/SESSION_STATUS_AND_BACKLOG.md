# Session Status & Prioritized Backlog (as of 2026-07-09)

Purpose: one-page next-session handoff. This document consolidates what shipped, what is highest leverage next, and what was corrected or de-scoped during the session.

---

## Shipped this session (committed + deployed)

- Splits display + full SPLIT SCOPE toggle (VS HAND/SEASON) + three-way batter card (season/vs-LHP/vs-RHP, HR+PA+rates, thin-sample amber tags). Retired fabricated platoon multiplier.
- FanDuel event deep-links (`fd_event_link`; efficacy pending FD appearing on odds feed).
- FanDuel search name-normalization (strip Jr./Sr./II-IV + accent-fold; display name stays full).
- Player-name dot §12 relabel: MATCHUP -> BATTER THREAT + two-axis tooltip (base = batter threat, glow = pitcher TARGET). Legitimate MATCHUP features left intact.
- Strategy Rail honesty remediation (`77f8354`): removed fabricated HR ENV SCORE; ELITE SPOT shows real MODEL HR %; PARK BOOST shows real PARK HR factor; POWER STACK / HOT STREAK / MODEL QUALITY / BAT-HAND LENS are marked HEURISTIC; stopped writing fabricated `signal_snapshot.rail.hr_env_score`. Display-only/no scoring impact confirmed.
- Graded May 17-31 whole-slate rows: `pick_tracker` now ~3,828 settled rows (was 737).
- Tooling: read-only doctrine-aware code-reviewer subagent (`.claude/agents/`); Supabase read-only MCP connected (`.mcp.json`, gitignored).

## Highest-priority next builds (by direct impact on live betting decisions)

1. **CALIBRATION FIX (`prob_scale`) — HIGHEST VALUE.**
   On 3,828 settled rows, board probabilities under-predict ~17.5% (`0.88` too aggressive). Model sound; issue is concentrated in 5-15% bands; high bands are well-calibrated. Fix = offline replay through the real scale -> Platt path + regression, **not** a blind scalar edit. Fable-tier, scoring surface. Raw-proxy best-fit ~1.067, but Platt-downstream means that is not a literal config value. FLAG: grading May rows armed `auto_apply_safe` (`pipeline.py:623`) — a pipeline run could auto-move `prob_scale`; decide whether to freeze it first.

2. **`picks` RLS security fix — READY, low-risk.**
   One line: `alter table public.picks enable row level security;` No policies needed if all app access remains service-role, which bypasses RLS; frontend never reads `picks` directly; no anon writes. Optional `beta_users_read_picks` SELECT policy only if an external anon-key reader exists. Operator runs SQL manually + tests: cron insert, `/api/slate`, `/api/picks/today`, `/api/strategies` still work; anon REST blocked. Instant revert available.

3. **STRATEGY room rebuild.**
   Scoped in `strategy-section-spec.md` §11 port map: lift odds/EV/parlay math, adapt builders, rebuild composites as transparent filters, ledger-based per-strategy tracking, phased P1-P5, reimagine not 1:1. Separate from COMMAND.

4. **LIVE TARGETS banner rebuild.**
   Currently 100% hardcoded mock, intentionally unwired (`ticket-slip-system.md`). Needs new JWT-gated endpoint `GET /api/tickets/live-targets` returning user's committed legs (`completed_at IS NOT NULL`, `removed = false`, today's `leg_date`) + join to `slate_games` for game status. v1 = game-level status (honest). v2 = live inning/HR detail needs new live-linescore source (`/api/slate` lacks it — do not fake it). Frontend reuses `LiveTargets` / `TargetCard` / marquee. Backend endpoint = Fly deploy.

## Lower-priority / later

- Multi-season splits (small-sample fix; Fable-tier weighting design; revisit after living with this-season toggle).
- FanDuel deep-link efficacy verification once FD appears on odds feed.
- AEI pitcher-arsenal dashes -> optional "thin sample" tag (cosmetic; data verified honest / no integrity risk — sample gates working).
- Analyst agents (`design-expert-agent-layer.md`); fold into STRATEGY P5, consume typed outputs, non-authoritative until ledger-validated.

## Corrections to prior backlog (verified this session)

- Slip-integrity bugs (`removeLeg` client-only, no `resetSlip`) are already fixed (server soft-delete + `resetSlip` present) — remove from backlog.
- Dot polarity is correct; it was only mislabeled and is now fixed.
- AEI dashes are cosmetic, not integrity; sample gates work as designed.

## Standing awareness

- Auto-learn (`auto_apply_safe`) runs every pipeline run, learns from `pick_tracker`, and currently has `prob_scale = 0.88`. Grading May rows may let it re-derive on next run — freeze before deliberate calibration if you want `0.88` held.
- `legs.player_id` is TEXT, `picks.player_id` is INTEGER — cast needed if joining.
- Tooling: use `@code-reviewer` before protected-surface commits; Supabase MCP is read-only for direct ledger queries.

## Source anchors

- Recent shipped commits: `git log --oneline -15` through `dd5b61a`.
- Calibration finding: `wiki/log.md` 2026-07-08 `prob_scale=0.88 calibration re-audit`.
- Strategy port reference: `wiki/roadmap/strategy-section-spec.md` §11.
- Current sync check before writing: `HEAD == origin/main == dd5b61a55c93d8d5b48625697ee728862dfe54a7`.
