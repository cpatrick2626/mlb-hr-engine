# Run from repo root: python mlb_hr_engine_v4/scripts/ops/refresh_league_averages.py
# Add to OPS_DAILY_SETUP.md as a weekly refresh step
"""
refresh_league_averages.py

Fetches live 2026 league-average Statcast constants from Baseball Savant,
compares them against current config.py values, and prints a ready-to-paste
config.py patch block. Operator reviews and applies manually unless --apply
is passed.

Endpoints (mirrors mlb_hr_engine_v4/clients/statcast.py):
  - /leaderboard/statcast          (batter, min=50 PA)
  - /leaderboard/batted-ball       (batter, min=50 PA)
  - /leaderboard/expected_statistics (batter, min=50 PA)
  - /leaderboard/statcast          (pitcher, min=30 IP)

Output sections:
  1) CURRENT vs FETCHED diff table (delta + flag if >5%)
  2) Ready-to-paste config.py block
  3) Warnings if any value drifted >10% (possible data quality issue)

Flags:
  --apply    Patch config.py in place. Without it, this is a dry run.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from datetime import date
from pathlib import Path

import requests


# ── Baseline (current config.py values as of May-6, 2026) ─────────────────────
CURRENT: dict[str, float] = {
    "LEAGUE_AVG_BARREL_RATE": 0.055,
    "LEAGUE_AVG_EXIT_VELO":   89.1,
    "LEAGUE_AVG_HARD_HIT":    0.399,
    "LEAGUE_AVG_SWEET_SPOT":  0.334,
    "LEAGUE_AVG_XSLG":        0.418,
    "LEAGUE_AVG_FB_PCT":      0.264,
    "LEAGUE_AVG_GB_PCT":      0.428,
    "LEAGUE_AVG_LD_PCT":      0.235,
    "LEAGUE_AVG_PULL_PCT":    0.392,
    "LEAGUE_AVG_OPPO_PCT":    0.240,
    "LEAGUE_AVG_STR_PCT":     0.368,
    "LEAGUE_AVG_IFFB_PCT":    0.073,
    "LEAGUE_AVG_HR9":         1.05,
    "LEAGUE_HR_FB":           0.097,
    "LEAGUE_AVG_ISO":         0.157,
}

# Inline comment to write back into config.py for each constant when --apply is used.
COMMENT: dict[str, str] = {
    "LEAGUE_AVG_BARREL_RATE": "barrel per PA (brl_pa)",
    "LEAGUE_AVG_EXIT_VELO":   "mph average exit velocity",
    "LEAGUE_AVG_HARD_HIT":    "EV >95 mph rate",
    "LEAGUE_AVG_SWEET_SPOT":  "LA 8-32 deg sweet spot rate",
    "LEAGUE_AVG_XSLG":        "expected SLG (est_slg)",
    "LEAGUE_AVG_FB_PCT":      "Savant pure fly ball rate (excludes popups)",
    "LEAGUE_AVG_GB_PCT":      "ground ball rate",
    "LEAGUE_AVG_LD_PCT":      "line drive rate",
    "LEAGUE_AVG_PULL_PCT":    "pull rate",
    "LEAGUE_AVG_OPPO_PCT":    "opposite field rate",
    "LEAGUE_AVG_STR_PCT":     "straightaway/center rate",
    "LEAGUE_AVG_IFFB_PCT":    "infield fly ball (popup) rate",
    "LEAGUE_AVG_HR9":         "HR per 9 IP (qualified pitchers)",
    "LEAGUE_HR_FB":           "HR per fly ball",
    "LEAGUE_AVG_ISO":         "ISO = SLG - AVG",
}

# Decimal precision per constant when writing back.
PRECISION: dict[str, int] = {
    "LEAGUE_AVG_BARREL_RATE": 3,
    "LEAGUE_AVG_EXIT_VELO":   1,
    "LEAGUE_AVG_HARD_HIT":    3,
    "LEAGUE_AVG_SWEET_SPOT":  3,
    "LEAGUE_AVG_XSLG":        3,
    "LEAGUE_AVG_FB_PCT":      3,
    "LEAGUE_AVG_GB_PCT":      3,
    "LEAGUE_AVG_LD_PCT":      3,
    "LEAGUE_AVG_PULL_PCT":    3,
    "LEAGUE_AVG_OPPO_PCT":    3,
    "LEAGUE_AVG_STR_PCT":     3,
    "LEAGUE_AVG_IFFB_PCT":    3,
    "LEAGUE_AVG_HR9":         2,
    "LEAGUE_HR_FB":           3,
    "LEAGUE_AVG_ISO":         3,
}

YEAR = 2026
BATTER_MIN = 50
PITCHER_MIN = 30

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/csv,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://baseballsavant.mlb.com/",
}

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.py"


# ── HTTP + CSV helpers ────────────────────────────────────────────────────────
def _fetch_csv(url: str) -> list[dict]:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    text = resp.text.lstrip("﻿")
    return list(csv.DictReader(io.StringIO(text)))


def _f(row: dict, *keys: str) -> float | None:
    """Return first non-empty key as float, else None."""
    for k in keys:
        v = row.get(k)
        if v in (None, "", "null", "NA", "N/A"):
            continue
        try:
            return float(v)
        except ValueError:
            continue
    return None


def _pct(row: dict, *keys: str) -> float | None:
    """Return percentage value as a 0..1 decimal, handling both 0-100 and 0-1 sources."""
    v = _f(row, *keys)
    if v is None:
        return None
    if v > 1.5:
        v /= 100.0
    if not (0.0 <= v <= 1.0):
        return None
    return v


def _weighted_mean(pairs: list[tuple[float, float]]) -> float | None:
    """pairs is [(value, weight), ...] — returns None when no positive weight."""
    total_w = sum(w for _, w in pairs if w > 0)
    if total_w <= 0:
        return None
    total_v = sum(v * w for v, w in pairs if w > 0)
    return total_v / total_w


# ── Aggregation ───────────────────────────────────────────────────────────────
def _batter_statcast() -> dict[str, float]:
    """PA-weighted league averages from batter statcast leaderboard."""
    url = (
        "https://baseballsavant.mlb.com/leaderboard/statcast"
        f"?type=batter&year={YEAR}&min={BATTER_MIN}&csv=true"
    )
    rows = _fetch_csv(url)
    out: dict[str, list[tuple[float, float]]] = {
        "LEAGUE_AVG_BARREL_RATE": [],
        "LEAGUE_AVG_EXIT_VELO":   [],
        "LEAGUE_AVG_HARD_HIT":    [],
        "LEAGUE_AVG_SWEET_SPOT":  [],
    }
    iso_pairs: list[tuple[float, float]] = []

    for r in rows:
        pa = _f(r, "pa", "attempts")
        if not pa or pa < BATTER_MIN:
            continue

        brl = _f(r, "brl_pa")
        if brl is not None:
            out["LEAGUE_AVG_BARREL_RATE"].append((brl / 100.0, pa))

        ev = _f(r, "avg_hit_speed", "exit_velocity_avg")
        if ev is not None and 60.0 <= ev <= 125.0:
            out["LEAGUE_AVG_EXIT_VELO"].append((ev, pa))

        hh = _f(r, "ev95percent", "hard_hit_percent")
        if hh is not None:
            out["LEAGUE_AVG_HARD_HIT"].append((hh / 100.0, pa))

        sw = _f(r, "sweet_spot_percent", "anglesweetspotpercent", "sweet_spot_pct")
        if sw is not None:
            out["LEAGUE_AVG_SWEET_SPOT"].append((sw / 100.0, pa))

        slg = _f(r, "slg_percent", "slg", "slugging")
        avg = _f(r, "ba", "batting_avg", "avg")
        if slg is not None and avg is not None:
            iso = slg - avg
            if 0.0 <= iso <= 0.6:
                iso_pairs.append((iso, pa))

    result = {k: _weighted_mean(v) for k, v in out.items()}
    result["LEAGUE_AVG_ISO"] = _weighted_mean(iso_pairs)
    return result


def _batter_batted_ball() -> dict[str, float]:
    """PA-weighted league averages from batted-ball leaderboard."""
    url = (
        "https://baseballsavant.mlb.com/leaderboard/batted-ball"
        f"?type=batter&year={YEAR}&min={BATTER_MIN}&csv=true"
    )
    rows = _fetch_csv(url)
    keys = {
        "LEAGUE_AVG_FB_PCT":   ("fb_rate", "fb_percent", "fb"),
        "LEAGUE_AVG_GB_PCT":   ("gb_rate", "gb_percent", "gb"),
        "LEAGUE_AVG_LD_PCT":   ("ld_rate", "ld_percent", "ld"),
        "LEAGUE_AVG_IFFB_PCT": ("pu_rate", "pu_percent", "iff_percent", "ifb_percent"),
        "LEAGUE_AVG_PULL_PCT": ("pull_rate", "pull_percent", "pull"),
        "LEAGUE_AVG_OPPO_PCT": ("oppo_rate", "oppo_percent", "opposite_percent"),
        "LEAGUE_AVG_STR_PCT":  ("straight_rate", "straightaway_percent", "center_percent"),
    }
    bag: dict[str, list[tuple[float, float]]] = {k: [] for k in keys}

    for r in rows:
        # batted-ball CSV uses "id" or "player_id"; weight is BBE/PA if present, else 1.
        pa = _f(r, "pa", "attempts", "bbe", "batted_ball_events") or 1.0
        for label, candidates in keys.items():
            v = _pct(r, *candidates)
            if v is not None:
                bag[label].append((v, pa))

    return {k: _weighted_mean(v) for k, v in bag.items()}


def _batter_expected() -> dict[str, float]:
    """PA-weighted xSLG from expected-statistics leaderboard."""
    url = (
        "https://baseballsavant.mlb.com/leaderboard/expected_statistics"
        f"?type=batter&year={YEAR}&min={BATTER_MIN}&csv=true"
    )
    rows = _fetch_csv(url)
    pairs: list[tuple[float, float]] = []
    for r in rows:
        pa = _f(r, "pa", "attempts") or 1.0
        xslg = _f(r, "xslg", "est_slg", "expected_slg")
        if xslg is not None and 0.0 <= xslg <= 1.5:
            pairs.append((xslg, pa))
    return {"LEAGUE_AVG_XSLG": _weighted_mean(pairs)}


def _pitcher_aggregates() -> dict[str, float]:
    """Totals-based aggregates from pitcher statcast leaderboard."""
    url = (
        "https://baseballsavant.mlb.com/leaderboard/statcast"
        f"?type=pitcher&year={YEAR}&min={PITCHER_MIN}&csv=true"
    )
    rows = _fetch_csv(url)

    total_hr = 0.0
    total_ip = 0.0
    total_air_outs = 0.0

    for r in rows:
        ip = _f(r, "ip", "innings_pitched", "p_formatted_ip")
        if ip is None or ip < PITCHER_MIN:
            continue
        hr = _f(r, "hrs", "home_run", "home_runs", "hr")
        if hr is None:
            continue
        ao = _f(r, "air_out", "air_outs", "airOuts", "fb", "fly_balls")
        total_hr += hr
        total_ip += ip
        if ao is not None:
            total_air_outs += ao

    result: dict[str, float | None] = {"LEAGUE_AVG_HR9": None, "LEAGUE_HR_FB": None}
    if total_ip > 0:
        result["LEAGUE_AVG_HR9"] = (total_hr / total_ip) * 9.0
    if (total_hr + total_air_outs) > 0:
        result["LEAGUE_HR_FB"] = total_hr / (total_hr + total_air_outs)
    return result


def fetch_all() -> dict[str, float]:
    fetched: dict[str, float] = {}
    for source in (_batter_statcast, _batter_batted_ball, _batter_expected, _pitcher_aggregates):
        fetched.update(source())
    return fetched


# ── Output formatting ─────────────────────────────────────────────────────────
def _fmt(name: str, value: float | None) -> str:
    if value is None:
        return "  n/a"
    return f"{value:.{PRECISION[name]}f}"


def print_diff(fetched: dict[str, float]) -> list[tuple[str, float, float, float]]:
    """Print the diff table and return list of (name, old, new, pct_delta) for >5% flags."""
    print("\n" + "=" * 78)
    print(f"  SECTION 1 — CURRENT vs FETCHED  (Baseball Savant {YEAR}, fetched {date.today().isoformat()})")
    print("=" * 78)
    print(f"{'CONSTANT':<26} {'CURRENT':>10} {'FETCHED':>10} {'DELTA':>10} {'%':>8}  FLAG")
    print("-" * 78)

    flagged: list[tuple[str, float, float, float]] = []
    for name in CURRENT:
        old = CURRENT[name]
        new = fetched.get(name)
        if new is None:
            print(f"{name:<26} {old:>10.4f} {'n/a':>10} {'n/a':>10} {'n/a':>8}  FETCH-FAIL")
            continue
        delta = new - old
        pct = (delta / old) * 100.0 if old else 0.0
        flag = ""
        if abs(pct) > 10:
            flag = "!! >10%"
        elif abs(pct) > 5:
            flag = "!  >5%"
        print(
            f"{name:<26} {old:>10.4f} {new:>10.4f} {delta:>+10.4f} {pct:>+7.1f}%  {flag}"
        )
        flagged.append((name, old, new, pct))
    return flagged


def print_patch_block(fetched: dict[str, float]) -> None:
    today = date.today().strftime("%Y %b-%d")
    print("\n" + "=" * 78)
    print("  SECTION 2 — READY-TO-PASTE config.py BLOCK")
    print("=" * 78)
    for name in CURRENT:
        new = fetched.get(name)
        if new is None:
            print(f"# {name}: float = <fetch failed — leave as-is>")
            continue
        val = f"{new:.{PRECISION[name]}f}"
        print(f"{name}: float = {val}  # {COMMENT[name]}; {today}")


def print_warnings(diffs: list[tuple[str, float, float, float]]) -> None:
    big = [(n, o, v, p) for (n, o, v, p) in diffs if abs(p) > 10]
    print("\n" + "=" * 78)
    print("  SECTION 3 — WARNINGS")
    print("=" * 78)
    if not big:
        print("  No constants drifted by more than 10%. Looks clean.")
        return
    print("  The following constants drifted by more than 10% — verify before applying:")
    for name, old, new, pct in big:
        print(f"    {name}: {old:.4f} -> {new:.4f} ({pct:+.1f}%)")
    print("  Possible causes: small sample size early in season, Savant column rename,")
    print("  upstream data outage, or a genuine league-level shift.")


# ── --apply: patch config.py in place ─────────────────────────────────────────
def apply_to_config(fetched: dict[str, float]) -> None:
    if not CONFIG_PATH.exists():
        print(f"ERROR: config.py not found at {CONFIG_PATH}")
        sys.exit(1)

    text = CONFIG_PATH.read_text()
    today = date.today().strftime("%Y %b-%d")
    patched = 0
    skipped: list[str] = []

    for name in CURRENT:
        new = fetched.get(name)
        if new is None:
            skipped.append(f"{name} (no fetched value)")
            continue
        val = f"{new:.{PRECISION[name]}f}"
        # Match an assignment line; preserve indentation and the type annotation.
        pattern = re.compile(
            rf"^(?P<indent>[ \t]*){re.escape(name)}\s*:\s*float\s*=\s*[^\n#]+(?P<rest>(?:\s*#.*)?)$",
            re.MULTILINE,
        )
        replacement = rf"\g<indent>{name}: float = {val}  # {COMMENT[name]}; {today}"
        new_text, count = pattern.subn(replacement, text, count=1)
        if count == 0:
            skipped.append(f"{name} (no matching line in config.py)")
            continue
        text = new_text
        patched += 1

    CONFIG_PATH.write_text(text)
    print(f"\nAPPLIED: {patched} constants written to {CONFIG_PATH}")
    if skipped:
        print("SKIPPED:")
        for s in skipped:
            print(f"  - {s}")


# ── Entrypoint ────────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Write fetched values into config.py (default: dry run).")
    args = parser.parse_args()

    print(f"Fetching {YEAR} Baseball Savant league averages "
          f"(batter min={BATTER_MIN} PA, pitcher min={PITCHER_MIN} IP)...")
    try:
        fetched = fetch_all()
    except requests.RequestException as e:
        print(f"ERROR: Savant fetch failed: {e}", file=sys.stderr)
        return 2

    diffs = print_diff(fetched)
    print_patch_block(fetched)
    print_warnings(diffs)

    if args.apply:
        apply_to_config(fetched)
    else:
        print("\nDRY RUN — pass --apply to write config.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
