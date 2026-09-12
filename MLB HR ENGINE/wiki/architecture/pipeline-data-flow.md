# Pipeline Data Flow

## Summary

`pipeline.py` is the canonical data-assembly entrypoint for the MLB HR Engine. It is shared between `app.py` (Streamlit dashboard) and `main.py` (CLI). Both surfaces consume `pipeline.py` independently — they do not share session state, auth, or caching. The pipeline executes a fixed sequence: fetch external data → build batter/pitcher profiles → compute Poisson probability → price against market → filter → rank → size → output.

## Key Points

### Canonical Pipeline Sequence

1. **Fetch** — MLB Stats API (lineups, rosters), The Odds API (market lines), Baseball Savant/Statcast (batter/pitcher stats), weather, pitch mix
2. **Build Profiles** — per-batter profile assembly: Barrel%, ISO, HR/FB, xSLG, Avg EV, Hard Hit%, Sweet Spot%, Pull%, Launch Angle, xwOBA, SwStr%, K%
3. **Pitcher Vulnerability** — per-pitcher: HR/9, Barrel% Allowed, xFIP, Recent HR/9, Hard Hit% Allowed, GB%
4. **λ Calculation** — combines batter base score × pitcher vulnerability × environmental multipliers
5. **Poisson P(HR≥1)** — `1 − e^(−λ)`
6. **Market Pricing** — model probability vs no-vig implied probability → EV%, Edge%
7. **Filter** — MAIN filters (model-supportive, broader) applied separately from JIG filters
8. **Rank** — by composite score (`EV% × 0.40 + Edge% × 0.35 + Confidence × 0.25`)
9. **Size** — Kelly-derived bet sizing using bankroll from config
10. **Output** — ranked pick list with full metadata

### Key Constraints
- `pipeline.py` is consumed by both `app.py` and `main.py`. Changes affect both surfaces.
- `config.py` is the single source of truth for all thresholds, weights, and baselines used in the pipeline.
- JIG scoring runs through a separate path — pipeline.py does not inject JIG signals into MAIN probability construction.
- Do not reorder pipeline stages without explicit operator authorization.

## Pre-Lineup Player Population & Projection State (verified 2026-09-11)

This section records the pipeline's behavior for a team whose MLB lineup has not yet posted, and the two probability fields (`model_prob`, `model_prob_projected`) that can attach to a player row before and after that posting. It supersedes any prior assumption that unconfirmed teams contribute no rows or that CURRENT is confirmed-lineup-only.

### Unconfirmed player population

For a team with an empty lineup array, the pipeline falls back to that team's full MLB `rosterType=active` non-pitcher pool: exclude entries whose exact MLB `position.type` is `"Pitcher"`, require a player ID and name, then attempt profile construction on each remaining player. This is the **active roster pool** (also **unconfirmed hitter pool**) — not a projected lineup. No verified provider identifies which nine of these hitters will start; do not use language that implies MLB or any other source projected them as starters.

### Eligibility gates

The active-roster fallback does not guarantee every non-pitcher becomes an API row. A candidate is still dropped by the standing profile/data gates:
- Missing player ID or name excludes the player.
- If current-season PA, prior-season PA, and recent-game PA all resolve to zero, the profile is dropped (`pipeline.py:120–121`).
- Profile-construction failure can drop a player.
- Zero HR, missing Statcast, missing handedness, and missing probable pitcher do **not**, on their own, exclude a player.
- Catcher/DH/bench/non-pitcher position players and MLB-labeled Two-Way Players remain eligible.

Describe this population as "the full eligible active non-pitcher roster pool, subject to profile/data gates" — never as an unconditional guarantee that all 26 roster spots become rows.

### Lineup fallback edge case

Any non-empty parsed lineup array suppresses the active-roster fallback for that team. Current source code does not require the array to contain nine valid starters before taking that branch, so a partial or abnormal upstream lineup response is a real population edge case, not just a theoretical one. Treat it as an architectural caveat, not a confirmed production failure, unless direct evidence shows one occurred.

### CURRENT model probability

CURRENT (`model_prob`) is not confirmed-lineup-only. Every successfully emitted row — including an unconfirmed active-roster hitter — receives a CURRENT probability. For an unconfirmed hitter, lineup position is unknown, so the pipeline uses `DEFAULT_PA = 3.8` and applies a separate lineup-uncertainty factor of `×0.82`. All other available game/player/pitcher context is used normally; an unknown pitcher does not by itself block CURRENT from being calculated, since neutral pitcher/platoon context still allows the computation. Do not redefine this behavior — in particular, do not restrict CURRENT to confirmed lineups only. That was proposed and explicitly rejected as the approved architecture.

