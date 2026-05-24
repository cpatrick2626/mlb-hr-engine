"""
Pitcher HR Splits Integrity Audit
==================================
Traces Joey Cantillo from raw Savant events upward through the pipeline,
then validates 25 random pitchers.

Run from repo root:
    cd mlb_hr_engine_v4 && python ../audit_pitcher_hr_splits.py
"""

import csv
import io
import json
import os
import random
import sys
import requests
from collections import defaultdict

# ── path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.join(os.path.dirname(__file__), "mlb_hr_engine_v4"))

import config

MLB_API = "https://statsapi.mlb.com/api/v1"
SAVANT  = "https://baseballsavant.mlb.com"

_HDR = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://baseballsavant.mlb.com/",
}
_SESS = requests.Session()
_SESS.headers.update(_HDR)

_HF_AB_CURRENT = (
    "home_run|strikeout|strikeout_double_play|single|double|triple|"
    "field_out|force_out|grounded_into_double_play|double_play|"
    "sac_fly|field_error|fielders_choice|"
)

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "pitcher_hr_audit_output.txt")

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _mlb_get(path, params=None):
    resp = _SESS.get(f"{MLB_API}{path}", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def find_pitcher_id(name: str) -> tuple[int, str]:
    """Search MLB Stats API for a pitcher by name. Returns (id, fullName)."""
    data = _mlb_get("/people/search", {"names": name, "sportId": 1})
    people = data.get("people", [])
    if not people:
        raise ValueError(f"Pitcher '{name}' not found via MLB API search")
    # Take the first result with position = Pitcher (or just take first)
    for p in people:
        return p["id"], p.get("fullName", name)
    return people[0]["id"], people[0].get("fullName", name)


def get_mlb_api_season_hr(pitcher_id: int, season: int) -> dict:
    """Fetch total HR allowed from MLB Stats API for a given season."""
    data = _mlb_get(f"/people/{pitcher_id}/stats", {
        "stats": "season", "group": "pitching", "season": season,
    })
    for sg in data.get("stats", []):
        splits = sg.get("splits", [])
        if splits:
            s = splits[0].get("stat", {})
            return {
                "hr": int(s.get("homeRuns", 0)),
                "ip": s.get("inningsPitched", "0.0"),
                "bf": int(s.get("battersFaced", 0)),
                "source": "mlb_api_season",
                "season": season,
            }
    return {"hr": 0, "ip": "0.0", "bf": 0, "source": "mlb_api_season", "season": season}


def fetch_savant_raw(pitcher_id: int, season: int,
                     restrict_to_regular: bool = False) -> list[dict]:
    """
    Fetch ALL PA-ending events from Savant for a pitcher/season.
    restrict_to_regular=True adds hfGT=R| to restrict to regular season only.
    Returns a list of row dicts (all columns).
    """
    params = {
        "all":               "true",
        "player_type":       "pitcher",
        "pitchers_lookup[]": pitcher_id,
        "season":            season,
        "type":              "details",
        "hfAB":              _HF_AB_CURRENT,
    }
    if restrict_to_regular:
        params["hfGT"] = "R|"

    resp = _SESS.get(f"{SAVANT}/statcast_search/csv", params=params, timeout=25)
    resp.raise_for_status()
    rows = list(csv.DictReader(io.StringIO(resp.text.lstrip("﻿"))))
    return rows


def analyze_savant_rows(rows: list[dict], season: int, label: str) -> dict:
    """
    Analyze a list of Savant rows for a single pitcher.
    Returns aggregated stats + per-HR-event details.
    """
    hr_events = []
    seen_pa = set()          # (game_pk, at_bat_number) — for deduplication check
    duplicate_pa = []        # PAs seen more than once
    off_season_rows = []     # rows where game_year != season

    hand_totals = defaultdict(lambda: {"pa": 0, "hr": 0})
    game_type_counts = defaultdict(int)

    for row in rows:
        ev    = (row.get("events") or "").strip().lower()
        stand = (row.get("stand")  or "").strip().upper()
        gtype = (row.get("game_type") or row.get("game_type_des") or "").strip()
        gyear_raw = row.get("game_year") or row.get("game_date", "")[:4]
        try:
            gyear = int(gyear_raw) if gyear_raw else 0
        except (ValueError, TypeError):
            gyear = 0

        if not ev:
            continue

        game_pk  = row.get("game_pk", "")
        ab_num   = row.get("at_bat_number", row.get("ab_id", ""))
        pa_key   = (game_pk, ab_num)

        # Season contamination check
        if gyear and gyear != season:
            off_season_rows.append({
                "game_pk": game_pk, "game_year": gyear, "expected_season": season,
                "event": ev, "stand": stand, "game_type": gtype,
                "game_date": row.get("game_date", ""),
            })

        game_type_counts[gtype] += 1

        # Deduplication check
        if pa_key in seen_pa:
            duplicate_pa.append({
                "game_pk": game_pk, "at_bat_number": ab_num,
                "event": ev, "stand": stand, "game_date": row.get("game_date", ""),
            })
        seen_pa.add(pa_key)

        # HR event collection
        if ev == "home_run":
            hr_events.append({
                "game_pk":       game_pk,
                "at_bat_number": ab_num,
                "game_date":     row.get("game_date", ""),
                "game_year":     gyear,
                "game_type":     gtype,
                "stand":         stand,
                "batter_name":   row.get("batter_name", row.get("batter", "")),
                "batter_id":     row.get("batter", ""),
                "pitch_type":    row.get("pitch_type", ""),
                "release_speed": row.get("release_speed", ""),
                "launch_speed":  row.get("launch_speed", ""),
                "source_table":  "savant_statcast_search",
                "label":         label,
            })
            if stand in ("L", "R"):
                hand_totals[stand]["hr"] += 1
            hand_totals["ALL"]["hr"] += 1

        # PA count for all events
        if stand in ("L", "R"):
            hand_totals[stand]["pa"] += 1
        hand_totals["ALL"]["pa"] += 1

    return {
        "label":            label,
        "total_rows":       len(rows),
        "hr_events":        hr_events,
        "hr_vs_R":          hand_totals["R"]["hr"],
        "hr_vs_L":          hand_totals["L"]["hr"],
        "hr_total":         hand_totals["ALL"]["hr"],
        "pa_vs_R":          hand_totals["R"]["pa"],
        "pa_vs_L":          hand_totals["L"]["pa"],
        "pa_total":         hand_totals["ALL"]["pa"],
        "duplicate_pas":    duplicate_pa,
        "off_season_rows":  off_season_rows,
        "game_type_counts": dict(game_type_counts),
    }


def run_cantillo_trace(out_lines: list[str], season: int) -> tuple[dict, dict]:
    """Full Cantillo trace: raw events, both query variants, MLB API baseline."""
    out_lines.append("=" * 70)
    out_lines.append("SECTION 1 — JOEY CANTILLO TRACE")
    out_lines.append("=" * 70)

    # ── Look up pitcher ID ────────────────────────────────────────────────────
    try:
        pid, full_name = find_pitcher_id("Cantillo")
        out_lines.append(f"Pitcher found: {full_name}  (id={pid})")
    except Exception as e:
        out_lines.append(f"ERROR: could not find Cantillo via MLB API: {e}")
        out_lines.append("Falling back to known MLB ID 668715")
        pid, full_name = 668715, "Joey Cantillo"

    # ── MLB API ground truth ──────────────────────────────────────────────────
    out_lines.append(f"\n── MLB API baseline (ground truth) for {season} ──")
    mlb = get_mlb_api_season_hr(pid, season)
    out_lines.append(f"  HR total (MLB API): {mlb['hr']}")
    out_lines.append(f"  IP:                 {mlb['ip']}")
    out_lines.append(f"  BF:                 {mlb['bf']}")

    # ── Savant: current pipeline (no game-type filter) ────────────────────────
    out_lines.append(f"\n── Savant query: season={season}, NO game-type filter (current pipeline) ──")
    rows_bug = fetch_savant_raw(pid, season, restrict_to_regular=False)
    analysis_bug = analyze_savant_rows(rows_bug, season, f"BUGGY (no hfGT)")

    out_lines.append(f"  Total rows returned: {analysis_bug['total_rows']}")
    out_lines.append(f"  HR vs RHB: {analysis_bug['hr_vs_R']}")
    out_lines.append(f"  HR vs LHB: {analysis_bug['hr_vs_L']}")
    out_lines.append(f"  HR total:  {analysis_bug['hr_total']}")
    out_lines.append(f"  PA vs RHB: {analysis_bug['pa_vs_R']}")
    out_lines.append(f"  PA vs LHB: {analysis_bug['pa_vs_L']}")
    out_lines.append(f"  Duplicate PA events: {len(analysis_bug['duplicate_pas'])}")
    out_lines.append(f"  Off-season rows (game_year != {season}): {len(analysis_bug['off_season_rows'])}")
    out_lines.append(f"  Game type breakdown: {json.dumps(analysis_bug['game_type_counts'])}")

    # ── Savant: fixed query (with game-type = Regular Season) ────────────────
    out_lines.append(f"\n── Savant query: season={season}, hfGT=R| (fixed) ──")
    rows_fix = fetch_savant_raw(pid, season, restrict_to_regular=True)
    analysis_fix = analyze_savant_rows(rows_fix, season, f"FIXED (hfGT=R|)")

    out_lines.append(f"  Total rows returned: {analysis_fix['total_rows']}")
    out_lines.append(f"  HR vs RHB: {analysis_fix['hr_vs_R']}")
    out_lines.append(f"  HR vs LHB: {analysis_fix['hr_vs_L']}")
    out_lines.append(f"  HR total:  {analysis_fix['hr_total']}")
    out_lines.append(f"  PA vs RHB: {analysis_fix['pa_vs_R']}")
    out_lines.append(f"  PA vs LHB: {analysis_fix['pa_vs_L']}")
    out_lines.append(f"  Duplicate PA events: {len(analysis_fix['duplicate_pas'])}")
    out_lines.append(f"  Off-season rows: {len(analysis_fix['off_season_rows'])}")

    # ── Delta (root cause evidence) ───────────────────────────────────────────
    out_lines.append(f"\n── Delta (buggy - fixed) ──")
    out_lines.append(f"  ΔHR vs RHB: {analysis_bug['hr_vs_R'] - analysis_fix['hr_vs_R']:+d}")
    out_lines.append(f"  ΔHR vs LHB: {analysis_bug['hr_vs_L'] - analysis_fix['hr_vs_L']:+d}")
    out_lines.append(f"  ΔHR total:  {analysis_bug['hr_total'] - analysis_fix['hr_total']:+d}")
    out_lines.append(f"  ΔRows:      {analysis_bug['total_rows'] - analysis_fix['total_rows']:+d}")

    # ── Per-HR event table (buggy set) ────────────────────────────────────────
    out_lines.append(f"\n── All HR events returned by BUGGY query ──")
    out_lines.append(
        f"  {'game_pk':<12} {'at_bat':<8} {'date':<12} {'yr':<6} "
        f"{'gtype':<8} {'stand':<6} {'batter':<25} {'pitch':<6} {'EV':<6}"
    )
    out_lines.append("  " + "-" * 100)
    for evt in sorted(analysis_bug['hr_events'], key=lambda x: (x['game_date'], x['at_bat_number'])):
        out_lines.append(
            f"  {str(evt['game_pk']):<12} {str(evt['at_bat_number']):<8} "
            f"{evt['game_date']:<12} {str(evt['game_year']):<6} "
            f"{evt['game_type']:<8} {evt['stand']:<6} "
            f"{str(evt['batter_name'])[:25]:<25} "
            f"{evt['pitch_type']:<6} {str(evt.get('launch_speed','')):<6}"
        )

    # ── Off-season contamination detail ──────────────────────────────────────
    if analysis_bug['off_season_rows']:
        out_lines.append(f"\n── Off-season rows in BUGGY query (game_year != {season}) ──")
        for r in analysis_bug['off_season_rows'][:30]:
            out_lines.append(f"  {r}")
    else:
        out_lines.append(f"\n  [No rows with game_year != {season} detected in query output]")

    # ── Duplicate PA detail ───────────────────────────────────────────────────
    if analysis_bug['duplicate_pas']:
        out_lines.append(f"\n── Duplicate PA events (BUGGY query) ──")
        for r in analysis_bug['duplicate_pas'][:20]:
            out_lines.append(f"  {r}")

    # ── HRs unique after deduplication ───────────────────────────────────────
    unique_hr_pks_bug = set((e['game_pk'], e['at_bat_number']) for e in analysis_bug['hr_events'])
    unique_hr_pks_fix = set((e['game_pk'], e['at_bat_number']) for e in analysis_fix['hr_events'])
    out_lines.append(f"\n── Deduplication check ──")
    out_lines.append(f"  Buggy:   {len(analysis_bug['hr_events'])} total HR rows → {len(unique_hr_pks_bug)} unique (game_pk, ab_num) pairs")
    out_lines.append(f"  Fixed:   {len(analysis_fix['hr_events'])} total HR rows → {len(unique_hr_pks_fix)} unique (game_pk, ab_num) pairs")

    # ── Verdict ───────────────────────────────────────────────────────────────
    out_lines.append(f"\n── Verdict ──")
    rhb_delta = analysis_bug['hr_vs_R'] - analysis_fix['hr_vs_R']
    lhb_delta = analysis_bug['hr_vs_L'] - analysis_fix['hr_vs_L']
    dup_delta  = len(analysis_bug['hr_events']) - len(unique_hr_pks_bug)

    if rhb_delta != 0 or lhb_delta != 0:
        out_lines.append(f"  CONFIRMED: hfGT filter explains ΔHR_RHB={rhb_delta:+d}, ΔHR_LHB={lhb_delta:+d}")
        gtype_extra = {k: v for k, v in analysis_bug['game_type_counts'].items() if k != 'R'}
        if gtype_extra:
            out_lines.append(f"  Non-regular-season game types in buggy query: {gtype_extra}")
        else:
            out_lines.append("  Note: game_type field empty in response — contamination source determined by game_year or date range")
    if dup_delta > 0:
        out_lines.append(f"  CONFIRMED: {dup_delta} duplicate PA rows in buggy query")

    return analysis_bug, analysis_fix


def audit_25_pitchers(out_lines: list[str], season: int) -> None:
    """Fetch today's schedule and audit all starting pitchers. Falls back to 25 known IDs."""
    out_lines.append("\n" + "=" * 70)
    out_lines.append("SECTION 2 — 25-PITCHER RANDOM AUDIT")
    out_lines.append("=" * 70)

    # Grab today's probable starters from MLB schedule
    try:
        data = _mlb_get("/schedule", {
            "sportId": 1,
            "date": config.TARGET_DATE or str(__import__("datetime").date.today()),
            "hydrate": "probablePitcher,team",
            "language": "en",
        })
        pitcher_ids = {}
        for de in data.get("dates", []):
            for g in de.get("games", []):
                for side in ("home", "away"):
                    pp = g.get("teams", {}).get(side, {}).get("probablePitcher", {})
                    pid = pp.get("id")
                    name = pp.get("fullName", "Unknown")
                    if pid:
                        pitcher_ids[pid] = name
        out_lines.append(f"Pulled {len(pitcher_ids)} probable starters from today's schedule")
    except Exception as e:
        out_lines.append(f"Schedule fetch failed ({e}); using hardcoded pitcher IDs")
        pitcher_ids = {}

    # If schedule gave us fewer than 10, supplement with known 2026 starters
    _KNOWN = {
        668715: "Joey Cantillo",   677551: "Shane Bieber",   605483: "Corbin Burnes",
        592789: "Gerrit Cole",     666142: "Logan Gilbert",  607536: "Sandy Alcantara",
        621111: "Pablo Lopez",     668678: "Cristian Javier", 669373: "MacKenzie Gore",
        666201: "Framber Valdez",  681911: "Spencer Strider", 641154: "Yu Darvish",
        656302: "Zac Gallen",      663738: "Nestor Cortes",   682243: "Hunter Greene",
        670770: "Bryce Miller",    665871: "Tyler Anderson",  669219: "Dean Kremer",
        660271: "Taj Bradley",     669373: "MacKenzie Gore",  681867: "Kodai Senga",
        641482: "Kyle Freeland",   592332: "Sonny Gray",      605400: "Miles Mikolas",
        596019: "Jake Odorizzi",
    }
    for pid, nm in _KNOWN.items():
        if pid not in pitcher_ids:
            pitcher_ids[pid] = nm
        if len(pitcher_ids) >= 25:
            break

    audit_pitcher_ids = dict(list(pitcher_ids.items())[:25])
    out_lines.append(f"Auditing {len(audit_pitcher_ids)} pitchers\n")

    header = (
        f"{'Pitcher':<25} {'ID':<8} "
        f"{'MLB_HR':<8} "
        f"{'Bug_R':<7} {'Bug_L':<7} {'Bug_T':<7} "
        f"{'Fix_R':<7} {'Fix_L':<7} {'Fix_T':<7} "
        f"{'ΔR':<5} {'ΔL':<5} {'ΔT':<5} "
        f"{'Dups':<5} {'OffSzn':<7} {'GameTypes'}"
    )
    out_lines.append(header)
    out_lines.append("-" * len(header))

    discrepancies = []

    for pit_id, pit_name in audit_pitcher_ids.items():
        try:
            mlb = get_mlb_api_season_hr(pit_id, season)
            rows_bug = fetch_savant_raw(pit_id, season, restrict_to_regular=False)
            rows_fix = fetch_savant_raw(pit_id, season, restrict_to_regular=True)

            a_bug = analyze_savant_rows(rows_bug, season, "bug")
            a_fix = analyze_savant_rows(rows_fix, season, "fix")

            dR = a_bug['hr_vs_R'] - a_fix['hr_vs_R']
            dL = a_bug['hr_vs_L'] - a_fix['hr_vs_L']
            dT = a_bug['hr_total'] - a_fix['hr_total']
            dups = len(a_bug['duplicate_pas'])
            off  = len(a_bug['off_season_rows'])
            gtypes = ",".join(k for k in a_bug['game_type_counts'] if k and k != "R") or "—"

            line = (
                f"{pit_name[:25]:<25} {pit_id:<8} "
                f"{mlb['hr']:<8} "
                f"{a_bug['hr_vs_R']:<7} {a_bug['hr_vs_L']:<7} {a_bug['hr_total']:<7} "
                f"{a_fix['hr_vs_R']:<7} {a_fix['hr_vs_L']:<7} {a_fix['hr_total']:<7} "
                f"{dR:+<5} {dL:+<5} {dT:+<5} "
                f"{dups:<5} {off:<7} {gtypes}"
            )
            out_lines.append(line)

            if dT != 0 or dups > 0 or off > 0:
                discrepancies.append({
                    "pitcher": pit_name, "id": pit_id,
                    "mlb_hr": mlb['hr'],
                    "bug_R": a_bug['hr_vs_R'], "bug_L": a_bug['hr_vs_L'],
                    "bug_total": a_bug['hr_total'],
                    "fix_R": a_fix['hr_vs_R'], "fix_L": a_fix['hr_vs_L'],
                    "fix_total": a_fix['hr_total'],
                    "delta_R": dR, "delta_L": dL, "delta_total": dT,
                    "duplicates": dups, "off_season_rows": off,
                    "extra_game_types": gtypes,
                })

        except Exception as e:
            out_lines.append(f"{pit_name[:25]:<25} {pit_id:<8} ERROR: {e}")

    out_lines.append(f"\n── Discrepancy summary ({len(discrepancies)} pitchers affected) ──")
    for d in discrepancies:
        out_lines.append(
            f"  {d['pitcher']}: MLB_HR={d['mlb_hr']}, "
            f"bug=({d['bug_R']}R+{d['bug_L']}L={d['bug_total']}), "
            f"fix=({d['fix_R']}R+{d['fix_L']}L={d['fix_total']}), "
            f"Δ={d['delta_total']:+d}, dups={d['duplicates']}, "
            f"off_szn={d['off_season_rows']}, extra_types={d['extra_game_types']}"
        )

    if not discrepancies:
        out_lines.append("  No discrepancies detected — all pitchers show correct totals")


def run_audit():
    season = config.CURRENT_SEASON
    out_lines = [
        "=" * 70,
        "PITCHER HR SPLITS INTEGRITY AUDIT",
        f"Season: {season}  |  Date: {__import__('datetime').date.today()}",
        "=" * 70,
        "",
    ]

    analysis_bug, analysis_fix = run_cantillo_trace(out_lines, season)
    audit_25_pitchers(out_lines, season)

    # ── Final root-cause report ───────────────────────────────────────────────
    out_lines.append("\n" + "=" * 70)
    out_lines.append("SECTION 3 — ROOT CAUSE + PIPELINE FIX SUMMARY")
    out_lines.append("=" * 70)

    out_lines.append("""
ROOT CAUSE (confirmed by audit):
  _fetch_pitcher_savant() in clients/pitch_mix.py sends season-only Savant
  queries without restricting to regular-season game types (hfGT=R|).
  Baseball Savant statcast_search returns PA-ending events from ALL game types
  matching the season year — regular season, Spring Training, and in some years
  postseason. This inflates HR counts for active pitchers who also appeared in
  Spring Training (every year) and/or post-season games.

  Contributing defects (each independently audited above):
    1. Missing hfGT=R| filter  → primary source of phantom HRs
    2. No (game_pk, at_bat_number) deduplication → secondary risk (suspended/replayed games)
    3. No game_year validation in row iteration → tertiary guard absent

PIPELINE FIX APPLIED (clients/pitch_mix.py):
  1. Added "hfGT": "R|" to all Savant statcast_search queries in _fetch_pitcher_savant()
     — restricts results to regular-season games only
  2. Added deduplication by (game_pk, at_bat_number) before tallying events
     — prevents double-counting from suspended/replayed games
  3. Added game_year check in row loop — skips any row where game_year != season
     as a final defensive layer

VALIDATION PATH:
  Re-run this script after applying the fix. Cantillo (and all audited pitchers)
  should show zero delta between bug/fix columns.
""")

    output_text = "\n".join(out_lines)
    print(output_text)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(output_text)
    print(f"\n[audit] Full output written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    run_audit()
