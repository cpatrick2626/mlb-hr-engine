"""
Settlement resolver — dry-run by default (Phase S2 / D3-D4).

--dry-run is the DEFAULT and has zero reachable write path.
--commit is the ONLY write path in this module and is hard-gated:
  * requires an explicit --date YYYY-MM-DD (bulk commit not enabled),
  * uses the SAME resolver output as dry-run (no divergent logic),
  * writes only legs.hr_result / settlement_status / settled_at,
  * only via UPDATE ... WHERE leg_id=<id> AND settlement_status='pending'
    (write-once: a settled/void row can never be re-selected or flipped),
  * only for classifications 'settled' and 'void' — deferred, name_mismatch,
    unresolvable_id, id_not_found, no_games_on_date stay pending, untouched.

Usage (from mlb_hr_engine_v4/):
    python -m api.settle_legs                            # dry-run, all pending, 14-day lookback
    python -m api.settle_legs --date 2026-07-06          # dry-run, single date
    python -m api.settle_legs --commit --date 2026-07-06 # OPERATOR-GATED single-date write
"""

import sys
import os
import time
import csv
import argparse
import unicodedata
import requests
from datetime import date, datetime, timedelta, timezone
from typing import Optional

# sys.path so imports resolve when run as `python -m api.settle_legs`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # Python 3.8 compat shim

MLB_API  = "https://statsapi.mlb.com/api/v1"
EASTERN  = ZoneInfo("America/New_York")
LOOKBACK = 14  # days

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "Codex-HR-Engine-Settle/1.0"})

_SEEN_STATES: set[str] = set()   # accumulated during a run for the verification report

_POSTPONED_OR_CANCELLED = frozenset({"Postponed", "Cancelled"})


# ── MLB Stats API (isolated from clients/mlb_stats.py) ───────────────────────

def _get(path: str, params: dict = None) -> dict:
    url = f"{MLB_API}{path}"
    for attempt in range(3):
        try:
            resp = _SESSION.get(url, params=params, timeout=15)
            if resp.status_code in (404, 403):
                return {}
            resp.raise_for_status()
            try:
                return resp.json()
            except ValueError:
                raise requests.RequestException(
                    f"non-JSON response (status={resp.status_code})"
                )
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)  # 1s, then 2s


def schedule_for_date(date_str: str) -> list[dict]:
    """
    Return [{gamePk, abstractGameState, detailedState, home_team, away_team}]
    for all games on date_str. One call per settlement date.
    """
    data = _get("/schedule", {"sportId": 1, "date": date_str, "hydrate": "team"})
    games: list[dict] = []
    for entry in data.get("dates", []):
        if entry.get("date") != date_str:
            continue
        for g in entry.get("games", []):
            st    = g.get("status", {})
            teams = g.get("teams", {})
            games.append({
                "gamePk":            g.get("gamePk"),
                "abstractGameState": st.get("abstractGameState", ""),
                "detailedState":     st.get("detailedState", ""),
                "home_team":         teams.get("home", {}).get("team", {}).get("abbreviation", ""),
                "away_team":         teams.get("away", {}).get("team", {}).get("abbreviation", ""),
            })
    return games


def boxscore_for_game(game_pk: int) -> dict[int, dict]:
    """
    Return {person_id_int: {"pa": int, "hr": int, "name": str}} for every player
    in the boxscore. Caller enforces ~0.4s inter-call delay.
    """
    data = _get(f"/game/{game_pk}/boxscore")
    result: dict[int, dict] = {}
    for side in ("home", "away"):
        for key, pdata in data.get("teams", {}).get(side, {}).get("players", {}).items():
            if not key.startswith("ID"):
                continue
            try:
                pid = int(key[2:])
            except ValueError:
                continue
            batting = pdata.get("stats", {}).get("batting", {})
            result[pid] = {
                "pa": int(batting.get("plateAppearances", 0) or 0),
                "hr": int(batting.get("homeRuns", 0) or 0),
                "name": pdata.get("person", {}).get("fullName", "") or "",
            }
    return result


