# ROLE_CALIBRATION_REPORT.md
Generated: 2026-06-14T11:25 | Analyst: Claude Code (read-only calibration pass)

---

## 1. Config.py Threshold Values Read

### FS_TIER_THRESHOLDS (model_prob)
| Tier   | Floor  |
|--------|--------|
| APEX   | 0.20   |
| ELITE  | 0.16   |
| EDGE   | 0.11   |
| SIGNAL | 0.07   |
| WATCH  | 0.04   |
| COLD   | 0.00   |

### STATCAST_THRESHOLDS (relevant fields, elite_floor)
| Field       | ELITE floor | STRONG | AVG    | WEAK   |
|-------------|-------------|--------|--------|--------|
| barrel_pct  | 14.0%       | 10.0%  | 7.0%   | 4.0%   |
| xslg        | 0.500       | 0.450  | 0.400  | 0.350  |
| pull_air_pct| 20.0%       | 15.0%  | 10.0%  | 6.0%   |
| blast       | 8.0%        | 6.0%   | 4.0%   | 2.0%   |
| max_ev      | 115.0 mph   | 110.0  | 105.0  | 100.0  |
| squp        | 20.0%       | 16.0%  | 12.0%  | 8.0%   |
| fast        | 65.0%       | 58.0%  | 50.0%  | 42.0%  |

### ELITE_REG_TARGET_BARREL_THRESHOLD
- `barrel_rate >= 0.08` (8%) → elite Bayesian ceiling raised
- `ELITE_PLATT_BARREL_THRESHOLD = 0.10` (10%) → lighter Platt compression

### LEAGUE BASELINES (2026 May-25)
- `LEAGUE_AVG_BARREL_RATE = 5.5%`
- `LEAGUE_AVG_HARD_HIT = 39.8%`
- `LEAGUE_AVG_XSLG = 0.400`
- `LEAGUE_AVG_ISO = 0.148`

---

## 2. Row Schema Field Confirmation

### Pipeline → leaderboard_rows field map
| Spec assumes     | Pipeline field   | API row field | Format               |
|------------------|------------------|---------------|----------------------|
| barrel%          | `barrel_pct`     | `barrel`      | String "5.5%"        |
| xSLG             | `xslg`           | `xslg`        | Float 0-1 (e.g. 0.487) |
| HH%              | `hard_hit`       | `hh`          | String "44.8%"       |
| EV               | `exit_velo`      | `ev`          | Float mph (e.g. 90.3) |
| max EV           | `max_ev`         | `maxev`       | Float mph (e.g. 111.1) |
| blast%           | `blast`          | `blast`       | Float % (e.g. 12.2)  |
| pull-air%        | `pull_air_pct`   | `pullair`     | Float % (e.g. 25.5)  |
| tier             | computed from `model_prob` | `tier` | String            |

### Field mismatches vs spec
- None. All spec-assumed columns map cleanly to real pipeline fields.
- `blast`, `squp`, `fast` arrive as raw floats (not strings) — no % suffix.
- `barrel_pct` and `hard_hit` arrive as strings with "%" suffix — must be stripped before numeric comparison.
- `xslg` is on 0–1 scale; spec threshold `.500` is correct as written.

---

## 3. Slate Snapshot

| Item            | Value                        |
|-----------------|------------------------------|
| generated_at    | 2026-06-14T11:23:39          |
| from_cache      | N/A (pipeline run locally)   |
| odds source     | stale cached props (113 lines) — live fetch failed |
| total players   | 317                          |
| with market odds| 57 matched                   |
| qualified picks | 1 (EV+Edge filters apply to rest) |

---

## 4. Role Distribution

### FOUNDATION (barrel% ≥ 9 AND xSLG ≥ .500 AND HH% ≥ 45 AND EV ≥ 90 AND tier APEX/ELITE)
**Count: 13** | null-skips: 0

| Player            | Tier   | Barrel% | xSLG  | HH%   | EV    | Model Prob |
|-------------------|--------|---------|-------|-------|-------|------------|
| James Wood        | APEX   | 13.0%   | 0.620 | 58.1% | 95.6  | 0.2310     |
| Luke Raley        | APEX   | 10.2%   | 0.528 | 48.8% | 90.8  | 0.2006     |
| Dominic Canzone   | APEX   | 11.8%   | 0.548 | 49.6% | 93.2  | 0.2242     |
| Dillon Dingler    | APEX   | 9.0%    | 0.559 | 51.6% | 90.9  | 0.2134     |
| Juan Soto         | APEX   | 11.9%   | 0.627 | 50.0% | 93.0  | 0.2251     |
| Michael Harris II | APEX   | 11.4%   | 0.548 | 52.1% | 92.7  | 0.2041     |
| Matt Olson        | APEX   | 9.7%    | 0.540 | 52.9% | 93.5  | 0.2064     |
| Yordan Alvarez    | ELITE  | 12.3%   | 0.739 | 52.9% | 94.6  | 0.1648     |
| Byron Buxton      | APEX   | 12.6%   | 0.510 | 47.7% | 90.5  | 0.2525     |
| Shohei Ohtani     | APEX   | 10.2%   | 0.575 | 53.8% | 93.8  | 0.2090     |
| Max Muncy         | ELITE  | 10.5%   | 0.550 | 48.1% | 90.5  | 0.1746     |
| Jackson Chourio   | ELITE  | 10.6%   | 0.511 | 49.1% | 92.3  | 0.1788     |
| Nick Kurtz        | ELITE  | 9.2%    | 0.515 | 57.0% | 94.1  | 0.1697     |

