---
title: Market Inefficiency - Doctrine
type: tactical_system_doctrine
category: tactical_systems
status: active
created: 2026-05-23
---

# Market Inefficiency — Doctrine

## Core Concept

Market inefficiency doctrine governs when and how the ENGINE exploits pricing gaps between model probability and book-implied probability. The fundamental assumption: books price HR props from park/pitcher/platoon factors (observable) but do not fully incorporate batter Statcast barrel data (partially observable, requires integration). The ENGINE's barrel-first model creates an information premium that is real at barrel ≥ 8% and negligible below barrel ≤ 6%.

## Market Model Assumption

Books' true probability approximation:
```
market_true_prob = 1 - exp(-LEAGUE_AVG_HR_PA × pk_factor × pit_factor × plat_factor × exp_pa)
```

ENGINE adds `power_mult` (Statcast barrel data) then applies calibration. Information gap:
```
edge_pct = cal_prob - market_true_prob
```

Positive edge = Statcast premium over naive market. This is the deployable edge source.

## Barrel ROI Reality (Session 24 Synthetic Analysis)

| Barrel Tier | Edge Breakeven | Synthetic ROI | Deploy? |
|-------------|---------------|--------------|---------|
| < 4% | Negative | −100% | NEVER |
| 4–6% | Negative | −2.7% | NO |
| 6–8% | Near zero | −1.3% | Borderline |
| 8–10% | Positive | +28.0% | YES |
| 10–12% | Strong | +65.3% | YES (priority) |
| 12%+ | Elite | +119.3% | YES (max size) |

**Edge breakeven ≈ barrel ≥ 8%.** Below that, Statcast provides no meaningful information premium over the naive market.

**Critical limitation**: All ROI figures are synthetic simulation (Session 24, n=10,777 batter-games). Validated against real settled data at n ≥ 200. Do NOT adjust thresholds on synthetic data alone.

## Sportsbook Tier Doctrine

Deploy in this priority order when equivalent picks available:

| Book | Vig | Edge Preservation |
|------|-----|------------------|
| Pinnacle | ~3% | Highest |
| Circa | ~4% | High |
| BetOnline.ag | ~5.5% | Good |
| BetRivers | ~7% | Moderate |
| Caesars | ~7.8% | Moderate |
| DraftKings | ~8.8% | Standard |
| FanDuel | ~9.5% | Lower |
| Fanatics | ~11% | Lowest |

Sharp book floor: consider EV ≥ 1.5% at Pinnacle/Circa — their lower vig screens bad edges natively. Retail books require EV ≥ 3.0% minimum.

## CLV Doctrine (Walters Principle)

CLV (Closing Line Value) is the sharp betting metric. A positive CLV indicates the model consistently gets better prices than the efficient closing line. CLV targets:
- `SHARP`: avg CLV > +1.0 pp
- `SLIGHTLY SHARP`: avg CLV > 0 pp
- `NEUTRAL`: avg CLV > −1.0 pp
- `SOFT`: avg CLV < −1.0 pp

**Walters doctrine**: bet early (at opening line) when model edge is expected to compress by close. This applies when:
1. Model identifies barrel-based edge that books will reprice as public money moves
2. Favorable weather identified before books update lines
3. Lineup confirmation reveals favorable spot books haven't repriced yet

## Deployment Timing Doctrine

1. **Opening line**: deploy when model edge is highest (before sharp money compresses)
2. **Pre-game (-30 min)**: capture closing lines for CLV computation via `capture_closing_lines.py`
3. **Stale line window**: if book hasn't updated for confirmed lineup/weather → secondary deployment opportunity
4. **Never chase**: do not deploy into a line that has already moved against the model

## Edge Threshold Analysis (Session 24)

| Filter | Picks | ROI | Delta |
|--------|-------|-----|-------|
| EV≥3%, Edge≥2% (current) | 2,136 | +37.1% (synthetic) | baseline |
| EV≥4%, Edge≥2.5% (tighter) | 1,882 | +42.3% (synthetic) | +5.2pp, -12% picks |
| Edge≥5% (tightest) | 906 | +51.8% (synthetic) | barrel≥10% dominated |

**Pending**: validate with real settled data at n ≥ 200 before tightening thresholds.

## False Edge Archetypes (Do Not Deploy)

- barrel 4–6%, average power, any park: ROI −2% to −30%
- barrel 8–10%, average power, any park: ROI −56% (synthetic) — small sample, high variance
- Mild platoon advantage with average barrel: market prices platoon correctly; model offers no premium

## Doctrine Rules

**Rule 1 — Barrel breakeven governs deployment.** EV% and Edge% are necessary but not sufficient without barrel ≥ 8%. Positive EV at barrel < 6% is a model artifact, not a market edge.

**Rule 2 — n < 200 real picks: no threshold changes.** Current real settled data (n=324, ROI=−30.3%) is too small for threshold adjustment. Synthetic ROI and real ROI divergence is expected at small n. Wait for n ≥ 500.

**Rule 3 — Sharp books first.** When two picks have equivalent model edge, prefer the one on a lower-vig book. Vig erosion is real and cumulative.

**Rule 4 — CLV is the long-run validation metric.** Short-term ROI fluctuates on HR hit/miss variance. CLV measures whether the model is getting good prices. Positive CLV with negative short-term ROI = correct behavior.

**Rule 5 — Do not optimize for ROI on small n.** Rule from Session 25. Do not adjust MIN_EV_PCT, MIN_EDGE_PCT, or barrel thresholds based on n < 200 real picks.

## Related Doctrine Links

- [[Barrel_Quality/doctrine]] — barrel rate determines whether EV% is real or artifact
- [[Confidence_Tiering/doctrine]] — EV/Edge danger layers feed tier assignment
- [[HR_Threat_Escalation/doctrine]] — EV layer is 5th primary danger signal
- [[Environmental_Leverage/doctrine]] — weather not priced by books → structural edge source