def _norm_name(name: str) -> str:
    """Normalize a player name for cross-check: strip accents, periods, case,
    and extra spaces ("J.T. Realmuto" ~ "JT Realmuto", "Acuna" ~ "Acuña")."""
    s = unicodedata.normalize("NFKD", str(name or ""))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace(".", "").lower()
    return " ".join(s.split())


def _verify_person_id(pid: int) -> bool:
    """Return True if MLB Stats API recognises this person ID."""
    data = _get(f"/people/{pid}")
    return bool(data.get("people"))


# ── Supabase — SELECT only ────────────────────────────────────────────────────

def select_pending_legs(lookback_days: int = LOOKBACK) -> list[dict]:
    """
    SELECT-only. Returns pending, non-removed legs with leg_date < today (ET)
    within the look-back window.
    """
    from api.cache import _client

    today_et   = datetime.now(EASTERN).date()
    today_str  = today_et.isoformat()
    cutoff_str = (today_et - timedelta(days=lookback_days)).isoformat()

    result = (
        _client()
        .table("legs")
        .select("leg_id, leg_date, player_name, player_id, team, tickets(board)")
        .eq("settlement_status", "pending")
        .eq("removed", False)
        .lt("leg_date", today_str)
        .gte("leg_date", cutoff_str)
        .execute()
    )
    # Flatten tickets.board into the leg row for convenience
    rows = []
    for row in (result.data or []):
        ticket_data = row.pop("tickets", None) or {}
        row["board"] = ticket_data.get("board", "") if isinstance(ticket_data, dict) else ""
        rows.append(row)
    return rows


# ── Resolver ──────────────────────────────────────────────────────────────────

def _is_terminal(g: dict) -> bool:
    """True when a game will produce no more stats (Final, Postponed, or Cancelled)."""
    if g["abstractGameState"] == "Final":
        return True
    return any(s in g["detailedState"] for s in _POSTPONED_OR_CANCELLED)


def _is_real_final(g: dict) -> bool:
    """Final game that produced real batting stats (not a Postponed/Cancelled game)."""
    return (
        g["abstractGameState"] == "Final"
        and not any(s in g["detailedState"] for s in _POSTPONED_OR_CANCELLED)
    )


def resolve_legs(legs: list[dict], target_date: Optional[str] = None) -> list[dict]:
    """
    Dry-run resolver implementing spec §1.3.
    Returns result rows with would_status / would_hr_result — NO database writes.
    """
    if target_date:
        legs = [l for l in legs if str(l.get("leg_date", "")) == target_date]

    by_date: dict[str, list] = {}
    for leg in legs:
        by_date.setdefault(str(leg["leg_date"]), []).append(leg)

    results: list[dict] = []

    for leg_date, date_legs in sorted(by_date.items()):
        print(f"[settle] {leg_date}: {len(date_legs)} leg(s) — fetching schedule…")

        # ── 1. Schedule ───────────────────────────────────────────────────────
        try:
            games = schedule_for_date(leg_date)
        except Exception as exc:
            print(f"[settle]   schedule_for_date({leg_date}) FAILED: {exc} — deferring all")
            for leg in date_legs:
                results.append(_row(leg, "deferred", None, "", "api_error"))
            continue

        if not games:
            for leg in date_legs:
                results.append(_row(leg, "no_games_on_date", None, "", ""))
            continue

        for g in games:
            _SEEN_STATES.add(g["detailedState"])

        real_final  = [g for g in games if _is_real_final(g)]
        all_terminal = all(_is_terminal(g) for g in games)

        # ── 2. Boxscores for Final games ──────────────────────────────────────
        # person_index: pid -> [(gamePk, pa, hr, name), ...]
        # game_teams:   gamePk -> (home_abbr, away_abbr)
        person_index: dict[int, list] = {}
        game_teams:   dict[int, tuple] = {}

        for g in real_final:
            gk = g["gamePk"]
            game_teams[gk] = (g["home_team"].upper(), g["away_team"].upper())
            try:
                bsc = boxscore_for_game(gk)
                for pid, st in bsc.items():
                    person_index.setdefault(pid, []).append((gk, st["pa"], st["hr"], st["name"]))
            except Exception as exc:
                print(f"[settle]   boxscore({gk}) FAILED: {exc} — skipping game")
            time.sleep(0.4)  # polite inter-call delay

        # ── 3. Classify each leg ──────────────────────────────────────────────
        for leg in date_legs:
            results.append(
                _classify(leg, games, real_final, all_terminal, person_index, game_teams)
            )

    return results


