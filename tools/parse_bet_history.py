#!/usr/bin/env python3
"""
Parse FanDuel bet-history export → structured deployed-picks dataset.

Input:  Downloads/baseball_only_bet_history.txt  (DO NOT commit - account data)

Output (in tools/):
  deployed_picks_from_fd.csv   - one row per leg
  deployed_bets_summary_from_fd.csv - one row per bet

Usage:
  python tools/parse_bet_history.py [path/to/export.txt]
"""
import csv
import re
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_INPUT = Path(r"C:\Users\ChrisPatrick\Downloads\baseball_only_bet_history.txt")
OUT_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------
TEAM_AT_RE = re.compile(r'^(.+\([^)]+\))\s+@\s+(.+\([^)]+\))\s*$')
TEAM_SINGLE_RE = re.compile(r'^[A-Za-z].{2,}\([A-Za-z][^)]{1,30}\)\s*$')
PITCHER_RE = re.compile(r'^(.*?)\s*\(([^)]+)\)\s*$')
ODDS_RE = re.compile(r'^[+-]\d+$')
MONEY_RE = re.compile(r'^\$(\d+\.\d+)$')
PLACED_RE = re.compile(r'^PLACED:\s*(.+)$')
DATE_LINE_RE = re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+,')

KNOWN_NON_TEAM = {
    "Same Game Parlay™", "Same Game Parlay+", "Finished",
    "Open", "Settled", "Void", "TOTAL WAGER", "RETURNED",
}
NON_TEAM_PREFIXES = ("$", "Includes:", "BET ID:", "PLACED:", "bet reset")
NON_TEAM_DIGIT_START = frozenset("0123456789")


def is_odds(s: str) -> bool:
    return bool(ODDS_RE.match(s))


def is_date_line(s: str) -> bool:
    return bool(DATE_LINE_RE.match(s))


def is_team_line(s: str) -> bool:
    if not s:
        return False
    if s[0] in NON_TEAM_DIGIT_START or s.startswith("$"):
        return False
    if s in KNOWN_NON_TEAM:
        return False
    if any(s.startswith(p) for p in NON_TEAM_PREFIXES):
        return False
    if "parlay" in s.lower() and "(" not in s:
        return False
    if is_date_line(s):
        return False
    if "(" not in s:
        return False
    return bool(TEAM_AT_RE.match(s) or TEAM_SINGLE_RE.match(s))


