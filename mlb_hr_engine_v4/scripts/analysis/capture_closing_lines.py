"""
capture_closing_lines.py — Session 26 CLV infrastructure.

Fetches current HR odds from The Odds API and records them as "closing" line
snapshots for CLV computation. Run this script ~30-60 minutes before first pitch
(or any time during the day to capture pre-game line movement).

Usage:
  py -3.12 capture_closing_lines.py                  # capture for today
  py -3.12 capture_closing_lines.py --type pre_game  # label as pre-game snapshot
  py -3.12 capture_closing_lines.py --help

Workflow:
  1. Fetch all current HR Over odds via The Odds API
  2. Store as "closing" snapshots in line_snapshots.csv
  3. Match against pick_tracker.csv picks for today/recent dates
  4. Compute CLV for matched picks and update pick_tracker.csv + clv_log.csv
  5. Print summary report

CLV formula:
  clv_pp = (close_no_vig - open_no_vig) × 100
  positive = we got better price than the closing line = sharp model signal
"""

import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Force UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent / "mlb_hr_engine_v4"))

import config
from clients import odds_api as _odds_api
from tracking import clv as _clv
from tracking import line_snapshots as _snaps
from tracking import pick_tracker as _pt


def main():
    # ── Parse args ────────────────────────────────────────────────────────────
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print(__doc__)
        return

    snapshot_type = "closing"
    if "--type" in args:
        idx = args.index("--type")
        if idx + 1 < len(args):
            snapshot_type = args[idx + 1]
            if snapshot_type not in ("opening", "pre_game", "closing", "manual"):
                print(f"[!] Unknown snapshot type '{snapshot_type}'. Using 'closing'.")
                snapshot_type = "closing"

    target_dates = [a for a in args if not a.startswith("--") and len(a) == 10 and a[4] == "-"]
    if not target_dates:
        target_dates = [date.today().isoformat()]

    today_str = date.today().isoformat()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"\n{'='*72}")
    print(f"  CAPTURE CLOSING LINES — {ts}")
    print(f"{'='*72}")
    print(f"  Snapshot type : {snapshot_type}")
    print(f"  Target dates  : {', '.join(target_dates)}")

    if not config.ODDS_API_KEY:
        print("\n  [ERROR] ODDS_API_KEY not set. Cannot fetch closing lines.")
        print("  Add ODDS_API_KEY to .env or Streamlit secrets.")
        return

    # ── Fetch current odds ─────────────────────────────────────────────────────
    print(f"\n  Fetching current HR odds from The Odds API...")
    props_raw, source_label, quota = _odds_api.get_hr_odds_all_games()

    if not props_raw:
        err = _odds_api.get_last_error()
        print(f"  [ERROR] No odds returned: {err or 'unknown error'}")
        print(f"  Quota: used={quota.get('used')}, remaining={quota.get('remaining')}")
        return

    print(f"  Source: {source_label}")
    print(f"  Props fetched: {len(props_raw)} raw lines")
    if quota.get("remaining") is not None:
        print(f"  API quota: {quota['used']} used, {quota['remaining']} remaining")

    # ── Save snapshots ─────────────────────────────────────────────────────────
    for date_str in target_dates:
        n_saved = _snaps.save_snapshots(props_raw, snapshot_type=snapshot_type, date_str=date_str)
        print(f"\n  [{date_str}] Saved {n_saved} {snapshot_type} snapshots to line_snapshots.csv")

    # ── Build player→best_odds lookup from props ───────────────────────────────
    import unicodedata

    def _norm(name: str) -> str:
        return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower().strip()

    # Best American odds per player (any book)
    best_odds: dict[str, tuple[int, str]] = {}   # normalized_name → (odds, book)
    for p in props_raw:
        name  = _norm(p.get("player_name", ""))
        price = p.get("price")
        book  = p.get("bookmaker", "")
        if not name or not price:
            continue
        try:
            price = int(price)
        except (ValueError, TypeError):
            continue
        if -100 < price < 100:
            continue
        if name not in best_odds or price > best_odds[name][0]:
            best_odds[name] = (price, book)

    print(f"\n  Players with closing odds: {len(best_odds)}")

    # ── Update pick_tracker.csv for matched picks ──────────────────────────────
    from engine.vig import no_vig_prob_for_book

    total_updated = 0
    total_clv_computed = 0

    for date_str in target_dates:
        # Ensure schema is current
        _pt._migrate_schema()
        rows = _pt._load_all()

        date_rows = [r for r in rows if r.get("date") == date_str]
        if not date_rows:
            print(f"  [{date_str}] No picks found in pick_tracker.csv")
            continue

        n_updated = 0
        n_clv     = 0
        clv_values = []

        for row in rows:
            if row.get("date") != date_str:
                continue
            if row.get("close_odds"):
                continue  # already has closing odds — skip

            pname = _norm(row.get("player_name", ""))
            if pname not in best_odds:
                continue

            close_american, close_book = best_odds[pname]
            sportsbook = row.get("sportsbook", "") or close_book

            try:
                close_nv = no_vig_prob_for_book(close_american, sportsbook)
            except Exception:
                close_nv = 0.0

            row["close_odds"]       = str(close_american)
            row["close_no_vig_pct"] = f"{close_nv * 100:.3f}"
            n_updated += 1

            # Compute CLV if we have opening no-vig
            open_nv_str = row.get("open_no_vig_pct", "")
            if not open_nv_str:
                # Backfill from american_odds / best_odds
                odds_str = row.get("best_odds") or row.get("american_odds") or ""
                try:
                    open_am = int(float(odds_str))
                    open_nv = no_vig_prob_for_book(open_am, sportsbook) if abs(open_am) >= 100 else 0.0
                    if open_nv > 0:
                        row["open_no_vig_pct"]  = f"{open_nv * 100:.3f}"
                        imp = _pt._american_to_implied(open_am)
                        row["open_implied_pct"] = f"{imp * 100:.3f}"
                except (ValueError, TypeError):
                    open_nv = 0.0
            else:
                try:
                    open_nv = float(open_nv_str) / 100.0
                except (ValueError, TypeError):
                    open_nv = 0.0

            if open_nv > 0 and close_nv > 0:
                clv_pp  = (close_nv - open_nv) * 100
                clv_pp  = max(-100.0, min(100.0, clv_pp))
                clv_rel = (clv_pp / (open_nv * 100)) * 100 if open_nv > 0 else 0.0
                row["clv_pp"]      = f"{clv_pp:.3f}"
                row["clv_pct_rel"] = f"{clv_rel:.2f}"
                clv_values.append(clv_pp)
                n_clv += 1

        if n_updated > 0:
            _pt._rewrite(rows)

        total_updated     += n_updated
        total_clv_computed += n_clv

        if clv_values:
            avg_clv = sum(clv_values) / len(clv_values)
            beats   = sum(1 for v in clv_values if v > 0)
            print(f"  [{date_str}] Updated {n_updated} picks | CLV computed: {n_clv} | "
                  f"Avg CLV: {avg_clv:+.3f}pp | Beats close: {beats}/{n_clv} "
                  f"({beats/n_clv*100:.1f}%)")
        elif n_updated > 0:
            print(f"  [{date_str}] Updated {n_updated} picks with closing odds "
                  f"(opening odds unavailable for CLV)")
        else:
            print(f"  [{date_str}] No matching picks to update "
                  f"(picks may have no odds logged or are already settled)")

    # ── Also update clv_log.csv ────────────────────────────────────────────────
    for date_str in target_dates:
        updated = _clv.fetch_and_compute_clv(target_date=date_str, snapshot_type=snapshot_type)
        if updated:
            has_clv = sum(1 for r in updated if r.get("clv_pp"))
            print(f"\n  [{date_str}] CLV log updated: {has_clv}/{len(updated)} entries with CLV")

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n{'='*72}")
    print(f"  SUMMARY")
    print(f"  Total picks updated in pick_tracker.csv : {total_updated}")
    print(f"  Total CLV values computed               : {total_clv_computed}")
    print()
    print(f"  Next steps:")
    print(f"    • Check CLV report: py -3.12 analyze_clv.py")
    print(f"    • Run daily ops: py -3.12 ops_daily.py")
    print(f"{'='*72}\n")


if __name__ == "__main__":
    main()
