# Session Capstone — 2026-07-14

Single-narrative tie-together of the session. Individual phase notes hold detail; this is the arc + outstanding obligations.

## The arc
A 7-surface scoring audit sweep found a P0, and unwinding it exposed a month-long silent outage in the calibration loop. The session: fix the foundation, harden it so it can't silently break again, then build a new feature backend on the solid base.

1. Audit sweep (7 scoring surfaces) -> found the pnl.py P0, mapped every surface.
2. P0 pnl.py fix (f817fe9) -- 210 smart-quote glyphs threw SyntaxError for 25 days, silently killing settlement/CLV/CLI. Fixed, deployed (Fly v96+).
3. Settlement backfill + CLV reconcile + live calibration rollup (11be08a) -- APEX confirmed 20.0% actual on n=3,828. Flagship claim holds. Decision: do NOT retune (sample stale/small; honors n<200 rule).
4. Deeper find: calibration loop captured NO new qualified-pick data for a month. Two independent outages: (a) missing ODDS_API_KEY GitHub Actions secret -> empty odds -> 0 qualified -> 0 inserted (source_tab='cron' rows = 0 ever); ROOT CAUSE, FIXED (secret added, confirmed reaching pipeline as ***). (b) ephemeral GH-runner filesystem -> CSV tracking writes vanish (Outage 2, permanent fix = Supabase-authoritative logging, deferred to post-Jul-16).
5. Two loud-failure guards so this class can't silently recur: observability guard (e486eb1, capture failure -> workflow RED, does NOT false-alarm on no-games days); fail-closed writer (6b439f5, persistence failure -> workflow RED).
6. jigTier (f27dff1 API + 97d949a/1c7d3dc frontend) -- killed the 100%-APEX bug. Ratified 0-100 bands (APEX>=88...), native backend jigTier, single config source. Validated spread: APEX ~7.7%.
7. Player Intelligence backend B1-B5 -- new /api/batter-detail endpoint, scoring engine provably untouched (hash-verified every phase).

## Earlier same session (own notes exist)
- 6-step AEI legibility redesign.
- BVP/recent-form overlap + color-valence (desktop + mobile).
- Complete doubleheader collision fix -- all 5 sites + row-id keys, proven non-DH invariant, two validation audits. Load-bearing findings: Site E is NOT display-only (feeds edge/EV/qualification/picks-log); row id must stay raw player_id (composite ripples through ticket storage).

## Player Intelligence backend -- state (IMPORTANT for Jul 16)
New /api/batter-detail. Isolated display-only cache (clients/batter_pitch_profile.py, _BATTER_PITCH_PROFILE_DISPLAY_CACHE) -- never touches _BATTER_PT_CACHE (feeds JIG scoring). All 5 phases hash-verified: no scoring / _jig_score / _true_matchup_score / arsenal_matchup_factor / /api/slate change.
- B1 aggregate (8e3ffe3) -- DEPLOYED, live.
- B2 derivations (e28158b) -- DEPLOYED, live. (real ISO, guarded season pace [>=30g + 80-HR clamp], HR-env 0-10 park-weighted, handedness label, 20g trend. Percentiles deferred -- no reference population.)
- B3 per-pitch xwOBA + barrel% -- COMMITTED, DEPLOY HELD.
- B4 all-pitches whiff% + tactical pills/damage/verdict (81854e4) -- COMMITTED, DEPLOY HELD. Contracts: pill EXPLOIT>=.380 / HUNT .340-.380 / NEUTRAL; damage = xwOBA scaled .200-.500 -> 0-100; verdict DEPLOY (exploit pitch at >=20% usage) / WATCHLIST / HOLD / SCRATCH.
- B5 hardening (678237f) -- COMMITTED, DEPLOY HELD. DH-safe cache key, graceful degradation (fully-degraded = 200 + all-Gap, never 500), stable contract, 11/11 contract tests.
B3+B4+B5 on origin/main but NOT live on Fly -- held for live-slate JIG-order proof. Endpoint not called by GH cron, so committing without deploying is safe.
Remaining for the feature: frontend surfaces (Batter Card + Pitch Mix modals). Design specs exist; backend contract fixed + degradation-safe. Plus B5's noted latency follow-up (sequential Savant calls not parallelized).

## JULY 16 CHECKLIST (first game day -- do ALL; #1 silently bites if skipped)
1. flyctl deploy -- ships held B3+B4+B5. Without this the per-pitch surfaces never activate.
2. Verify JIG order unchanged on the live slate -- the acceptance gate the held phases waited for.
3. Capture verify -- gh workflow run daily_pipeline.yml; confirm CAPTURE_SUMMARY non-zero games/odds/qualified, source_tab='cron' rows in Supabase, run GREEN, idempotent on rerun.
4. jigTier renders a real spread (not all-APEX, not all-COLD).
5. Spot-check /api/batter-detail on a real player -- returns populated data (404s during break only because cache empty).

## Open follow-ups (none urgent)
- Supabase-authoritative pick logging (Outage 2 permanent fix) -- audit done, Phases 0-5 spec exists; build AFTER Jul-16 proves capture. Phase 0 is a production schema migration against a drifted table -- do deliberately.
- BOO / SUP junk GitHub secrets -- clean up after Jul-16 confirms ODDS_API_KEY.
- Pre-existing app.py syntax error + /api/pitcher-detail display-cache isolation test failure -- surfaced during B-phase tests, NOT ours, backlog.
- rapidfuzz dependency -- confirm in requirements.
- pitcher_status rename (#4), TM band retune, control-bar cleanup, #5 Poisson recalibration (needs ~3-4wk fresh post-break data), 50-row raw-state coverage limit, batter-vs-team-games denominator for season pace.

## Graphify
Refreshed mid-session, went STALE again after B1-B5. Re-refreshed at session close.
