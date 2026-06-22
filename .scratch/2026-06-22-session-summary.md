# Session Summary — 2026-06-22

Continuation from prior session (commit 34d718a). Covers: confidence-ranking
investigation, platoon resolution, HR9 defer, conf-tier "C" fix + deploy, and a
full-repo cleanup. Plus one NEW unresolved contradiction (app.py).

## SHIPPED

### Conf-tier "C" mislabel — FIXED + DEPLOYED (6081e4e)
- Root cause: _enrich_with_ev (pipeline.py ~447-448) early-returns for no-odds
  players -> confidence never set -> no-odds else-branch (pipeline.py ~739-743)
  read conf=0/edge=0 -> confidence_tier(0,0) fell through to "C" catch-all.
- Fix: key-presence check ("confidence" not in p) -> stamp "NE"; evaluated rows
  (incl. genuine computed 0) still go through confidence_tier() unchanged.
- Validated LOCALLY on live engine: 10 NE / 8 graded (6 C, 2 B) on an 18-player
  degraded slate — exact reconciliation with "10 no-odds, 8 matched."
- Committed 6081e4e, pushed, deployed to Fly (flyctl). Engine + cache + P&L log
  now correct.
- IMPORTANT CAVEAT: confidence_tier is NOT serialized to /api/slate (live payload
  row keys: tier, model_tier_rank, quality, model_prob — no confidence S/A/B/C/NE).
  So the "C"/"NE" label was only ever VISIBLE on the dead Streamlit surface
  (strategies_ui.py). Live Next.js board never showed it. Real benefit = P&L log
  no longer records false "C". See OPEN: cache.py serialization gap.

### Full-repo cleanup — COMMITTED (cedfd89), push pending
- 229 files / 32,175 deletions. Removed: v1/v2/v3 trees, root frontend/ (dead Vite
  build), test/, archive/, _volume_backup_2026-06-17/, compare.py, stale root files,
  junk/logs. All git-recoverable (in history at cedfd89^).
- Verified live tree intact: zero mlb_hr_engine_v4/ paths deleted; v4 frontend,
  requirements-api.txt, graphify-out all confirmed present post-commit.
- G6 (dead Streamlit) HELD — see OPEN/app.py below.

## RESOLVED (no action needed)

### Platoon factor "neutral collapse" — NOT A BUG
- Original lead (missing handedness -> 1.0 collapse) and the impact-diagnostic
  (degenerate total_rate==0 on zero-HR hitters) were BOTH wrong on inspection.
- Stage 1b empirical: the one 1.0 row (Jared Young) is path (c) — 100% of PA vs one
  handedness, so Bayesian shrinkage has no deviation signal and correctly outputs
  1.0. Correct model behavior, not a defect. probability.py:377 else-branch is dead
  code under normal data flow (rates+PA written atomically, pa>=30).
- Three layers of characterization overturned by verification. No patch.
- Optional LOW-risk follow-up: display-only plat_src:"one-sided" label for operator
  visibility (writes to assembled dict, never model_prob). Own scoped task if wanted.

## DEFERRED

### HR9 collapse (hr9_conf=6.0 fallback) — DEFER pending healthy slate
- Mechanism confirmed: pit_ip<5 (or 0 HR) -> pitcher_hr9=0.0 -> else-branch ->
  hr9_conf=6.0 neutral. Gate collapses missing AND true-zero identically.
- 0/72 inflated on the measured (degraded) slate — but slate was odds-degraded and
  too thin for a base rate. Re-measure on a 200+ healthy-odds slate before deciding
  depress / flag+cap / leave. Fix lever (the else branch) is cleanly independent.

## OPEN — needs attention next session

### app.py CONTRADICTION (HIGH interest)
- G6 cleanup gate found app.py last modified by commit 9980700 (2026-06-19):
  "fix(tracking): surface 4 silent persistence-path excepts (18-day pick_tracker
  gap root cause)" — a REAL production tracking fix, +41/-27.
- Contradiction: app.py is framed as the DEAD Streamlit surface (Lead 2, slated for
  removal), yet a production tracking root-cause fix was committed into it 3 days ago.
- Implications: (a) app.py canNOT be safely deleted right now; (b) either the fix
  belongs in a live module and was placed in the wrong file, OR app.py is not as
  dead as assumed. Resolve before any G6 removal.
- G6 items HELD intact: app.py, strategies_ui.py, components/, .streamlit/.

### cache.py -> /api/slate serialization gap
- api/cache.py:82 puts confidence_tier into the serialization dict, but the live
  /api/slate payload does NOT contain it. Something between cache and the FastAPI
  response drops it (response model/schema filter, or /api/slate reads a different
  path). Determines whether the shipped "NE" value reaches ANY live API consumer or
  only the P&L log. Small read-only trace. Not a Streamlit issue.

### Odds API reliability — 4/4 slates failed this session
- Every slate observed degraded: live odds fetch failed, served stale cached props,
  ~8-21 of ~18-72 players matched. Upstream cause of the thin slates that blocked
  HR9 sizing and made "NE" dominate the board.
- If no-odds is the steady state, "Option B" (score no-odds players on non-market
  signal: data quality + contact + pitcher matchup, ~0-70 pts available) becomes the
  high-value fix that keeps Full Slate useful on a normal day. Currently no-odds
  players are correctly labeled NE but unranked on confidence. MEDIUM risk (touches
  confidence scoring path, not model_prob core). Decide deliberately.

## METHOD NOTE
Every confident characterization this session was overturned on inspection (plat_conf
"fallback" misread x1; platoon cause misattributed x2; HR9 magnitude unmeasurable on
degraded slates; app.py "config drift" -> real fix). Read-only-before-fix and the
staged gates caught all of them. Keep the discipline.
