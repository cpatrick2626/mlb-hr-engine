"""
Baseball Savant (Statcast) client — three-source, production-grade implementation.

Data sources (all free, no API key):
  1. /leaderboard/statcast        → barrel%, exit velo, sweet spot%, hard hit%, xSLG
  2. /leaderboard/batted-ball     → GB%, FB%, LD%, IFFB%, Pull%, Straight%, Oppo%
  3. /leaderboard/expected_statistics → xBA, xSLG, xwOBA, xISO (contact quality cross-check)

All three are merged per player_id. Current year is primary; prior year fills
missing players for early-season coverage. statcast leaderboard takes precedence
on any overlapping fields.

Batter power multiplier (7 signals, evidence-based weights):
  Barrel%      38%  — ~57% of barrels become HRs; the most HR-specific metric
  FB%          15%  — HRs require air balls; high FB% = more HR opportunities
  xSLG         14%  — contact quality proxy; stabilizes in ~50 PA vs ~300 for HR/PA
  Sweet Spot%  10%  — LA 8-32°: the exact angle band where HRs happen (replaces avg LA)
  Hard Hit%    10%  — EV >95 mph; secondary contact quality signal
  Pull%         8%  — ~43% of MLB HRs are pulled; pull side = short porch
  Exit Velo     5%  — raw power ceiling

Pitcher contact-quality factor (4 signals):
  Barrel% against  45%  — primary HR-vulnerability metric
  FB% against      25%  — more flies allowed = more HR exposure
  Hard Hit% against 15% — high-EV contact rate allowed
  Exit Velo against 15% — average raw contact quality
"""

import io
import csv
import requests
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

import config

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/csv,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://baseballsavant.mlb.com/",
})

# ── Module-level aliases — all canonical values live in config.py ─────────────
PRIOR_YEAR_TRUST    = config.PRIOR_YEAR_TRUST
MIN_CURRENT_YEAR_PA = config.MIN_CURRENT_YEAR_PA
LEAGUE_AVG_BARREL_RATE = config.LEAGUE_AVG_BARREL_RATE
LEAGUE_AVG_FB_PCT      = config.LEAGUE_AVG_FB_PCT
LEAGUE_AVG_EXIT_VELO   = config.LEAGUE_AVG_EXIT_VELO
LEAGUE_AVG_HARD_HIT    = config.LEAGUE_AVG_HARD_HIT
LEAGUE_AVG_XSLG        = config.LEAGUE_AVG_XSLG
LEAGUE_AVG_SWEET_SPOT  = config.LEAGUE_AVG_SWEET_SPOT
LEAGUE_AVG_PULL_PCT    = config.LEAGUE_AVG_PULL_PCT
LEAGUE_AVG_GB_PCT      = config.LEAGUE_AVG_GB_PCT
LEAGUE_AVG_LD_PCT      = config.LEAGUE_AVG_LD_PCT
LEAGUE_AVG_IFFB_PCT    = config.LEAGUE_AVG_IFFB_PCT
LEAGUE_AVG_STR_PCT     = config.LEAGUE_AVG_STR_PCT
LEAGUE_AVG_OPPO_PCT    = config.LEAGUE_AVG_OPPO_PCT

# Fields blended between current and prior Statcast seasons (shared by batter + pitcher tiers)
_BATTER_BLEND_KEYS = (
    "barrel_rate", "exit_velocity_avg", "hard_hit_pct",
    "sweet_spot_pct", "xslg", "fb_pct", "gb_pct",
    "ld_pct", "pull_pct", "pu_pct", "str_pct", "oppo_pct", "xba",
)
_PITCHER_BLEND_KEYS = (
    "barrel_rate", "exit_velocity_avg", "hard_hit_pct",
    "sweet_spot_pct", "xslg", "fb_pct", "gb_pct",
    "ld_pct", "pull_pct", "pu_pct", "str_pct", "oppo_pct",
)


