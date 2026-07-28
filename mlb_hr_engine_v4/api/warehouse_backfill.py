"""Backfill binary HR outcomes onto write-separate batter history rows.

Dry-run is the default. Commit mode requires an explicit slate date and writes
only ``batter_stat_history.hr_outcome`` where that column is still NULL.
Outcome evidence comes from the same MLB schedule/boxscore primitives used by
``api.settle_legs`` and is matched exactly by ``(batter_id, game_pk)``.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter, defaultdict
from typing import Callable

from api.settle_legs import _is_real_final, boxscore_for_game, schedule_for_date


def select_unlabeled_rows(slate_date: str, client=None) -> list[dict]:
    """Return only currently-unlabeled warehouse rows for one slate date."""
    if client is None:
        from api.cache import _client

        client = _client()

    result = (
        client.table("batter_stat_history")
        .select("slate_date,run_ts,batter_id,game_pk,hr_outcome")
        .eq("slate_date", slate_date)
        .is_("hr_outcome", "null")
        .execute()
    )
    return result.data or []


def resolve_outcomes(
    rows: list[dict],
    slate_date: str,
    *,
    schedule_fn: Callable[[str], list[dict]] = schedule_for_date,
    boxscore_fn: Callable[[int], dict[int, dict]] = boxscore_for_game,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> list[dict]:
    """Resolve one result per exact batter/game pair without database writes."""
    pair_counts: Counter[tuple[int, int]] = Counter()
    batters_by_game: dict[int, set[int]] = defaultdict(set)
    for row in rows:
        batter_id = int(row["batter_id"])
        game_pk = int(row["game_pk"])
        pair_counts[(batter_id, game_pk)] += 1
        batters_by_game[game_pk].add(batter_id)

    games = {
        int(game["gamePk"]): game
        for game in schedule_fn(slate_date)
        if game.get("gamePk") is not None
    }

    resolved: list[dict] = []
    for game_pk in sorted(batters_by_game):
        game = games.get(game_pk)
        if game is None:
            for batter_id in sorted(batters_by_game[game_pk]):
                resolved.append(_resolution(
                    slate_date, batter_id, game_pk, pair_counts, None,
                    "game_not_on_schedule",
                ))
            continue

        if not _is_real_final(game):
            for batter_id in sorted(batters_by_game[game_pk]):
                resolved.append(_resolution(
                    slate_date, batter_id, game_pk, pair_counts, None,
                    "game_not_final",
                ))
            continue

        try:
            boxscore = boxscore_fn(game_pk)
        except Exception as exc:
            reason = f"boxscore_error:{type(exc).__name__}"
            for batter_id in sorted(batters_by_game[game_pk]):
                resolved.append(_resolution(
                    slate_date, batter_id, game_pk, pair_counts, None, reason,
                ))
            continue

        # A final MLB game always has player records. Treat an empty response as
        # unavailable evidence so a transient API response cannot label all rows 0.
        if not boxscore:
            for batter_id in sorted(batters_by_game[game_pk]):
                resolved.append(_resolution(
                    slate_date, batter_id, game_pk, pair_counts, None,
                    "empty_boxscore",
                ))
            continue

        for batter_id in sorted(batters_by_game[game_pk]):
            home_runs = int(boxscore.get(batter_id, {}).get("hr", 0) or 0)
            resolved.append(_resolution(
                slate_date,
                batter_id,
                game_pk,
                pair_counts,
                1 if home_runs >= 1 else 0,
                "final_boxscore",
            ))
        sleep_fn(0.4)

    return resolved


def _resolution(
    slate_date: str,
    batter_id: int,
    game_pk: int,
    pair_counts: Counter,
    hr_outcome: int | None,
    reason: str,
) -> dict:
    return {
        "slate_date": slate_date,
        "batter_id": batter_id,
        "game_pk": game_pk,
        "hr_outcome": hr_outcome,
        "reason": reason,
        "snapshot_rows": pair_counts[(batter_id, game_pk)],
    }


def commit_outcomes(resolutions: list[dict], client=None) -> int:
    """Write ready labels with exact identity and NULL-only guards."""
    if client is None:
        from api.cache import _client

        client = _client()

    rows_written = 0
    for item in resolutions:
        outcome = item["hr_outcome"]
        if outcome is None:
            continue
        result = (
            client.table("batter_stat_history")
            .update({"hr_outcome": int(outcome)})
            .eq("slate_date", item["slate_date"])
            .eq("batter_id", item["batter_id"])
            .eq("game_pk", item["game_pk"])
            .is_("hr_outcome", "null")
            .execute()
        )
        rows_written += len(result.data or [])
    return rows_written


def summarize(rows: list[dict], resolutions: list[dict]) -> dict[str, int]:
    row_counts = Counter()
    for item in resolutions:
        key = "unresolved" if item["hr_outcome"] is None else str(item["hr_outcome"])
        row_counts[key] += item["snapshot_rows"]
    return {
        "selected_rows": len(rows),
        "unique_batter_games": len(resolutions),
        "label_0_rows": row_counts["0"],
        "label_1_rows": row_counts["1"],
        "unresolved_rows": row_counts["unresolved"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill batter_stat_history.hr_outcome (dry-run by default)"
    )
    parser.add_argument("--date", required=True, metavar="YYYY-MM-DD")
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()

    mode = "COMMIT" if args.commit else "DRY-RUN"
    print(f"[warehouse-backfill] {mode} date={args.date}")
    rows = select_unlabeled_rows(args.date)
    if not rows:
        print("[warehouse-backfill] No NULL outcomes found; rows_written=0")
        return

    resolutions = resolve_outcomes(rows, args.date)
    summary = summarize(rows, resolutions)
    for key, value in summary.items():
        print(f"[warehouse-backfill] {key}: {value}")

    for item in resolutions:
        if item["hr_outcome"] is None:
            print(
                "[warehouse-backfill] deferred "
                f"batter_id={item['batter_id']} game_pk={item['game_pk']} "
                f"reason={item['reason']}"
            )

    if not args.commit:
        print("[warehouse-backfill] DRY-RUN complete; zero writes")
        return

    rows_written = commit_outcomes(resolutions)
    print(f"[warehouse-backfill] rows_written: {rows_written}")
    if rows_written != summary["label_0_rows"] + summary["label_1_rows"]:
        print(
            "[warehouse-backfill] NOTE: fewer rows written than projected; "
            "NULL guards indicate concurrent or prior labeling"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[warehouse-backfill] FAILED: {exc}", file=sys.stderr)
        raise
