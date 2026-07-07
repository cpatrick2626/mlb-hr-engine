"""
!! DO NOT RE-RUN — RETIRED ONE-OFF !!

This script belongs to the pre-generated_at-derivation era (through commit
7088c5d). Since add_leg began deriving leg_date/tickets.date from
engine_generated_at (ET), this script's core heuristic — ET-of-created_at
!= leg_date implies a mislabeled leg — is NO LONGER VALID: a legitimate
after-midnight capture of a stale board now correctly has leg_date = the
board's slate date while created_at falls on the next day. Re-running
--commit would FALSELY "fix" correct legs. Kept only as ops record of the
original backfill; do not run against post-fix data.

One-off leg_date correction — dry-run by default.

Fixes the 23 legs mislabeled by the UTC off-by-one capture bug (api/cache.py
used UTC date.today() for tickets opened after 8pm ET; bug itself already
fixed in commit 41bda4b — this script only corrects the EXISTING bad rows).

--dry-run is the DEFAULT and has zero reachable write path.
--commit is the ONLY write path in this module and is hard-gated:
  * requires an explicit --batch "WRONG->RIGHT" (one of the two known
    batches below; bulk all-at-once commit is not enabled),
  * uses the SAME identification output as dry-run (no divergent logic),
  * writes ONLY legs.leg_date,
  * only via UPDATE ... WHERE leg_id=<id> AND settlement_status='pending'
    AND leg_date=<current_wrong_date>
    (write-once: a settled row or an already-corrected row can never be
    re-selected or flipped),
  * refuses to run if the identified batch count differs from the
    investigation-confirmed count (15 or 8).

Known batches (from the read-only investigation):
  2026-06-26->2026-06-25   15 legs (tickets opened 8:20-9:39pm ET on 6/25)
  2026-07-07->2026-07-06    8 legs (tickets opened 8:28-8:30pm ET on 7/6)

Out of scope, never touched: settled rows (incl. the 32 committed 7/6 legs),
removed rows, and the 9 legacy NULL-leg_date legs.

Usage (from mlb_hr_engine_v4/):
    python -m api.fix_leg_dates                                        # dry-run
    python -m api.fix_leg_dates --commit --batch "2026-07-07->2026-07-06"  # OPERATOR-GATED
"""

import sys
import os
import time
import csv
import argparse
import unicodedata
import requests
from datetime import datetime

# sys.path so imports resolve when run as `python -m api.fix_leg_dates`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # Python 3.8 compat shim

MLB_API = "https://statsapi.mlb.com/api/v1"
EASTERN = ZoneInfo("America/New_York")

# Investigation-confirmed batches: "wrong->right" -> expected leg count.
# --commit refuses any batch not in this map or whose identified count differs.
# NOTE: the investigation counted 8 legs in the 7/7 batch, but leg
# 3a57a54e (Casey Schmitt / Kevin Gausman, ticket 2026-07-07T00:28 UTC)
# is removed=true — out of scope by the removed=false filter (removed legs
# never settle, so its wrong date is inert). Actionable set: 22 = 15 + 7.
EXPECTED_BATCHES = {
    "2026-06-26->2026-06-25": 15,
    "2026-07-07->2026-07-06": 7,
}
EXPECTED_TOTAL = sum(EXPECTED_BATCHES.values())  # 22 actionable (23 incl. removed leg)

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "Codex-HR-Engine-FixLegDates/1.0"})


# ── MLB Stats API (pitcher anchor — verification only) ───────────────────────

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
            time.sleep(2 ** attempt)


def _norm_name(name: str) -> str:
    """Normalize a name for cross-check: strip accents, periods, case, spaces."""
    s = unicodedata.normalize("NFKD", str(name or ""))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace(".", "").lower()
    return " ".join(s.split())


def starters_for_date(date_str: str) -> set[str]:
    """
    Normalized full names of every probable/starting pitcher on date_str's
    schedule. One API call per distinct proposed date.
    """
    data = _get("/schedule", {"sportId": 1, "date": date_str,
                              "hydrate": "probablePitcher"})
    names: set[str] = set()
    for entry in data.get("dates", []):
        if entry.get("date") != date_str:
            continue
        for g in entry.get("games", []):
            for side in ("home", "away"):
                pp = g.get("teams", {}).get(side, {}).get("probablePitcher", {})
                nm = pp.get("fullName", "")
                if nm:
                    names.add(_norm_name(nm))
    return names