# ── Public API ─────────────────────────────────────────────────────────────────

def get_batter_statcast(year: int = None, player_ids: set[int] = None) -> dict[int, dict]:
    """
    Full batter dataset: statcast + batted-ball + expected stats merged per player_id.

    Args:
        year: Season year (defaults to current)
        player_ids: Optional set of player IDs to filter (for performance)

    Three-tier prior-year coverage (runs every call regardless of curr size):
      Tier 1 — current-year data with >= MIN_CURRENT_YEAR_PA: full trust, no flag
      Tier 2 — current-year data but sparse (< MIN_CURRENT_YEAR_PA PA): signals
               linearly blended with prior-year; statcast_source = "blended"
      Tier 3 — no current-year data at all: use prior-year with trust discount;
               statcast_source = "prior"
    """
    year = year or config.CURRENT_SEASON

    # Fetch current and prior year data in parallel for better performance
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_curr = executor.submit(_merge_batter_sources, year, player_ids)
        future_prior = executor.submit(_merge_batter_sources, year - 1, player_ids)

        curr = future_curr.result()
        prior = future_prior.result()

    # Tier 3: player has zero current-year data
    for pid, stats in prior.items():
        if pid not in curr:
            curr[pid] = {**stats, "season": year - 1, "statcast_source": "prior"}

    # Tier 2: player has current-year data but PA count is too small to fully trust
    for pid in list(curr.keys()):
        if curr[pid].get("statcast_source"):
            continue   # already flagged as prior
        curr_pa = curr[pid].get("pa", 0)
        if 0 < curr_pa < MIN_CURRENT_YEAR_PA and pid in prior:
            trust   = curr_pa / MIN_CURRENT_YEAR_PA   # 0..1 over 0..30 PA
            blended = dict(curr[pid])
            for key in _BATTER_BLEND_KEYS:
                cv = curr[pid].get(key)
                pv = prior[pid].get(key)
                if cv is not None and pv is not None:
                    blended[key] = cv * trust + pv * (1.0 - trust)
                elif pv is not None:
                    blended[key] = pv
            blended["statcast_source"] = "blended"
            curr[pid] = blended

    return curr


def get_pitcher_statcast(year: int = None, player_ids: set[int] = None) -> dict[int, dict]:
    """
    Full pitcher dataset: statcast + batted-ball merged per player_id.

    Three-tier prior-year coverage (always fetches both years in parallel):
      Tier 1 — current-year data with >= MIN_CURRENT_YEAR_PA BF: full trust, no flag
      Tier 2 — current-year data but sparse (< MIN_CURRENT_YEAR_PA BF): signals
               linearly blended with prior-year; statcast_source = "blended"
      Tier 3 — no current-year data at all: use prior-year with trust discount;
               statcast_source = "prior"
    """
    year = year or config.CURRENT_SEASON

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_curr  = executor.submit(_merge_pitcher_sources, year,     player_ids)
        future_prior = executor.submit(_merge_pitcher_sources, year - 1, player_ids)
        curr  = future_curr.result()
        prior = future_prior.result()

    # Tier 3: pitcher has zero current-year data
    for pid, stats in prior.items():
        if pid not in curr:
            curr[pid] = {**stats, "season": year - 1, "statcast_source": "prior"}

    # Tier 2: pitcher has current data but BF count is too small to fully trust
    for pid in list(curr.keys()):
        if curr[pid].get("statcast_source"):
            continue   # already flagged as prior
        curr_pa = curr[pid].get("pa", 0)
        if 0 < curr_pa < MIN_CURRENT_YEAR_PA and pid in prior:
            trust   = curr_pa / MIN_CURRENT_YEAR_PA
            blended = dict(curr[pid])
            for key in _PITCHER_BLEND_KEYS:
                cv = curr[pid].get(key)
                pv = prior[pid].get(key)
                if cv is not None and pv is not None:
                    blended[key] = cv * trust + pv * (1.0 - trust)
                elif pv is not None:
                    blended[key] = pv
            blended["statcast_source"] = "blended"
            curr[pid] = blended

    return curr


