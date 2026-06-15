"""
CEILING threshold sweep — read-only analysis.
Operator authorized n<200 override for threshold exploration.
Run from inside mlb_hr_engine_v4/:
    python scripts/analysis/ceiling_sweep.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import config
from pipeline import load_game_data
from roles import classify_role, _parse_pct, _parse_float

# ── helpers ──────────────────────────────────────────────────────────────────

def check_ceiling(row, max_ev_thresh, barrel_thresh, blast_thresh, pull_air_thresh):
    barrel   = _parse_pct(row.get("barrel_pct"))
    max_ev   = _parse_float(row.get("max_ev"))
    blast    = _parse_float(row.get("blast"))
    pull_air = _parse_float(row.get("pull_air_pct"))
    if max_ev is None or barrel is None:
        return False
    if max_ev < max_ev_thresh or barrel < barrel_thresh:
        return False
    blast_pass    = blast    is not None and blast    >= blast_thresh
    pull_air_pass = pull_air is not None and pull_air >= pull_air_thresh
    return blast_pass or pull_air_pass

def check_foundation(row, tier):
    roles = classify_role(row, tier=tier)
    return roles["foundation"]

def get_tier(row):
    prob = _parse_float(row.get("model_prob")) or 0.0
    if prob >= 0.28:   return "APEX"
    if prob >= 0.22:   return "ELITE"
    if prob >= 0.16:   return "STRONG"
    if prob >= 0.10:   return "MODERATE"
    return "VALUE"

# ── load slate ────────────────────────────────────────────────────────────────

print("Loading pipeline ...")
result = load_game_data()
rows = result.get("all_players") or result.get("all_by_model") or []
print(f"Slate: {len(rows)} players\n")

# ── CURRENT state ─────────────────────────────────────────────────────────────

current_ceiling = []
current_foundation = []
for r in rows:
    tier = get_tier(r)
    roles = classify_role(r, tier=tier)
    name = r.get("name") or r.get("batter") or r.get("player_name") or "?"
    if roles["ceiling"]:
        current_ceiling.append((name, roles["foundation"]))
    if roles["foundation"]:
        current_foundation.append(name)

print("=" * 60)
print("CURRENT STATE (maxEV>=115, barrel>=9, blast>=15 OR pullair>=25)")
print(f"  CEILING count : {len(current_ceiling)}")
overlap = [(n, f) for n, f in current_ceiling if f]
distinct = [(n, f) for n, f in current_ceiling if not f]
print(f"  Also FOUNDATION (overlap) : {len(overlap)}")
for n, _ in overlap:
    print(f"    [CEIL+FOUND] {n}")
print(f"  CEILING only (distinct)   : {len(distinct)}")
for n, _ in distinct:
    print(f"    [CEIL only ] {n}")
print()

# ── SWEEP ─────────────────────────────────────────────────────────────────────

max_ev_vals   = [113, 114, 115]
barrel_vals   = [8.0, 8.5, 9.0]
pull_air_vals = [18, 20, 22, 25]
blast_vals    = [12, 13, 15]

print("=" * 60)
print("SWEEP TABLE")
print(f"{'maxEV':>6} {'brl':>5} {'pa':>4} {'bst':>4} | {'CEIL':>5} {'DIST':>5} {'OVL':>5}")
print("-" * 42)

results_for_combos = []

for mev in max_ev_vals:
    for brl in barrel_vals:
        for pa in pull_air_vals:
            for bst in blast_vals:
                ceiling_rows = []
                for r in rows:
                    tier = get_tier(r)
                    found = check_foundation(r, tier)
                    ceil  = check_ceiling(r, mev, brl, bst, pa)
                    name  = r.get("name") or r.get("batter") or r.get("player_name") or "?"
                    if ceil:
                        ceiling_rows.append((name, found))
                total = len(ceiling_rows)
                overlap_n = sum(1 for _, f in ceiling_rows if f)
                distinct_n = total - overlap_n
                print(f"{mev:>6} {brl:>5} {pa:>4} {bst:>4} | {total:>5} {distinct_n:>5} {overlap_n:>5}")
                results_for_combos.append((mev, brl, pa, bst, total, distinct_n, overlap_n, ceiling_rows))

# ── PROMISING COMBOS ─────────────────────────────────────────────────────────

print()
print("=" * 60)
print("PROMISING COMBOS (target: 10-20 CEILING, healthy distinct share)")
print()

# Filter for combos in target range with decent distinct ratio
candidates = [
    x for x in results_for_combos
    if 8 <= x[4] <= 25 and x[5] >= 3
]
# Sort by: closest to 15 total, then most distinct
candidates.sort(key=lambda x: (abs(x[4] - 15), -x[5]))

shown = 0
for mev, brl, pa, bst, total, dist_n, ovl_n, ceiling_rows in candidates[:5]:
    if shown >= 3:
        break
    shown += 1
    print(f"  maxEV≥{mev}, barrel≥{brl}, pullair≥{pa}, blast≥{bst}")
    print(f"  CEILING={total}  distinct={dist_n}  overlap={ovl_n}")
    for name, found in ceiling_rows:
        tag = "[CEIL+FOUND]" if found else "[CEIL only ]"
        print(f"    {tag} {name}")
    print()
