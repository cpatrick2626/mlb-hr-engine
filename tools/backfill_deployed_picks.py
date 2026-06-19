#!/usr/bin/env python3
"""
backfill_deployed_picks.py  —  Phase 2: Backfill HR outcomes for deployed FD picks.

Input:  tools/deployed_picks_from_fd.csv       (NOT overwritten)
Output: tools/deployed_picks_backfilled.csv    (new file)

Resolution order for player_id (open legs only):
  Pass 1: pick_tracker exact name match
  Pass 2: pick_tracker normalized name (strip accents, lowercase)
  Pass 3: 2026 MLB roster API fallback (normalized)

hr_result encoding:
  hit              = player hit HR that day (API or FD-direct)
  miss             = player played, no HR (API or FD-direct)
  void             = FD-voided leg (preserved, no API lookup)
  unresolved_dnp   = API returned None — date not in game log (DNP / postponed)
  unresolved_error = name not matched to any ID, OR API call threw exception

NEVER: map None/unmatched to "miss".  Missing data is not a negative outcome.

Usage:
  python tools/backfill_deployed_picks.py
"""

import csv
import time
import unicodedata
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT      = Path(__file__).resolve().parent.parent   # → mlb-hr-engine-master/
TOOLS_DIR = ROOT / "tools"
TRACKING  = ROOT / "mlb_hr_engine_v4" / "tracking"

SOURCE   = TOOLS_DIR / "deployed_picks_from_fd.csv"
OUTPUT   = TOOLS_DIR / "deployed_picks_backfilled.csv"
PICK_CSV = TRACKING / "pick_tracker.csv"

# ---------------------------------------------------------------------------
# HTTP session
# ---------------------------------------------------------------------------
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Codex-HR-Engine/backfill"})

MLB_GAMELOG_URL = "https://statsapi.mlb.com/api/v1/people/{pid}/stats"
MLB_ROSTER_URL  = "https://statsapi.mlb.com/api/v1/sports/1/players"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _norm(name: str) -> str:
    """Strip accents, lowercase, strip whitespace.  Acuña → acuna."""
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower().strip()


def _fetch_hr_result(player_id: str, date_str: str) -> bool | None | str:
    """
    Return:
      True      — player hit HR on date_str
      False     — player played, no HR
      None      — date not in game log (DNP / postponed game)
      "error"   — HTTP error or exception (data gap, not negative outcome)
    """
    try:
        r = SESSION.get(
            MLB_GAMELOG_URL.format(pid=player_id),
            params={"stats": "gameLog", "group": "hitting", "season": date_str[:4]},
            timeout=10,
        )
        if r.status_code != 200:
            return "error"
        stats_list = r.json().get("stats", [])
        splits = stats_list[0].get("splits", []) if stats_list else []
        for split in splits:
            if split.get("date") == date_str:
                return int(split.get("stat", {}).get("homeRuns", 0)) > 0
        return None   # date not present → DNP / postponement
    except Exception:
        return "error"


# ---------------------------------------------------------------------------
# Name → player_id maps
# ---------------------------------------------------------------------------