def batter_power_multiplier(
    player_id: int,
    batter_data: dict[int, dict],
) -> float:
    """Composite power multiplier, all signals normalized to league avg = 1.0."""
    stats = dict(batter_data.get(player_id) or {})

    if not stats:
        return 1.0

    barrel_rate  = _safe(stats, "barrel_rate",      LEAGUE_AVG_BARREL_RATE, lo=0.0,   hi=0.30)
    ev           = _safe(stats, "exit_velocity_avg", LEAGUE_AVG_EXIT_VELO,   lo=60.0,  hi=120.0)
    xslg         = _safe(stats, "xslg",             LEAGUE_AVG_XSLG,        lo=0.05,  hi=1.20)
    hard_hit     = _safe(stats, "hard_hit_pct",     LEAGUE_AVG_HARD_HIT,    lo=0.0,   hi=0.80)
    sweet_spot   = _safe(stats, "sweet_spot_pct",   LEAGUE_AVG_SWEET_SPOT,  lo=0.0,   hi=0.70)
    fb_pct       = _safe(stats, "fb_pct",           LEAGUE_AVG_FB_PCT,      lo=0.05,  hi=0.70)
    pull_pct     = _safe(stats, "pull_pct",         LEAGUE_AVG_PULL_PCT,    lo=0.10,  hi=0.75)

    # Lower barrel floor (0.30 vs 0.40): true zero-barrel players score meaningfully lower.
    barrel_mult     = _clamp(barrel_rate  / LEAGUE_AVG_BARREL_RATE,  0.30, 2.50)
    ev_mult         = _clamp(1.0 + (ev - LEAGUE_AVG_EXIT_VELO) / 100.0, 0.85, 1.20)
    xslg_mult       = _clamp(xslg         / LEAGUE_AVG_XSLG,         0.50, 2.00)
    hard_hit_mult   = _clamp(hard_hit     / LEAGUE_AVG_HARD_HIT,     0.60, 1.70)
    sweet_spot_mult = _clamp(sweet_spot   / LEAGUE_AVG_SWEET_SPOT,   0.65, 1.55)
    fb_mult         = _clamp(fb_pct       / LEAGUE_AVG_FB_PCT,       0.55, 1.70)
    pull_mult       = _clamp(pull_pct     / LEAGUE_AVG_PULL_PCT,     0.65, 1.55)

    # Barrel% raised to 38% (strongest HR-specific signal); xSLG and Pull trimmed to fund it.
    composite = (
        barrel_mult       * 0.38
        + fb_mult         * 0.15
        + xslg_mult       * 0.14
        + pull_mult       * 0.08
        + sweet_spot_mult * 0.10
        + hard_hit_mult   * 0.10
        + ev_mult         * 0.05
    )
    raw_composite = _clamp(composite, 0.45, 1.75)

    # Prior-year-only data: shrink the deviation from 1.0 by PRIOR_YEAR_TRUST.
    # Year-to-year correlation on power metrics is ~0.75-0.80; 0.85 is slightly
    # optimistic but avoids under-predicting established power hitters.
    # "blended" source already has signals weighted by current/prior PA mix — no extra discount.
    source = stats.get("statcast_source", "current")
    if source == "prior":
        raw_composite = 1.0 + PRIOR_YEAR_TRUST * (raw_composite - 1.0)

    return round(_clamp(raw_composite, 0.45, 1.75), 3)