def split_team_pitcher(s: str) -> tuple[str, str]:
    m = PITCHER_RE.match(s.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return s.strip(), ""


def extract_teams(block_lines: list[str]) -> tuple[str, str, str, str] | None:
    """Return (team1, pitcher1, team2, pitcher2) or None."""
    pairs: list[tuple[str, str]] = []
    for line in block_lines:
        s = line.strip()
        at_m = TEAM_AT_RE.match(s)
        if at_m:
            t1, p1 = split_team_pitcher(at_m.group(1))
            t2, p2 = split_team_pitcher(at_m.group(2))
            return t1, p1, t2, p2
        if is_team_line(s):
            t, p = split_team_pitcher(s)
            pairs.append((t, p))
            if len(pairs) == 2:
                return pairs[0][0], pairs[0][1], pairs[1][0], pairs[1][1]
    if len(pairs) == 1:
        return pairs[0][0], pairs[0][1], "", ""
    return None


def parse_placed(s: str) -> tuple[str, str]:
    """'PLACED: M/D/YYYY H:MMAM/PM ET' → (date_str YYYY-MM-DD, datetime_str YYYY-MM-DD HH:MM)"""
    s = s.strip()
    if s.upper().startswith("PLACED:"):
        s = s[7:].strip()
    if s.upper().endswith(" ET"):
        s = s[:-3].strip()
    for fmt in ("%m/%d/%Y %I:%M%p", "%m/%d/%Y %I:%M %p"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d"), dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pass
    return s, s


# ---------------------------------------------------------------------------
# Split file into per-bet blocks
# ---------------------------------------------------------------------------
def split_bets(text: str) -> list[list[str]]:
    """Split file into bet blocks. Each block ends at the PLACED: line."""
    lines = text.splitlines()
    # strip each line for clean comparison, but keep originals for output
    placed_idx = [i for i, l in enumerate(lines) if l.strip().upper().startswith("PLACED:")]
    blocks = []
    prev = 0
    for pi in placed_idx:
        blocks.append([l.strip() for l in lines[prev: pi + 1]])
        prev = pi + 1
    return blocks


# ---------------------------------------------------------------------------
# Split block into blank-line-delimited sub-blocks
# ---------------------------------------------------------------------------
def to_sub_blocks(lines: list[str]) -> list[list[str]]:
    """Split lines on blank lines → list of non-empty sub-blocks."""
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if not line:
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(line)
    if current:
        blocks.append(current)
    return blocks


# ---------------------------------------------------------------------------
# Parse a single bet block
# ---------------------------------------------------------------------------
BET_TYPE_RE = re.compile(
    r'^(\d+ leg (?:Same Game Parlay\+|parlay)|Same Game Parlay[™+])',
    re.IGNORECASE
)

STATUS_TOKENS = {"Open", "Settled", "Void"}


def parse_bet(block_lines: list[str]) -> dict | None:
    if not block_lines:
        return None

    # --- Footer: last 6 lines ---
    if len(block_lines) < 6:
        return None

    placed_line = block_lines[-1]
    bet_id_line = block_lines[-2]
    # [-3] = "RETURNED", [-4] = $ returned, [-5] = "TOTAL WAGER", [-6] = $ stake

    if not placed_line.upper().startswith("PLACED:"):
        return None
    if not bet_id_line.upper().startswith("BET ID:"):
        return None

    try:
        stake = float(block_lines[-6].lstrip("$"))
        returned = float(block_lines[-4].lstrip("$"))
    except (ValueError, IndexError):
        stake = 0.0
        returned = 0.0

    bet_id = bet_id_line[7:].strip()
    placed_date, placed_dt = parse_placed(placed_line)

    body = block_lines[:-6]  # everything before footer

    # --- Header scan: bet type, parlay odds, optional status ---
    bet_type = ""
    parlay_odds = ""
    bet_status = "Settled"  # default assumption

    # Scan top of body for status and bet type
    header_idx = 0
    statuses_seen = []
    for i, line in enumerate(body):
        if not line:
            continue
        if line in STATUS_TOKENS:
            statuses_seen.append(line)
            header_idx = i + 1
            continue
        if BET_TYPE_RE.match(line):
            bet_type = line
            header_idx = i + 1
            break
        # Unrecognised header noise — skip
        header_idx = i + 1

    if statuses_seen:
        bet_status = statuses_seen[-1]

    if header_idx < len(body) and is_odds(body[header_idx]):
        parlay_odds = body[header_idx]
        header_idx += 1

    body_rest = body[header_idx:]

    # --- Sub-block parse ---
    sub_blocks = to_sub_blocks(body_rest)

    legs = []
    fallback_teams: tuple[str, str, str, str] | None = None

    for sb in sub_blocks:
        has_hr = "To Hit A Home Run" in sb
        if not has_hr:
            # Header / sub-parlay descriptor block → extract team info
            teams = extract_teams(sb)
            if teams:
                fallback_teams = teams
            continue

        # --- Leg block ---
        hr_pos = sb.index("To Hit A Home Run")

        # Player name: scan backward, skip odds / "Void"
        player_name = ""
        is_void_pre = False
        player_odds = ""
        for j in range(hr_pos - 1, -1, -1):
            token = sb[j]
            if not token:
                continue
            if token == "Void":
                is_void_pre = True
                continue
            if is_odds(token):
                player_odds = token
                continue
            if token in STATUS_TOKENS or token == "Finished":
                break
            # First real non-special line is the player name
            player_name = token
            break

        # Void check: also "Void" immediately after "To Hit A Home Run"
        is_void_post = (
            hr_pos + 1 < len(sb) and sb[hr_pos + 1] == "Void"
        )
        is_void = is_void_pre or is_void_post

        # Result
        if is_void:
            leg_result = "void"
        else:
            # First token after "To Hit A Home Run" (skip "Void" handled above)
            j = hr_pos + 1
            leg_result = "open"
            while j < len(sb):
                token = sb[j]
                if token == "Void":
                    leg_result = "void"
                    break
                if token.isdigit():
                    leg_result = "hit" if int(token) >= 1 else "miss"
                    break
                if token:
                    # Non-digit, non-blank after HR → no result recorded (open bet)
                    break
                j += 1

        # Team info: check leg block first, then fallback
        teams = extract_teams(sb)
        if not teams:
            teams = fallback_teams

        if teams:
            team1, pitcher1, team2, pitcher2 = teams
        else:
            team1 = pitcher1 = team2 = pitcher2 = ""

        legs.append({
            "player_name": player_name,
            "team1": team1,
            "pitcher1": pitcher1,
            "team2": team2,
            "pitcher2": pitcher2,
            "player_odds": player_odds,
            "leg_result": leg_result,
        })

    return {
        "bet_id": bet_id,
        "placed_date": placed_date,
        "placed_datetime": placed_dt,
        "bet_type": bet_type,
        "parlay_odds": parlay_odds,
        "stake": stake,
        "returned": returned,
        "bet_status": bet_status,
        "legs": legs,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}")
        sys.exit(1)

    text = input_path.read_text(encoding="utf-8")

    # Quick sanity counts from raw text
    raw_bet_count = text.count("BET ID:")
    raw_hr_total = text.count("To Hit A Home Run")
    # Only standalone "To Hit A Home Run" lines are actual legs;
    # player-list header lines (e.g. "X To Hit A Home Run, Y ...") inflate the raw count.
    raw_hr_standalone = sum(
        1 for l in text.splitlines() if l.strip() == "To Hit A Home Run"
    )
    print(f"Raw file: {raw_bet_count} BET IDs")
    print(f"  'To Hit A Home Run' total occurrences: {raw_hr_total}")
    print(f"  Standalone HR lines (actual legs):     {raw_hr_standalone}")
    print(f"  Player-list header occurrences:        {raw_hr_total - raw_hr_standalone}")

    # Split and parse
    bet_blocks = split_bets(text)
    print(f"Blocks split: {len(bet_blocks)}")

    all_bets = []
    all_legs = []
    warnings = []

    for raw in bet_blocks:
        bet = parse_bet(raw)
        if bet is None:
            warnings.append(f"SKIP: could not parse block ending with {raw[-1] if raw else '?'}")
            continue

        n_legs = len(bet["legs"])

        # Validate: player list cross-check (if bet has a player-list line)
        player_list_players = 0
        for sb in to_sub_blocks([l for l in raw[:-6] if l]):
            for line in sb:
                if "To Hit A Home Run" in line and "," in line:
                    # This is a player list line like "X To Hit A Home Run, Y ..."
                    player_list_players = line.count("To Hit A Home Run")
                    break
        if player_list_players and player_list_players != n_legs:
            warnings.append(
                f"MISMATCH bet {bet['bet_id']}: player_list={player_list_players} legs={n_legs}"
            )

        # Non-HR leg check (should be zero)
        for i, leg in enumerate(bet["legs"]):
            # All legs come from "To Hit A Home Run" lines, so this is a structural check
            pass  # already guaranteed by our parser anchoring on HR lines

        all_bets.append(bet)

        for leg in bet["legs"]:
            all_legs.append({
                "bet_id": bet["bet_id"],
                "placed_date": bet["placed_date"],
                "placed_datetime": bet["placed_datetime"],
                "player_name": leg["player_name"],
                "team1": leg["team1"],
                "pitcher1": leg["pitcher1"],
                "team2": leg["team2"],
                "pitcher2": leg["pitcher2"],
                "parlay_odds": bet["parlay_odds"],
                "leg_count": n_legs,
                "stake": bet["stake"],
                "returned": bet["returned"],
                "leg_result": leg["leg_result"],
                "bet_status": bet["bet_status"],
                "player_odds": leg["player_odds"],
            })

    # --- Validation report ---
    total_legs = len(all_legs)
    hit_count = sum(1 for l in all_legs if l["leg_result"] == "hit")
    miss_count = sum(1 for l in all_legs if l["leg_result"] == "miss")
    void_count = sum(1 for l in all_legs if l["leg_result"] == "void")
    open_count = sum(1 for l in all_legs if l["leg_result"] == "open")

    total_staked = sum(b["stake"] for b in all_bets)
    total_returned = sum(b["returned"] for b in all_bets)
    net = total_returned - total_staked

    # Bets with per-leg results (Jun 18 only — earlier dates have no digit results in export)
    bets_with_results = sum(
        1 for b in all_bets
        if any(l["leg_result"] in ("hit", "miss") for l in b["legs"])
    )

    print("\n=== VALIDATION ===")
    print(f"Bets parsed:       {len(all_bets)}  (expected {raw_bet_count})")
    print(f"Legs parsed:       {total_legs}  (expected {raw_hr_standalone} standalone HR lines)")
    print(f"Bets w/ per-leg results: {bets_with_results}  (Jun 18 export; earlier dates no digit result)")
    print(f"Leg results:       hit={hit_count}  miss={miss_count}  void={void_count}  open/unknown={open_count}")
    print(f"  NOTE: 'open' = no result digit in export (Jun 17 and earlier bets)")
    print(f"Total staked:      ${total_staked:.2f}")
    print(f"Total returned:    ${total_returned:.2f}")
    print(f"Net:               ${net:.2f}  ({'LOSS' if net < 0 else 'GAIN'})")

    # Missing player names
    missing_name = [l for l in all_legs if not l["player_name"]]
    if missing_name:
        print(f"\nWARNING: {len(missing_name)} legs with missing player name")
        for l in missing_name[:5]:
            print(f"  bet_id={l['bet_id']} result={l['leg_result']}")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings[:20]:
            print(f"  {w}")

    bets_ok = len(all_bets) == raw_bet_count
    legs_ok = total_legs == raw_hr_standalone
    print(f"\nBet count match:   {'OK' if bets_ok else 'FAIL'}")
    print(f"Leg count match:   {'OK' if legs_ok else 'FAIL'}")
    print(f"Net is negative:   {'OK' if net < 0 else 'WARNING — net is positive, verify parse'}")

    # --- Write CSVs ---
    legs_out = OUT_DIR / "deployed_picks_from_fd.csv"
    bets_out = OUT_DIR / "deployed_bets_summary_from_fd.csv"

    legs_fields = [
        "bet_id", "placed_date", "placed_datetime", "player_name",
        "team1", "pitcher1", "team2", "pitcher2",
        "parlay_odds", "leg_count", "player_odds",
        "stake", "returned", "leg_result", "bet_status",
    ]
    with open(legs_out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=legs_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(all_legs)

    bets_fields = [
        "bet_id", "placed_date", "placed_datetime", "bet_type",
        "parlay_odds", "n_legs", "all_hit", "stake", "returned", "net",
    ]
    with open(bets_out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=bets_fields)
        w.writeheader()
        for bet in all_bets:
            legs = bet["legs"]
            all_hit = all(l["leg_result"] == "hit" for l in legs) if legs else False
            net_bet = bet["returned"] - bet["stake"]
            w.writerow({
                "bet_id": bet["bet_id"],
                "placed_date": bet["placed_date"],
                "placed_datetime": bet["placed_datetime"],
                "bet_type": bet["bet_type"],
                "parlay_odds": bet["parlay_odds"],
                "n_legs": len(legs),
                "all_hit": all_hit,
                "stake": bet["stake"],
                "returned": bet["returned"],
                "net": net_bet,
            })

    print(f"\nWrote: {legs_out}")
    print(f"Wrote: {bets_out}")


if __name__ == "__main__":
    main()