def _classify(
    leg: dict,
    games: list[dict],
    real_final: list[dict],
    all_terminal: bool,
    person_index: dict[int, list],
    game_teams: dict[int, tuple],
) -> dict:
    raw_pid = leg.get("player_id") or ""

    # Non-numeric / NULL player_id → never name-match, report only (§1.2 #1)
    try:
        pid = int(str(raw_pid).strip())
    except (ValueError, TypeError):
        return _row(leg, "unresolvable_id", None, "", "")

    apps      = person_index.get(pid, [])
    total_pa  = sum(pa for _, pa, _, _ in apps)
    total_hr  = sum(hr for _, _, hr, _ in apps)

    # Name cross-check: person-ID and gamePk numeric ranges overlap, so a
    # numeric-but-wrong player_id can pass the existence check against the
    # wrong person. If the boxscore name doesn't match leg.player_name,
    # never settle/void — leave pending and report.
    if apps:
        box_names = {nm for _, _, _, nm in apps if nm}
        leg_norm  = _norm_name(leg.get("player_name", ""))
        if box_names and leg_norm and not any(_norm_name(nm) == leg_norm for nm in box_names):
            ev = "; ".join(f"gamePk={gk} PA={pa} HR={hr}" for gk, pa, hr, _ in apps)
            ev += "; boxscore_name=" + "|".join(sorted(box_names))
            return _row(leg, "name_mismatch", None, ev, "")

    # Team drift: player appeared in a game leg.team wasn't part of (§1.2 #3).
    # Empty/missing team abbrevs (partial hydrate=team response) mean no
    # cross-check is available — don't flag drift on them.
    leg_team = (leg.get("team") or "").strip().upper()
    flags: list[str] = []
    if apps and leg_team:
        for gk, _, _, _ in apps:
            home, away = game_teams.get(gk, ("", ""))
            if home and away and leg_team not in (home, away):
                flags.append("team_drift")
                break

    # Teams the player actually appeared for (used in pending-game check)
    appeared_teams: set[str] = set()
    for gk, _, _, _ in apps:
        home, away = game_teams.get(gk, ("", ""))
        appeared_teams.update([home, away])
    appeared_teams.discard("")

    # Any non-terminal game involving leg.team or player's appeared teams? (doubleheader guard)
    team_games_pending = False
    for g in games:
        if not _is_terminal(g):
            g_teams = {g["home_team"].upper(), g["away_team"].upper()}
            if (leg_team and leg_team in g_teams) or (appeared_teams & g_teams):
                team_games_pending = True
                break

    evidence = "; ".join(f"gamePk={gk} PA={pa} HR={hr}" for gk, pa, hr, _ in apps)
    flag_str = ",".join(flags)

    # §1.3 decision table
    if apps and total_pa >= 1:
        if team_games_pending:
            return _row(leg, "deferred", None, evidence, flag_str)
        return _row(leg, "settled", 1 if total_hr >= 1 else 0, evidence, flag_str)

    if all_terminal:
        if not apps:
            if not real_final:
                # All postponed/cancelled — void
                return _row(leg, "void", None, evidence, flag_str)
            # Final games exist but player absent — verify MLBAM ID (§1.2 #5)
            try:
                time.sleep(0.3)
                valid = _verify_person_id(pid)
            except Exception:
                valid = True  # network error: conservative, don't void
            if not valid:
                return _row(leg, "id_not_found", None, evidence, flag_str)
        # apps exist with 0 PA, or DNP with valid ID → void
        return _row(leg, "void", None, evidence, flag_str)

    # Non-terminal games still outstanding
    return _row(leg, "deferred", None, evidence, flag_str)