# ── Supabase — SELECT only ────────────────────────────────────────────────────

def identify_mislabeled_legs() -> list[dict]:
    """
    SELECT-only. Finds pending, non-removed, non-NULL-dated legs whose leg_date
    differs from the ET date of the parent ticket's created_at. The corrected
    date IS that ET date.
    """
    from api.cache import _client

    result = (
        _client()
        .table("legs")
        .select("leg_id, leg_date, player_name, pitcher, tickets(created_at)")
        .eq("settlement_status", "pending")
        .eq("removed", False)
        .not_.is_("leg_date", "null")   # 9 legacy NULL-date legs are out of scope
        .execute()
    )

    proposals: list[dict] = []
    for row in (result.data or []):
        ticket = row.get("tickets") or {}
        created_raw = ticket.get("created_at") if isinstance(ticket, dict) else None
        if not created_raw:
            continue
        created_utc = datetime.fromisoformat(str(created_raw).replace("Z", "+00:00"))
        created_et  = created_utc.astimezone(EASTERN)
        corrected   = created_et.date().isoformat()
        current     = str(row["leg_date"])
        if current == corrected:
            continue
        proposals.append({
            "leg_id":               row["leg_id"],
            "player_name":          row.get("player_name", ""),
            "pitcher":              row.get("pitcher", "") or "",
            "current_leg_date":     current,
            "proposed_leg_date":    corrected,
            "ticket_created_at_ET": created_et.strftime("%Y-%m-%d %H:%M:%S %Z"),
        })
    return proposals


# ── Pitcher anchor (report evidence — never gates the write selection) ───────

def anchor_check(proposals: list[dict]) -> None:
    """Annotate each proposal with pitcher_started_proposed_date yes/no.
    A 'no' is a red flag for the operator to inspect, not an auto-skip."""
    cache: dict[str, set[str]] = {}
    for p in proposals:
        d = p["proposed_leg_date"]
        if d not in cache:
            try:
                cache[d] = starters_for_date(d)
            except Exception as exc:
                print(f"[fix-dates]   starters_for_date({d}) FAILED: {exc}")
                cache[d] = set()
            time.sleep(0.4)
        pitcher_norm = _norm_name(p["pitcher"])
        p["pitcher_started_proposed_date"] = (
            "yes" if pitcher_norm and pitcher_norm in cache[d] else "no"
        )


# ── Output ────────────────────────────────────────────────────────────────────

_COLS = [
    "leg_id", "player_name", "pitcher", "current_leg_date",
    "proposed_leg_date", "pitcher_started_proposed_date", "ticket_created_at_ET",
]


def print_table(rows: list[dict]) -> None:
    if not rows:
        print("(no mislabeled legs found)")
        return
    def _cell(r, c):
        v = r.get(c)
        return "" if v is None else str(v)
    widths = {c: len(c) for c in _COLS}
    for r in rows:
        for c in _COLS:
            widths[c] = max(widths[c], len(_cell(r, c)))
    print("  ".join(c.ljust(widths[c]) for c in _COLS))
    print("  ".join("-" * widths[c] for c in _COLS))
    for r in rows:
        print("  ".join(_cell(r, c).ljust(widths[c]) for c in _COLS))


def batch_key(p: dict) -> str:
    return f"{p['current_leg_date']}->{p['proposed_leg_date']}"


def print_summary(proposals: list[dict]) -> None:
    counts: dict[str, int] = {}
    for p in proposals:
        counts[batch_key(p)] = counts.get(batch_key(p), 0) + 1
    print("\n=== BATCH SUMMARY ===")
    for k in sorted(counts):
        expected = EXPECTED_BATCHES.get(k)
        note = (f"(expected {expected})" if expected is not None
                else "(NOT an investigation-confirmed batch — inspect!)")
        print(f"  {k}: {counts[k]} leg(s) {note}")
    print(f"  TOTAL: {len(proposals)} (investigation confirmed {EXPECTED_TOTAL})")
    if len(proposals) != EXPECTED_TOTAL:
        print("  *** COUNT MISMATCH vs investigation — STOP and reconcile before "
              "any --commit (expected only if a batch was already corrected). ***")
    mismatches = [p for p in proposals
                  if p.get("pitcher_started_proposed_date") != "yes"]
    if mismatches:
        print(f"  *** {len(mismatches)} pitcher-anchor mismatch(es) — red flag, "
              "operator must inspect these legs. ***")


