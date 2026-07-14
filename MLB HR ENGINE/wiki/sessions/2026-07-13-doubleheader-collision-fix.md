# Doubleheader Collision Fix — 2026-07-13

Status: SHIPPED / DEPLOYED / VALIDATED

## Incident

On a doubleheader slate, the same player could appear once in each game. Several payload and UI lookups keyed those sibling rows only by player identity, so the games collided. A row could inherit the other game's model tier, `jigScore`, Arsenal Edge score (AEE), True Matchup score (TM), odds, or game card metadata such as park, start time, and weather.

The identity required for slate-row joins is therefore `(player, game_pk)`, not player alone.

## Root plumbing

`pipeline.py` already stamped `game_pk` on the player profile, but `api/main.py` dropped it when constructing the slate row. Commit `2eefdc0` made `game_pk` additive on both row and game-card payloads. JIG rows receive the field because they are shallow copies of MAIN rows via `copy.copy`.

This additive pass-through enabled every collision site to distinguish the two scheduled games without changing player-id semantics.

## Collision sites fixed

| Site | Commit | Failure | Shipped correction |
|---|---|---|---|
| D | `1546abd` | `_ranked_map` keyed by player name assigned the wrong game's tier. | Re-keyed on `(player_name, game_pk)`. |
| B + C | `21b15bf` | `players_by_id` and `_aee_map` crossed sibling profiles, corrupting `jigScore`, AEE, and TM. | Re-keyed on `(player_id, game_pk)` while preserving the `is None` fallback. |
| E | `6357cd8` | `_match_odds` pooled same-name props across both events, allowing the wrong odds, edge, and EV. | Added game-aware event-pool selection using teams and commence time, mirroring `_attach_fd_links` in `pipeline.py`. |
| A | `6b6d07f` | Matchup-only `gameId` collapsed both games into one slate card. | Added a `game_pk` suffix only when the same matchup slug collides. Non-doubleheader slugs remain unchanged. |
| React row key | `96ec142`, `1c7d3dc` | Repeated player ids created duplicate React keys across sibling rows. | Six frontend row-list files now use composite React `key` values based on `id` and `game_pk`. |

All five sites shipped and were deployed.

## Load-bearing lessons

### Site E is not display-only

Matched odds flow into `edge_pct`, `ev_pct`, confidence, `bet_dollars`, pick qualification, and the picks table. Those values become settlement and CLV inputs. A wrong game-aware odds fix can therefore silently change which opportunities are bet; it is not cosmetic plumbing.

Non-doubleheader invariance was proven empirically before shipment: 173 names were compared across all 10 pricing fields, and old versus new output was identical.

### Composite row `id` is prohibited

The row `id` is the raw MLB `player_id`. The B/C lookups, slip payload into ticket storage, and `/api/pitcher-detail` depend on that meaning. Replacing it with a player/game composite would ripple into the tickets table and other consumers.

Doubleheader uniqueness belongs in lookup tuples and React `key` props. The shipped frontend fix changed React keys only; row `id` semantics remained untouched.

## Validation and review gates

Two Fable audits cleared the fix set:

- Regression trace: no stored-ticket or settlement drift was introduced. Settlement resolves legs by date rather than game, so doubleheader re-keying cannot select a different game during grading. Calibration reads backtest CSV data and is unaffected.
- A/E clearance: review identified that Site E affects bet selection and blocked a proposed composite row `id` before either mistake could ship.

The final implementation preserved MAIN/JIG separation, model formulas, JIG scoring, thresholds, ticket-role logic, and player-id storage semantics.