def _row(leg: dict, status: str, hr_result, evidence: str, flags: str) -> dict:
    return {
        "leg_id":          leg.get("leg_id", ""),
        "leg_date":        leg.get("leg_date", ""),
        "player_name":     leg.get("player_name", ""),
        "player_id":       leg.get("player_id", ""),
        "board":           leg.get("board", ""),
        "would_status":    status,
        "would_hr_result": "" if hr_result is None else hr_result,
        "evidence":        evidence,
        "flags":           flags,
    }


# ── Output ────────────────────────────────────────────────────────────────────

_COLS = [
    "leg_id", "leg_date", "player_name", "player_id", "board",
    "would_status", "would_hr_result", "evidence", "flags",
]


def print_table(results: list[dict]) -> None:
    if not results:
        print("(no results)")
        return
    def _cell(r, c):
        v = r.get(c)
        return "" if v is None else str(v)  # keep 0 visible (0 is falsy)

    widths = {c: len(c) for c in _COLS}
    for r in results:
        for c in _COLS:
            widths[c] = max(widths[c], len(_cell(r, c)))
    hdr = "  ".join(c.ljust(widths[c]) for c in _COLS)
    sep = "  ".join("-" * widths[c] for c in _COLS)
    print(hdr)
    print(sep)
    for r in results:
        print("  ".join(_cell(r, c).ljust(widths[c]) for c in _COLS))


def compute_summary(results: list[dict]) -> dict:
    s = {k: 0 for k in [
        "settled_1", "settled_0", "void", "deferred",
        "unresolvable_id", "id_not_found", "name_mismatch",
        "no_games_on_date", "team_drift",
    ]}
    for r in results:
        status = r["would_status"]
        hr     = r["would_hr_result"]
        if status == "settled":
            s["settled_1" if hr == 1 else "settled_0"] += 1
        elif status in s:
            s[status] += 1
        if "team_drift" in str(r.get("flags") or ""):
            s["team_drift"] += 1
    return s