def pitcher_contact_suppressor(
    pitcher_id: int,
    pitcher_data: dict[int, dict],
) -> float:
    """
    4-signal pitcher contact quality factor.
    <1.0 = suppresses hard contact (good pitcher); >1.0 = homer-prone.
    """
    stats = dict(pitcher_data.get(pitcher_id) or {})

    if not stats:
        return 1.0

    barrel_against   = _safe(stats, "barrel_rate",       LEAGUE_AVG_BARREL_RATE, lo=0.0,  hi=0.25)
    ev_against       = _safe(stats, "exit_velocity_avg", LEAGUE_AVG_EXIT_VELO,   lo=60.0, hi=120.0)
    hard_hit_against = _safe(stats, "hard_hit_pct",      LEAGUE_AVG_HARD_HIT,    lo=0.0,  hi=0.80)
    fb_against       = _safe(stats, "fb_pct",            LEAGUE_AVG_FB_PCT,      lo=0.05, hi=0.70)

    barrel_mult  = _clamp(barrel_against   / LEAGUE_AVG_BARREL_RATE, 0.40, 2.50)
    fb_mult      = _clamp(fb_against       / LEAGUE_AVG_FB_PCT,      0.55, 1.70)
    hh_mult      = _clamp(hard_hit_against / LEAGUE_AVG_HARD_HIT,    0.60, 1.70)
    ev_mult      = _clamp(1.0 + (ev_against - LEAGUE_AVG_EXIT_VELO) / 100.0, 0.85, 1.20)

    composite = (
        barrel_mult * 0.45
        + fb_mult   * 0.25
        + hh_mult   * 0.15
        + ev_mult   * 0.15
    )

    # Mirror batter treatment: shrink prior-year-only pitcher data toward neutral.
    # Year-to-year correlation on contact quality metrics is ~0.75-0.80; 0.85
    # is slightly optimistic but avoids under-weighting established suppressors.
    # "blended" is already PA-weighted — no extra discount needed.
    source = stats.get("statcast_source", "current")
    if source == "prior":
        composite = 1.0 + PRIOR_YEAR_TRUST * (composite - 1.0)

    # Upper bound reduced 1.75→1.50: batter power multiplier also clamps at 1.75 but is
    # further damped 0.45x in statcast_blended_rate; pitcher contact suppressor feeds raw
    # into pitcher_combined_factor at 40% weight with no equivalent damping. 1.50 aligns
    # the effective ceiling with what the damped batter signal can produce.
    return round(_clamp(composite, 0.55, 1.50), 3)


def statcast_summary(
    player_id: int,
    batter_data: dict[int, dict],
) -> dict:
    """Return display-ready Statcast fields. Returns '--' for any missing value."""
    stats = dict(batter_data.get(player_id) or {})

    def _pct(key):
        v = stats.get(key)
        return f"{float(v)*100:.1f}%" if v is not None else "--"

    def _num(key, decimals=1):
        v = stats.get(key)
        return f"{float(v):.{decimals}f}" if v is not None else "--"

    return {
        "barrel_pct":      _pct("barrel_rate"),
        "exit_velo":       _num("exit_velocity_avg"),
        "hard_hit":        _pct("hard_hit_pct"),
        "sweet_spot_pct":  _pct("sweet_spot_pct"),
        "avg_launch_angle": round(float(stats["avg_launch_angle"]), 1)
                            if stats.get("avg_launch_angle") is not None else "--",
        "xslg":            round(float(stats["xslg"]), 3)
                            if stats.get("xslg") is not None else None,
        "fb_pct":          _pct("fb_pct"),
        "gb_pct":          _pct("gb_pct"),
        "ld_pct":          _pct("ld_pct"),
        "pull_pct":        _pct("pull_pct"),
        "oppo_pct":        _pct("oppo_pct"),
        "season":          stats.get("season", config.CURRENT_SEASON),
        "statcast_source": stats.get("statcast_source", "current"),
    }


# ── Internal merge helpers ─────────────────────────────────────────────────────

