# System Knowledge - Confidence, Platoon, Serialization

Durable facts about how the live v4 engine behaves. NOT session notes - these are
permanent properties verified empirically on 2026-06-22. Read these before any
investigation touching confidence tiers, platoon factor, or the /api/slate payload.
They have each independently caused a misdiagnosis when unknown.

## SERIALIZATION CONTRACT - what /api/slate actually exposes

The live /api/slate payload (leaderboard_rows) does NOT contain confidence_tier or
the confidence sub-scores. Verified from the deployed payload - row keys include:
tier, model_tier_rank, quality, model_prob, plus stat fields. There is NO
confidence S/A/B/C/NE field, no hr9_conf, no plat_conf, no pit_ip.

Implications:
- The confidence tier (S/A/B/C/NE) is engine-internal + API cache + P&L log only.
  It is NOT visible on the live Next.js board.
- "tier" and "quality" in the payload are the DEPLOYMENT tier (APEX/ELITE/EDGE/
  SIGNAL/WATCH/COLD), NOT the confidence tier. Do not conflate.
- Any investigation that observes a confidence-tier value is looking at a non-live
  surface (Streamlit strategies_ui.py) or an internal dict - NOT the production board.
- OPEN QUESTION: api/cache.py:82 puts confidence_tier into the serialization dict,
  yet /api/slate omits it. The drop happens between cache and the FastAPI response
  (response model/schema filter, or /api/slate reads a different path). Unresolved.

## CONFIDENCE SCORE - component breakdown (probability.py:518 confidence_score)

Returns a single 0-100 scalar (line 573). Sub-scores are LOCALS - they never leave
the function. To observe them you must read engine-side, not the API.

Components:
- Data Quality    0-30  (season PA + Statcast source: current 12 / blended 8 / prior 5)
- Contact Quality 0-20  (barrel% vs league avg)
- Pitcher Matchup 0-20  (HR/9 deviation + platoon edge)
- Market Signal   0-30  (edge SNR + book consensus)
- Penalty         -8    (lineup not confirmed)

KEY FACT for no-odds players: a player with no market odds forfeits ONLY the Market
Signal component (30 pts). The other 70 pts (data + contact + matchup) are still
computable. A strong no-odds player (high PA, current Statcast, elite barrel,
vulnerable pitcher) could legitimately score ~60-65 = A-tier - but currently is
never scored at all (see _enrich_with_ev early-return below). This is the basis of
the "Option B" decision.

## CONFIDENCE TIER ASSIGNMENT - two sites, one bug fixed

confidence_tier() thresholds: S>=70, A>=55, B>=35, else C. Defined in ranker.py.
Assigned at TWO sites:
- ranker.py:~71 (rank_picks): qualified picks, real conf/edge. Legitimate.
- pipeline.py:~739 (no-odds else-branch): for non-enriched players.

FIXED 2026-06-22 (6081e4e): _enrich_with_ev (pipeline.py ~447) early-returns for
no-odds players, so confidence/edge_pct were never set; the else-branch read them as
0 and confidence_tier(0,0) fell through to "C". Now: if "confidence" not in p, stamp
"NE" (not evaluated) instead. Evaluated rows - including a genuine computed 0 - still
go through confidence_tier() unchanged. The distinction is KEY-PRESENCE, not value:
"never ran" (NE) vs "ran, scored low" (C) are different states.

## PLATOON FACTOR - the FOUR paths to 1.0 (probability.py:332-378)

platoon_factor() can return exactly 1.0 via FOUR distinct paths. Three separate
investigations misdiagnosed this in 2026 because only some paths were known. ALL of
them produce 1.0; only context distinguishes them:

(a) MISSING DATA - pitcher_hand or batter_side empty (line ~339). Genuine data gap.
    Common on TBD/unconfirmed pitchers (pitcher_id None -> pitcher_hand stays "").
    batter_side can also soft-miss to "" on API failure.
(b) total_rate == 0 (line ~377 else). DEAD CODE under normal data flow: splits store
    rate and PA atomically only when pa>=30, so a non-zero rate never pairs with zero
    PA. Genuine zero-HR-season hitters hit the line-351 heuristic guard (1.03/1.06/
    0.96), not this. Do not expect to see this path in practice.
(c) ONE-SIDED PA - split_rate == total_rate because 100% of a hitter's PA are vs one
    handedness. Bayesian shrinkage has no opposite-hand deviation to model, so it
    CORRECTLY outputs 1.0. This is NOT a bug - it is the right answer. (Jared Young,
    2026-06-21: 85 PA all vs RHP, 0 vs LHP -> factor 1.0.)
(d) TRUE NEUTRAL - real split data that genuinely nets to neutral.

Distinguishability BEFORE confidence_score sees it: missing (a) vs the rest IS
distinguishable via batter_side/pitcher_hand fields (both serialized). But
confidence_score() itself only receives the float and is blind to which path produced
it. Any "fix" to platoon neutral-handling that doesn't first classify the path will
mis-treat correct (c)/(d) cases as broken.

## METHOD PRINCIPLE (why this doc exists)
Every confident characterization of these mechanisms was overturned on empirical
inspection. The fixes were only correct because each assumption was verified against
the live engine before code was written. Read-only-before-fix is not bureaucracy -
it is the only reason the confidence patch was correct and the platoon "bug" was
correctly identified as a non-bug.