### CEILING (max EV ≥ 115 AND (blast% ≥ 15 OR pull-air% ≥ 25) AND barrel% ≥ 9)
**Count: 5** | null-skips: 147

| Player          | Tier   | Max EV | Blast% | Pull-Air% | Barrel% |
|-----------------|--------|--------|--------|-----------|---------|
| James Wood      | APEX   | 116.3  | 16.7%  | 16.7%     | 13.0%   |
| Jac Caglianone  | SIGNAL | 116.1  | 16.6%  | 22.5%     | 9.2%    |
| Yordan Alvarez  | ELITE  | 117.8  | 17.4%  | 28.6%     | 12.3%   |
| Jordan Walker   | EDGE   | 116.6  | 17.0%  | 20.8%     | 9.3%    |
| Nick Kurtz      | ELITE  | 115.9  | 15.3%  | 18.3%     | 9.2%    |

### BOTH (Foundation ∩ Ceiling)
**Count: 3**
- James Wood (APEX)
- Yordan Alvarez (ELITE)
- Nick Kurtz (ELITE)

---

## 5. Null-Skip Counts by Role

| Role       | Null-skips | Root cause |
|------------|------------|------------|
| FOUNDATION | 0          | All 4 criteria fields populated across all 317 players |
| CEILING    | 147        | `blast` null for ~46% of player pool — see verdict below |

---

## 6. Sanity Verdict

### FOUNDATION: BUILDABLE AS DRAFTED
- **13 players** — solid anchor-tier size. Not too exclusive (>0), not too broad (<20).
- The 13 include marquee names (Wood, Soto, Ohtani, Alvarez, Buxton) plus legitimate secondary options (Muncy, Chourio, Kurtz, Olson, Harris).
- Tier gate (APEX/ELITE) correctly filters out EDGE/SIGNAL players with good Statcast profiles but lower model confidence.
- No threshold adjustment needed for FOUNDATION.

### CEILING: TOO SMALL AS DRAFTED — threshold may be too tight
- **5 players** is at the low end for a "ceiling outcome" hunting role.
- More importantly, **147 of 317 players have null `blast` field** — nearly half the pool can't be evaluated.
  - `blast` = "barrel + sweet spot + pull-air combo rate" metric — not populated for all Statcast profiles.
  - This makes the criterion structurally unreliable. If `blast` is null, the `blast >= 15` condition is automatically failed (per no-fabrication doctrine), which may exclude legitimate CEILING candidates who have max_ev ≥ 115 and high pull-air%.
  
**Suggested threshold direction (no change applied):**
- Option A: Make `blast` OR `pull-air%` the swing condition independently (drop the AND-blast requirement, keep OR):
  `max_ev >= 115 AND pull_air_pct >= 25 AND barrel_pct >= 9` as a clean fallback when blast is null.
- Option B: Lower max EV floor slightly (≥112) to include more candidates; current 115 mph is at the "ELITE floor" per STATCAST_THRESHOLDS, which is correct but yields only 5 players.
- Option C: Drop `barrel_pct >= 9` requirement from CEILING (it's already anchored by max_ev and blast/pull-air); barrel is already a FOUNDATION requirement.
- **Recommended first move:** Treat null `blast` as "use pull-air% only" for that player rather than nullifying the entire CEILING check. This addresses the 147-skip problem without changing numeric thresholds.

### Field Reliability Summary
| Field       | Null count | Reliable? |
|-------------|------------|-----------|
| barrel_pct  | 0 / 317    | Yes       |
| xslg        | 0 / 317    | Yes       |
| hard_hit    | 0 / 317    | Yes       |
| exit_velo   | 0 / 317    | Yes       |
| max_ev      | ~0         | Yes       |
| pull_air_pct| ~0         | Yes       |
| blast       | 147 / 317  | UNRELIABLE — 46% null rate |

---

## 7. Git Status
No files modified. Read-only calibration pass. Nothing committed.

---

## Summary

| Role       | Count | Verdict                         |
|------------|-------|---------------------------------|
| FOUNDATION | 13    | Buildable as drafted            |
| CEILING    | 5     | Too small; `blast` null rate (46%) is the root problem |
| BOTH       | 3     | Healthy overlap (Wood, Alvarez, Kurtz) |

**Action required before implementation:** Decide how null `blast` is handled in CEILING logic. Recommend: null `blast` = skip blast sub-criterion only, still evaluate `pull_air_pct >= 25` independently.