def _merge_batter_sources(year: int, player_ids: set[int] = None) -> dict[int, dict]:
    """Merge statcast + batted-ball + expected stats for batters.

    Args:
        year: Season year
        player_ids: Optional set of player IDs to filter (for performance)
    """
    # Convert set to frozenset for caching
    frozen_ids = frozenset(player_ids) if player_ids else None

    # Fetch all three sources in parallel for improved performance
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all fetch tasks concurrently
        future_sc = executor.submit(_fetch_leaderboard, "batter", year, frozen_ids)
        future_bb = executor.submit(_fetch_batted_ball, "batter", year, frozen_ids)
        future_xst = executor.submit(_fetch_expected_stats, "batter", year, frozen_ids)

        # Collect results as they complete
        sc = future_sc.result()
        bb = future_bb.result()
        xst = future_xst.result()

    merged: dict[int, dict] = {}

    # If filtering, only merge requested players
    pids_to_merge = set(sc) | set(bb) | set(xst)
    if player_ids:
        pids_to_merge &= player_ids

    for pid in pids_to_merge:
        row: dict = {}
        row.update(xst.get(pid) or {})   # lowest priority
        row.update(bb.get(pid)  or {})   # batted-ball fills direction stats
        row.update(sc.get(pid)  or {})   # statcast has highest priority
        if row:
            merged[pid] = row
    return merged


def _merge_pitcher_sources(year: int, player_ids: set[int] = None) -> dict[int, dict]:
    """Merge statcast + batted-ball for pitchers.

    Args:
        year: Season year
        player_ids: Optional set of player IDs to filter (for performance)
    """
    # Convert set to frozenset for caching
    frozen_ids = frozenset(player_ids) if player_ids else None

    # Fetch both sources in parallel for improved performance
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both fetch tasks concurrently
        future_sc = executor.submit(_fetch_leaderboard, "pitcher", year, frozen_ids)
        future_bb = executor.submit(_fetch_batted_ball, "pitcher", year, frozen_ids)

        # Collect results as they complete
        sc = future_sc.result()
        bb = future_bb.result()

    merged: dict[int, dict] = {}

    # If filtering, only merge requested players
    pids_to_merge = set(sc) | set(bb)
    if player_ids:
        pids_to_merge &= player_ids

    for pid in pids_to_merge:
        row: dict = {}
        row.update(bb.get(pid) or {})
        row.update(sc.get(pid) or {})
        if row:
            merged[pid] = row
    return merged


# ── Cached fetch functions ─────────────────────────────────────────────────────
# Manual success-only cache: lru_cache would permanently cache {} on failure,
# blocking retries for the rest of the session if Savant is temporarily down.

_FETCH_CACHE: dict = {}


def _fetch_leaderboard(player_type: str, year: int, player_ids: frozenset[int] = None) -> dict[int, dict]:
    """Fetch leaderboard data with optional filtering."""
    key = ("lb", player_type, year, player_ids)
    if key in _FETCH_CACHE:
        return _FETCH_CACHE[key]
    url = (
        "https://baseballsavant.mlb.com/leaderboard/statcast"
        f"?type={player_type}&year={year}&position=&team=&min=1&csv=true"
    )
    try:
        resp = _SESSION.get(url, timeout=25)
        if resp.status_code != 200:
            return {}
        result = _parse_statcast_csv(resp.text, year=year, player_ids=player_ids)
        _FETCH_CACHE[key] = result
        return result
    except Exception as e:
        print(f"[statcast] leaderboard fetch failed ({player_type} {year}): {e}")
        return {}


def _fetch_batted_ball(player_type: str, year: int, player_ids: frozenset[int] = None) -> dict[int, dict]:
    """Fetch batted ball data with optional filtering."""
    key = ("bb", player_type, year, player_ids)
    if key in _FETCH_CACHE:
        return _FETCH_CACHE[key]
    url = (
        "https://baseballsavant.mlb.com/leaderboard/batted-ball"
        f"?type={player_type}&year={year}&min=1&csv=true"
    )
    try:
        resp = _SESSION.get(url, timeout=25)
        if resp.status_code != 200:
            return {}
        result = _parse_batted_ball_csv(resp.text, player_ids=player_ids)
        _FETCH_CACHE[key] = result
        return result
    except Exception as e:
        print(f"[statcast] batted-ball fetch failed ({player_type} {year}): {e}")
        return {}