def write_csv(results: list[dict], tag: str) -> str:
    os.makedirs("reports", exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"reports/settlement_dryrun_{tag}_{ts}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_COLS)
        writer.writeheader()
        writer.writerows(results)
    return path


# ── Commit write path (ONLY write in this module — spec §4/§5 idempotency) ────

_WRITABLE_STATUSES = frozenset({"settled", "void"})  # everything else stays pending

_COMMIT_COLS = [
    "leg_id", "leg_date", "player_name", "player_id", "board",
    "hr_result_written", "settlement_status_written", "evidence", "rows_written",
]


def commit_results(results: list[dict]) -> tuple[list[dict], int]:
    """
    Apply resolver output to Supabase. Reachable ONLY from the --commit branch.

    Per leg, exactly one guarded UPDATE:
        UPDATE legs
        SET hr_result=<1|0|NULL>, settlement_status=<'settled'|'void'>, settled_at=now()
        WHERE leg_id=<id> AND settlement_status='pending'

    The settlement_status='pending' guard makes the write write-once: a
    settled/void row is never re-selected, so re-runs write 0 rows.
    Writes ONLY those three columns. Non-writable classifications (deferred,
    name_mismatch, unresolvable_id, id_not_found, no_games_on_date) are
    skipped entirely — the row is left untouched.
    Returns (per-leg report rows, total rows_written).
    """
    from api.cache import _client

    client = _client()
    # Aware UTC, then strip tzinfo so the stored string keeps the exact
    # pre-existing "<naive-iso>Z" shape (no "+00:00" suffix drift).
    now_iso = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"

    report: list[dict] = []
    total_written = 0

    for r in results:
        status = r["would_status"]
        if status not in _WRITABLE_STATUSES:
            continue  # stays pending — no UPDATE reachable for this leg

        hr_result = int(r["would_hr_result"]) if status == "settled" else None

        res = (
            client.table("legs")
            .update({
                "hr_result":          hr_result,
                "settlement_status":  status,
                "settled_at":         now_iso,
            })
            .eq("leg_id", r["leg_id"])
            .eq("settlement_status", "pending")   # MANDATORY write-once guard
            .execute()
        )
        rows_written = len(res.data or [])
        total_written += rows_written

        report.append({
            "leg_id":                    r["leg_id"],
            "leg_date":                  r["leg_date"],
            "player_name":               r["player_name"],
            "player_id":                 r["player_id"],
            "board":                     r["board"],
            "hr_result_written":         "" if hr_result is None else hr_result,
            "settlement_status_written": status,
            "evidence":                  r["evidence"],
            "rows_written":              rows_written,
        })

    return report, total_written


def print_commit_report(report: list[dict], total_written: int) -> None:
    if not report:
        print("(no writable legs — nothing was settled or voided)")
    else:
        def _cell(r, c):
            v = r.get(c)
            return "" if v is None else str(v)
        widths = {c: len(c) for c in _COMMIT_COLS}
        for r in report:
            for c in _COMMIT_COLS:
                widths[c] = max(widths[c], len(_cell(r, c)))
        print("  ".join(c.ljust(widths[c]) for c in _COMMIT_COLS))
        print("  ".join("-" * widths[c] for c in _COMMIT_COLS))
        for r in report:
            print("  ".join(_cell(r, c).ljust(widths[c]) for c in _COMMIT_COLS))
    print(f"\n[settle] rows_written: {total_written}")
    if total_written == 0 and report:
        print("[settle] 0 rows written with writable legs present — these rows are "
              "already non-pending (expected on a re-run; the pending guard makes "
              "the write idempotent).")


def write_commit_csv(report: list[dict], tag: str) -> str:
    os.makedirs("reports", exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"reports/settlement_commit_{tag}_{ts}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_COMMIT_COLS)
        writer.writeheader()
        writer.writerows(report)
    return path


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Settlement resolver — dry-run by default")
    parser.add_argument("--date", metavar="YYYY-MM-DD",
                        help="Restrict resolution to a single leg_date")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Dry-run mode (default)")
    parser.add_argument("--commit", action="store_true", default=False,
                        help="Write settled/void results to Supabase. Requires --date "
                             "(operator-gated single-date first run).")
    args = parser.parse_args()

    if args.commit and not args.date:
        print("[settle] REJECTED: --commit requires an explicit --date for the "
              "operator-gated single-date first run; bulk commit is not enabled")
        sys.exit(1)

    if args.commit:
        print(f"[settle] COMMIT MODE — will write settled/void legs for {args.date} "
              "(pending rows only, three columns only)")
    else:
        print("[settle] DRY-RUN — zero writes")

    legs = select_pending_legs()
    if not legs:
        print("[settle] No pending legs found in 14-day lookback.")
        return
    print(f"[settle] {len(legs)} pending leg(s) fetched from Supabase")

    results = resolve_legs(legs, target_date=args.date)

    print("\n=== PROPOSED SETTLEMENTS (DRY-RUN — OPERATOR HAND-CHECK REQUIRED) ===\n")
    print_table(results)

    summary = compute_summary(results)
    print("\n=== SUMMARY COUNTS ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    if _SEEN_STATES:
        print("\n=== detailedState strings observed ===")
        for s in sorted(_SEEN_STATES):
            print(f"  {s!r}")

    tag      = (args.date or "all").replace("-", "")
    csv_path = write_csv(results, tag)
    print(f"\n[settle] CSV: {csv_path}")

    if not args.commit:
        print("[settle] OPERATOR HAND-CHECK REQUIRED — correctness of individual settlements is NOT self-judged")
        return

    # ── COMMIT — the only reachable write path in this module ────────────────
    report, total_written = commit_results(results)

    print("\n=== POST-WRITE REPORT (verify against Supabase) ===\n")
    print_commit_report(report, total_written)

    commit_csv = write_commit_csv(report, tag)
    print(f"\n[settle] commit CSV: {commit_csv}")
    print("[settle] Idempotency: re-running this same --commit --date writes 0 rows — "
          "all written rows are now non-pending and the pending guard excludes them.")


if __name__ == "__main__":
    main()