def write_report_csv(rows: list[dict], tag: str) -> str:
    os.makedirs("reports", exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"reports/leg_date_fix_{tag}_{ts}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_COLS + ["rows_written"],
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


# ── Commit write path (ONLY write in this module) ─────────────────────────────

def commit_batch(proposals: list[dict], batch: str) -> tuple[list[dict], int]:
    """
    Apply ONE batch of re-dates. Reachable ONLY from the --commit branch.

    Per leg, exactly one guarded single-column UPDATE:
        UPDATE legs
        SET leg_date=<corrected>
        WHERE leg_id=<id> AND settlement_status='pending'
              AND leg_date=<current_wrong_date>

    The status + current-date guard makes the write write-once and can never
    touch a settled row or an already-corrected row. Writes ONLY leg_date.
    Returns (per-leg report rows, total rows_written).
    """
    from api.cache import _client

    client = _client()
    targets = [p for p in proposals if batch_key(p) == batch]

    report: list[dict] = []
    total_written = 0
    for p in targets:
        res = (
            client.table("legs")
            .update({"leg_date": p["proposed_leg_date"]})
            .eq("leg_id", p["leg_id"])
            .eq("settlement_status", "pending")       # MANDATORY guards:
            .eq("leg_date", p["current_leg_date"])    # write-once, wrong rows only
            .execute()
        )
        rows_written = len(res.data or [])
        total_written += rows_written
        report.append({**p, "rows_written": rows_written})

    return report, total_written


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="leg_date off-by-one correction — dry-run by default")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Dry-run mode (default)")
    parser.add_argument("--commit", action="store_true", default=False,
                        help="Write corrected leg_date. Requires --batch "
                             "(one batch at a time; no bulk commit).")
    parser.add_argument("--batch", metavar="WRONG->RIGHT",
                        help='One of: "2026-06-26->2026-06-25", '
                             '"2026-07-07->2026-07-06"')
    args = parser.parse_args()

    if args.commit and not args.batch:
        print("[fix-dates] REJECTED: --commit requires an explicit --batch "
              "(one batch at a time; bulk commit is not enabled)")
        sys.exit(1)
    if args.commit and args.batch not in EXPECTED_BATCHES:
        print(f"[fix-dates] REJECTED: --batch {args.batch!r} is not an "
              f"investigation-confirmed batch: {sorted(EXPECTED_BATCHES)}")
        sys.exit(1)

    if args.commit:
        print(f"[fix-dates] COMMIT MODE — will re-date pending legs for batch "
              f"{args.batch} (leg_date column only)")
    else:
        print("[fix-dates] DRY-RUN — zero writes")

    proposals = identify_mislabeled_legs()
    print(f"[fix-dates] {len(proposals)} mislabeled leg(s) identified "
          f"(ET-of-ticket-created_at != leg_date, pending, non-removed)")

    anchor_check(proposals)

    print("\n=== PROPOSED RE-DATES (DRY-RUN — OPERATOR HAND-CHECK REQUIRED) ===\n")
    print_table(proposals)
    print_summary(proposals)

    tag = "dryrun" if not args.commit else args.batch.replace("->", "_to_").replace("-", "")
    csv_path = write_report_csv(proposals, tag if not args.commit else f"pre_{tag}")
    print(f"\n[fix-dates] CSV: {csv_path}")

    if not args.commit:
        print("[fix-dates] OPERATOR HAND-CHECK REQUIRED — no writes performed")
        return

    # ── COMMIT — the only reachable write path in this module ────────────────
    batch_count = sum(1 for p in proposals if batch_key(p) == args.batch)
    expected = EXPECTED_BATCHES[args.batch]
    if batch_count != expected:
        print(f"[fix-dates] REJECTED: batch {args.batch} identified "
              f"{batch_count} leg(s), investigation confirmed {expected} — "
              "mismatched set, refusing to write. Reconcile first.")
        sys.exit(1)

    report, total_written = commit_batch(proposals, args.batch)

    print("\n=== POST-WRITE REPORT (verify against Supabase) ===\n")
    print_table(report)
    print(f"\n[fix-dates] rows_written: {total_written}")
    if total_written == 0 and report:
        print("[fix-dates] 0 rows written with targets present — rows already "
              "corrected or no longer pending (the guard makes this idempotent).")

    commit_csv = write_report_csv(report, f"commit_{tag}")
    print(f"[fix-dates] commit CSV: {commit_csv}")


if __name__ == "__main__":
    main()