### PROJECTED model probability (`model_prob_projected`)

`model_prob_projected` does not create players; it operates only on rows the pipeline already built. For an unconfirmed player with a known opposing probable pitcher, the pipeline uses that player's modal batting slot over the preceding seven calendar days (falling back to `DEFAULT_PA = 3.8` if no usable typical slot exists), assumes the player starts, and omits CURRENT's `×0.82` lineup-uncertainty discount. It otherwise runs the same MAIN batter/pitcher/park/weather/platoon/H2H/scaling/calibration chain as CURRENT.

- Confirmed lineup player with a known pitcher: `model_prob_projected == model_prob`.
- Unknown opposing probable pitcher: `model_prob_projected = null`. The row still carries CURRENT `model_prob`.

Population presence and projection availability are separate concerns — a player can be fully present with a valid CURRENT number and no projection at all.

### Lineup confirmation transition

On the next pipeline refresh after a team's lineup becomes non-empty: the roster fallback for that team stops firing, non-starters drop out of the new population, confirmed lineup players (subject to the normal gates) become the population, actual lineup slot replaces the default/typical assumption, CURRENT's `×0.82` discount disappears, probabilities recompute, and PROJECTED collapses to CURRENT wherever the pitcher is known. Tier, rank, Top Targets, JIG contextual population, AEE, and TM all rebuild from the refreshed population.

**Population changes: yes. Probabilities change: yes.**

### Cache / freshness behavior

Each pipeline run rebuilds player rows from the then-current schedule/roster/lineup state, and a same-date stored payload is replaced rather than merged row by row. Lineup publication itself does not directly invalidate an existing slate cache — `/api/slate` treats a same-day cache as valid for up to 12 hours (see the `/api/slate` pure cache-reader contract above), so a valid cache can temporarily lag a lineup that has already posted. The normal cron cadence generally keeps this lag short, but it does not make lineup posting instantaneous, and the stale-fallback path can also surface an older payload if today's is unavailable. `stale: false` reflects cache freshness under the time-based rule; it does not prove the underlying lineup state is current.

### Production evidence (2026-09-11)

CLE @ MIN was unconfirmed at build time. CLE's active roster held 28 players, 14 non-pitchers; the slate carried 14 CLE rows. MIN's active roster held 28 players, 14 non-pitchers; the slate carried 14 MIN rows. No eligible active non-pitcher was missing from either team, no extra rows appeared, 0 of 28 carried a confirmed flag, and all 28 had a CURRENT probability and a projected probability.

Separately, MIA had nine confirmed lineup rows with zero projected probabilities because the opposing pitcher was TBD; all nine still carried CURRENT probabilities. This is the clearest evidence that population presence and projection availability are independent: confirmation controls population, pitcher availability controls PROJECTED.

### State-label vocabulary

- **CONFIRMED** — the player appears in the posted lineup.
- **UNCONFIRMED / ROSTER POOL** — an eligible active-roster hitter surfaced before lineup confirmation.
- **PROJECTION** — `model_prob_projected`, when genuinely available.
- **PROJECTION PENDING / PITCHER TBD** — the row exists but no valid projected probability is available because the required pitcher context is missing.

Never call a roster-pool row a "projected starter" unless a future genuine projected-lineup source establishes that status.

### Morning-workflow architectural decision

The desired full-day morning hitter evaluation does not require expanding the production player-population pipeline; the backend already supplies the broad eligible active-roster pool for unconfirmed teams. The remaining known gap is frontend/state communication around CURRENT vs. PROJECTION, confirmed vs. unconfirmed, and a missing projected probability — see the open frontend defect in `known-gaps.md`. The approved design direction for that gap is frontend/display work only; no probability, player-population, or backend change is authorized by this record.

## Cross-References

- [MAIN Model Doctrine](../doctrine/main-model-doctrine.md)
- [JIG Tactical Doctrine](../doctrine/jig-tactical-doctrine.md)
- [Batter Score Weights](../formulas/batter-score-weights.md)
- [Pitcher Vulnerability](../formulas/pitcher-vulnerability.md)
- [Environmental Multipliers](../formulas/environmental-multipliers.md)
- [Session State Map](session-state-map.md)
- [Cache Ownership Map](cache-ownership-map.md)
- [Known Gaps](../doctrine/known-gaps.md) — open PROJECTION-fallback frontend defect