def build_pick_tracker_maps() -> tuple[dict, dict]:
    """Build exact and normalized name→player_id maps from pick_tracker.csv."""
    exact: dict[str, str]  = {}
    normed: dict[str, str] = {}
    if not PICK_CSV.exists():
        print(f"[WARN] pick_tracker.csv not found at {PICK_CSV}")
        return exact, normed
    with open(PICK_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row.get("player_name", "").strip()
            pid  = row.get("player_id", "").strip()
            if name and pid:
                exact[name]        = pid
                normed[_norm(name)] = pid
    print(f"[maps] pick_tracker: {len(exact)} unique names")
    return exact, normed


def fetch_roster_2026() -> dict[str, str]:
    """Fetch all 2026 MLB players → normalized_name → player_id."""
    print("[roster] fetching 2026 MLB roster from Stats API...")
    try:
        r = SESSION.get(MLB_ROSTER_URL, params={"season": "2026"}, timeout=30)
        if r.status_code != 200:
            print(f"[roster] WARN: status {r.status_code}")
            return {}
        people = r.json().get("people", [])
        roster: dict[str, str] = {}
        for p in people:
            full = p.get("fullName", "")
            pid  = str(p.get("id", ""))
            if full and pid:
                roster[_norm(full)] = pid
        print(f"[roster] {len(roster)} players loaded")
        return roster
    except Exception as e:
        print(f"[roster] ERROR: {e}")
        return {}


# Manual ID overrides for names that survive all 3 automated passes.
# Format: FD display name → MLB Stats API player_id string
# C.J. Abrams: period in name (CJ Abrams in API), Jazz Chisholm: Jr. suffix
# Max P. Muncy: disambiguates two same-name players; P. = Athletics Muncy (DOB 2002-08-25)
MANUAL_IDS: dict[str, str] = {
    "C.J. Abrams":   "682928",
    "Jazz Chisholm": "665862",
    "Max P. Muncy":  "691777",
}


def resolve_player_id(
    name: str,
    exact_map: dict,
    norm_map: dict,
    roster_map: dict,
) -> tuple[str | None, str | None]:
    """Returns (player_id, method) — method in 'manual'/'exact'/'normalized'/'roster'/None."""
    if name in MANUAL_IDS:
        return MANUAL_IDS[name], "manual"
    if name in exact_map:
        return exact_map[name], "exact"
    n = _norm(name)
    if n in norm_map:
        return norm_map[n], "normalized"
    if n in roster_map:
        return roster_map[n], "roster"
    return None, None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # --- Load source ---
    with open(SOURCE, newline="", encoding="utf-8") as f:
        source_rows = list(csv.DictReader(f))
    print(f"[source] {len(source_rows)} legs loaded from {SOURCE.name}")

    fd_settled = [r for r in source_rows if r["leg_result"] in ("hit", "miss")]
    voided     = [r for r in source_rows if r["leg_result"] == "void"]
    open_legs  = [r for r in source_rows if r["leg_result"] == "open"]
    print(f"  FD-settled (hit/miss): {len(fd_settled)}")
    print(f"  Voided:                {len(voided)}")
    print(f"  Open (need backfill):  {len(open_legs)}")

    # --- Build pick_tracker maps ---
    exact_map, norm_map = build_pick_tracker_maps()

    # --- Resolve names for open legs ---
    unique_open_names = sorted({r["player_name"] for r in open_legs if r["player_name"]})
    print(f"\n[resolve] {len(unique_open_names)} unique names in open legs")

    pid_map: dict[str, tuple[str | None, str | None]] = {}
    unmatched: list[str] = []
    counts = {"exact": 0, "normalized": 0, "roster": 0, "failed": 0}

    # Pass 1 + 2: pick_tracker maps
    for name in unique_open_names:
        pid, method = resolve_player_id(name, exact_map, norm_map, {})
        if pid:
            pid_map[name] = (pid, method)
            counts[method] += 1
        else:
            unmatched.append(name)

    print(f"  Pass 1 exact:          {counts['exact']}")
    print(f"  Pass 2 normalized:     {counts['normalized']}")
    print(f"  Need roster fallback:  {len(unmatched)}")

    # Pass 3: roster fallback for still-unmatched
    roster_map: dict[str, str] = {}
    if unmatched:
        roster_map = fetch_roster_2026()
        still_failed: list[str] = []
        for name in unmatched:
            pid, method = resolve_player_id(name, {}, {}, roster_map)
            if pid:
                pid_map[name] = (pid, method)
                counts["roster"] += 1
            else:
                pid_map[name] = (None, None)
                counts["failed"] += 1
                still_failed.append(name)
        print(f"  Pass 3 roster:         {counts['roster']}")
        print(f"  Still unmatched:       {counts['failed']}")
        if still_failed:
            print(f"\n  *** Names surviving all 3 passes (need manual ID): ***")
            for n in sorted(still_failed):
                print(f"    '{n}'")

    # --- Batch API lookups for open legs ---
    # Collect unique (player_id, date) pairs — skip unmatched names
    lookup_pairs: set[tuple[str, str]] = set()
    for leg in open_legs:
        pid, _ = pid_map.get(leg["player_name"], (None, None))
        if pid:
            lookup_pairs.add((pid, leg["placed_date"]))

    print(f"\n[api] {len(lookup_pairs)} unique (player_id, date) pairs to fetch")

    api_results: dict[tuple[str, str], bool | None | str] = {}
    for i, (pid, date_str) in enumerate(sorted(lookup_pairs)):
        api_results[(pid, date_str)] = _fetch_hr_result(pid, date_str)
        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(lookup_pairs)} fetched...", flush=True)
        time.sleep(0.05)   # 20 req/s polite rate limit

    print(f"  Done. {len(api_results)} results received")

    # --- Build output rows ---
    out_fields = list(source_rows[0].keys()) + ["hr_result", "player_id_resolved", "match_method"]
    out_rows: list[dict] = []
    stats: dict[str, int] = {
        "hit": 0, "miss": 0, "void": 0,
        "unresolved_dnp": 0, "unresolved_error": 0,
    }

    for row in source_rows:
        out        = dict(row)
        leg_result = row["leg_result"]
        name       = row["player_name"]

        if leg_result == "void":
            out["hr_result"]         = "void"
            out["player_id_resolved"] = ""
            out["match_method"]       = ""
            stats["void"] += 1

        elif leg_result in ("hit", "miss"):
            # FD-direct ground truth (Jun 18 bets with digit results in export)
            out["hr_result"]         = leg_result
            out["player_id_resolved"] = ""
            out["match_method"]       = "fd_direct"
            stats[leg_result] += 1

        else:  # "open" → API backfill
            pid, method = pid_map.get(name, (None, None))
            out["player_id_resolved"] = pid or ""
            out["match_method"]       = method or ""

            if pid is None:
                out["hr_result"] = "unresolved_error"
                stats["unresolved_error"] += 1
            else:
                api = api_results.get((pid, row["placed_date"]))
                if api is True:
                    out["hr_result"] = "hit"
                    stats["hit"] += 1
                elif api is False:
                    out["hr_result"] = "miss"
                    stats["miss"] += 1
                elif api is None:
                    out["hr_result"] = "unresolved_dnp"
                    stats["unresolved_dnp"] += 1
                else:  # "error"
                    out["hr_result"] = "unresolved_error"
                    stats["unresolved_error"] += 1

        out_rows.append(out)

    # --- Consistency check: bet-level vs leg-level (FD-settled bets) ---
    print(f"\n[consistency] checking bet-level outcome vs leg results...")
    # Group by bet_id for rows that have FD leg results
    from collections import defaultdict
    bet_legs: dict[str, list[dict]] = defaultdict(list)
    for r in out_rows:
        if r["leg_result"] in ("hit", "miss", "void"):
            bet_legs[r["bet_id"]].append(r)

    inconsistent: list[str] = []
    for bet_id, legs in bet_legs.items():
        non_void = [l for l in legs if l["hr_result"] != "void"]
        if not non_void:
            continue
        all_hit     = all(l["hr_result"] == "hit" for l in non_void)
        returned    = float(legs[0].get("returned", 0) or 0)
        stake       = float(legs[0].get("stake", 0) or 0)
        # All hit → returned should be > stake; any miss → returned == 0
        any_miss    = any(l["hr_result"] == "miss" for l in non_void)
        if all_hit and returned <= stake:
            inconsistent.append(f"  {bet_id}: all-hit but returned ${returned:.2f} <= stake ${stake:.2f}")
        if any_miss and returned > 0:
            inconsistent.append(f"  {bet_id}: has miss but returned ${returned:.2f} > 0")

    if inconsistent:
        print(f"  INCONSISTENCIES ({len(inconsistent)}):")
        for msg in inconsistent[:10]:
            print(msg)
    else:
        print(f"  OK — {len(bet_legs)} FD-settled bets pass consistency check")

    # --- Write output ---
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_fields)
        w.writeheader()
        w.writerows(out_rows)

    # --- Report ---
    total = len(out_rows)
    resolved = stats["hit"] + stats["miss"] + stats["void"]
    unresolved = stats["unresolved_dnp"] + stats["unresolved_error"]

    print(f"\n{'='*60}")
    print(f"  BACKFILL REPORT")
    print(f"{'='*60}")
    print(f"  Total legs:            {total}")
    print(f"  hit:                   {stats['hit']}")
    print(f"  miss:                  {stats['miss']}")
    print(f"  void:                  {stats['void']}")
    print(f"  unresolved_dnp:        {stats['unresolved_dnp']}")
    print(f"  unresolved_error:      {stats['unresolved_error']}")
    print(f"  -- resolved rate:      {resolved / total * 100:.1f}%")
    print(f"  -- unresolved rate:    {unresolved / total * 100:.1f}%")
    print()
    print(f"  Name resolution (open legs):")
    print(f"    Pass 1 exact:        {counts['exact']}")
    print(f"    Pass 2 normalized:   {counts['normalized']}")
    print(f"    Pass 3 roster:       {counts['roster']}")
    print(f"    Failed all 3:        {counts['failed']}")

    # --- Spot-checks: 5 API-resolved hits ---
    api_hits = [r for r in out_rows if r["hr_result"] == "hit" and r.get("match_method") not in ("fd_direct", "")]
    print(f"\n  SPOT CHECKS — first 5 API-resolved hits:")
    for r in api_hits[:5]:
        print(f"    {r['placed_date']}  {r['player_name']:<25s}  hr_result={r['hr_result']:<20s}  method={r['match_method']}  id={r['player_id_resolved']}")

    # --- Spot-checks: 5 unresolved_error (missing names) ---
    errors = [r for r in out_rows if r["hr_result"] == "unresolved_error" and not r.get("player_id_resolved")]
    if errors:
        seen: set[str] = set()
        print(f"\n  SPOT CHECKS — up to 5 unresolved_error (no ID found):")
        for r in errors:
            if r["player_name"] not in seen:
                print(f"    {r['placed_date']}  '{r['player_name']}'")
                seen.add(r["player_name"])
            if len(seen) >= 5:
                break

    print(f"\nWrote: {OUTPUT}")
    print("DO NOT COMMIT until operator review.")


if __name__ == "__main__":
    main()