def _fetch_expected_stats(player_type: str, year: int, player_ids: frozenset[int] = None) -> dict[int, dict]:
    """Fetch expected stats data with optional filtering."""
    key = ("es", player_type, year, player_ids)
    if key in _FETCH_CACHE:
        return _FETCH_CACHE[key]
    url = (
        "https://baseballsavant.mlb.com/leaderboard/expected_statistics"
        f"?type={player_type}&year={year}&min=1&csv=true"
    )
    try:
        resp = _SESSION.get(url, timeout=25)
        if resp.status_code != 200:
            return {}
        result = _parse_expected_stats_csv(resp.text, player_ids=player_ids)
        _FETCH_CACHE[key] = result
        return result
    except Exception as e:
        print(f"[statcast] expected-stats fetch failed ({player_type} {year}): {e}")
        return {}


# ── CSV parsers ────────────────────────────────────────────────────────────────

def _parse_statcast_csv(raw: str, year: int = None, player_ids: frozenset[int] = None) -> dict[int, dict]:
    """Parse Statcast CSV with optional filtering.

    Args:
        raw: Raw CSV text
        year: Season year
        player_ids: Optional frozenset of player IDs to filter
    """
    _year = year or config.CURRENT_SEASON
    result: dict[int, dict] = {}
    reader = csv.DictReader(io.StringIO(raw.lstrip("\ufeff")))

    def _f(row, *keys, div: float = 1.0, allow_negative: bool = False) -> Optional[float]:
        for k in keys:
            v = row.get(k)
            if v not in (None, "", "null", "NA", "N/A"):
                try:
                    f = float(v) / div
                    return f if (allow_negative or f >= 0) else None
                except ValueError:
                    pass
        return None

    for row in reader:
        try:
            pid = int(row.get("player_id") or 0)
            if not pid:
                continue

            # Early filter: skip players not in the filter set
            if player_ids and pid not in player_ids:
                continue

            barrel_rate = _f(row, "brl_pa",           div=100.0)
            barrel_bip  = _f(row, "brl_percent",      div=100.0)
            ev          = _f(row, "avg_hit_speed",     "exit_velocity_avg")
            hard_hit    = _f(row, "ev95percent",       "hard_hit_percent", div=100.0)
            avg_la      = _f(row, "avg_hit_angle", "avg_launch_angle", "launch_angle_avg", allow_negative=True)
            sweet_spot  = _f(row, "sweet_spot_percent","anglesweetspotpercent",
                              "sweet_spot_pct",         div=100.0)
            xslg        = _f(row, "xslg", "expected_slg", "xSLG")
            pa          = _f(row, "pa", "attempts")

            row_out: dict = {"season": _year}
            if barrel_rate is not None: row_out["barrel_rate"]       = barrel_rate
            if barrel_bip  is not None: row_out["barrel_bip_rate"]   = barrel_bip
            if ev          is not None: row_out["exit_velocity_avg"] = ev
            if hard_hit    is not None: row_out["hard_hit_pct"]      = hard_hit
            if avg_la      is not None: row_out["avg_launch_angle"]  = avg_la
            if sweet_spot  is not None: row_out["sweet_spot_pct"]    = sweet_spot
            if xslg        is not None: row_out["xslg"]              = xslg
            if pa          is not None: row_out["pa"]                = int(pa)

            result[pid] = row_out
        except (ValueError, KeyError):
            continue

    return result


