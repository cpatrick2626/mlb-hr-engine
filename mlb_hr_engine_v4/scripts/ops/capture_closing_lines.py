"""
capture_closing_lines.py — fetch current HR odds and compute CLV for today's picks.

Run ~30 min before first pitch (~6:45 PM ET for night slates).
Writes closing_american / clv_pp / clv_pct_rel into clv_log.csv.
"""

import sys
from pathlib import Path

ROOT_V4 = Path(__file__).resolve().parent.parent.parent   # mlb_hr_engine_v4/
sys.path.insert(0, str(ROOT_V4))

from tracking import clv as clv_tracker  # noqa: E402 (path insert above)


def main():
    print("[capture_closing_lines] fetching current HR odds and computing CLV …")
    results = clv_tracker.fetch_and_compute_clv()
    if not results:
        print("[capture_closing_lines] no CLV rows for today (clv_log.csv may be empty)")
        return
    filled = sum(1 for r in results if r.get("clv_pp"))
    print(f"[capture_closing_lines] done — {filled}/{len(results)} picks have CLV computed")
    for r in results:
        print(f"  {r.get('player_name','?'):25s}  open={r.get('opening_american','?'):>5}  "
              f"close={r.get('closing_american','?'):>5}  clv={r.get('clv_pp','?'):>7}")


if __name__ == "__main__":
    main()