def _parse_batted_ball_csv(raw: str, player_ids: frozenset[int] = None) -> dict[int, dict]:
    """Parse batted ball CSV with optional filtering.

    Args:
        raw: Raw CSV text
        player_ids: Optional frozenset of player IDs to filter
    """
    result: dict[int, dict] = {}
    reader = csv.DictReader(io.StringIO(raw.lstrip("\ufeff")))

    def _pct(row, *keys) -> Optional[float]:
        for k in keys:
            v = row.get(k)
            if v not in (None, "", "null", "NA", "N/A"):
                try:
                    f = float(v)
                    # Baseball Savant switched from percentage (0-100) to decimal (0-1)
                    # columns named *_rate. Detect by range: <=1.5 is already a fraction.
                    if f > 1.5:
                        f /= 100.0
                    return f if 0.0 <= f <= 1.0 else None
                except ValueError:
                    pass
        return None

    for row in reader:
        try:
            # Baseball Savant uses "id" in batted-ball CSV, "player_id" in others
            pid = int(row.get("player_id") or row.get("id") or 0)
            if not pid:
                continue

            # Early filter: skip players not in the filter set
            if player_ids and pid not in player_ids:
                continue

            row_out = {
                # Current column names (*_rate, decimal 0-1); legacy names as fallback
                "gb_pct":   _pct(row, "gb_rate",       "gb_percent",           "gb"),
                "fb_pct":   _pct(row, "fb_rate",       "fb_percent",           "fb"),
                "ld_pct":   _pct(row, "ld_rate",       "ld_percent",           "ld"),
                "pu_pct":   _pct(row, "pu_rate",       "pu_percent",           "iff_percent", "ifb_percent"),
                "pull_pct": _pct(row, "pull_rate",     "pull_percent",         "pull"),
                "str_pct":  _pct(row, "straight_rate", "straightaway_percent", "center_percent"),
                "oppo_pct": _pct(row, "oppo_rate",     "oppo_percent",         "opposite_percent"),
            }
            if any(v is not None for v in row_out.values()):
                result[pid] = row_out
        except (ValueError, KeyError):
            continue

    return result


def _parse_expected_stats_csv(raw: str, player_ids: frozenset[int] = None) -> dict[int, dict]:
    """Parse expected stats CSV with optional filtering.

    Args:
        raw: Raw CSV text
        player_ids: Optional frozenset of player IDs to filter
    """
    result: dict[int, dict] = {}
    reader = csv.DictReader(io.StringIO(raw.lstrip("\ufeff")))

    def _f(row, *keys) -> Optional[float]:
        for k in keys:
            v = row.get(k)
            if v not in (None, "", "null", "NA", "N/A"):
                try:
                    return float(v)
                except ValueError:
                    pass
        return None

    for row in reader:
        try:
            pid = int(row.get("player_id") or 0)
            if not pid:
                continue

            # Early filter: skip players not in the filter set
            if player_ids and pid not in player_ids:
                continue

            xslg  = _f(row, "xslg",  "est_slg", "x_slg",  "expected_slg")
            xwoba = _f(row, "xwoba", "est_woba", "x_woba")
            xba   = _f(row, "xba",   "est_ba",  "x_ba")
            row_out: dict = {}
            if xslg  is not None: row_out["xslg"]  = xslg
            if xwoba is not None: row_out["xwoba"] = xwoba
            if xba   is not None: row_out["xba"]   = xba
            if row_out:
                result[pid] = row_out
        except (ValueError, KeyError):
            continue

    return result


# ── Utility ────────────────────────────────────────────────────────────────────

def _safe(d: dict, key: str, default: float,
          lo: float = 0.0, hi: float = float("inf")) -> float:
    """Get a float from dict, fall back to default, validate range."""
    v = d.get(key)
    if v is None:
        return default
    try:
        f = float(v)
        return f if lo <= f <= hi else default
    except (TypeError, ValueError):
        return default


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def clear_all_caches() -> None:
    """Clear Statcast fetch cache. Call before Force Refresh so next load
    fetches fresh leaderboard, batted-ball, and expected-stats data."""
    _FETCH_CACHE.clear()
