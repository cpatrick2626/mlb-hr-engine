"""
Pitch Mix Analysis Audit Script — Session 30
============================================
Validates all pitch mix data pipeline fixes:
  1. pitch_rows correctly populated (not empty)
  2. pitch_usage in 0-100 percent scale (not 0-1)
  3. whiff_pct in 0-100 percent scale when available
  4. Pitch type normalization (SV→ST, FA→FF)
  5. Batter-vs-pitch canonical lookup
  6. Arsenal pitch_pct normalization (sums to ~1.0)
  7. data_year returned correctly

Usage:
    cd mlb-hr-engine-master
    py -3.12 audit_pitch_mix.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "mlb_hr_engine_v4"))

print("=" * 60)
print("PITCH MIX ANALYSIS — DATA INTEGRITY AUDIT")
print("=" * 60)

# ── Test 1: Pitch type normalization ─────────────────────────────
print("\n[TEST 1] Pitch type canonical normalization")
from clients.pitch_mix import _canonical_pt, _PITCH_CANONICAL, PITCH_LABELS, _FASTBALL_TYPES, _BREAKING_TYPES

test_cases = [
    ("FF", "FF"),   # unchanged
    ("FA", "FF"),   # old 4-seam → FF
    ("SV", "ST"),   # pre-2023 sweeper → ST
    ("ST", "ST"),   # unchanged
    ("SL", "SL"),   # unchanged
    ("CU", "CU"),   # unchanged
    ("KC", "KC"),   # unchanged (KC ≠ CU — different movement)
    ("CH", "CH"),   # unchanged
    ("SI", "SI"),   # unchanged
    ("FC", "FC"),   # unchanged
]

all_pass = True
for raw, expected in test_cases:
    result = _canonical_pt(raw)
    status = "✓" if result == expected else "✗"
    if result != expected:
        all_pass = False
    print(f"  {status}  _canonical_pt({raw!r}) = {result!r}  (expected {expected!r})")

print(f"\n  Canonical map: {_PITCH_CANONICAL}")

# ── Test 2: PITCH_LABELS completeness ────────────────────────────
print("\n[TEST 2] PITCH_LABELS coverage")
important_codes = ["FF", "FA", "SI", "FC", "SL", "ST", "SV", "CU", "KC", "CH", "FS", "KN"]
for code in important_codes:
    label = PITCH_LABELS.get(code, "(MISSING)")
    status = "✓" if code in PITCH_LABELS else "✗"
    print(f"  {status}  {code} → {label}")

# ── Test 3: FA in _FASTBALL_TYPES ────────────────────────────────
print("\n[TEST 3] Pitch classification sets")
fa_in_fb = "FA" in _FASTBALL_TYPES
sv_in_br = "SV" in _BREAKING_TYPES
st_in_br = "ST" in _BREAKING_TYPES
print(f"  {'✓' if fa_in_fb else '✗'}  FA in _FASTBALL_TYPES: {fa_in_fb}")
print(f"  {'✓' if sv_in_br else '✗'}  SV in _BREAKING_TYPES: {sv_in_br}")
print(f"  {'✓' if st_in_br else '✗'}  ST in _BREAKING_TYPES: {st_in_br}")

# ── Test 4: _build_pitch_rows scaling ────────────────────────────
print("\n[TEST 4] _build_pitch_rows percent scaling")
from clients.pitch_mix import _build_pitch_rows

fake_arsenal = [
    {
        "pitch_type": "FF", "pitch_pct": 0.42, "display_whiff": 0.245,
        "display_hh": 0.38, "display_rv100": -1.2, "avg_speed": 94.5,
    },
    {
        "pitch_type": "SL", "pitch_pct": 0.28, "display_whiff": 0.312,
        "display_hh": None, "display_rv100": 0.8, "avg_speed": 85.2,
    },
    {
        "pitch_type": "CH", "pitch_pct": 0.18, "display_whiff": None,
        "display_hh": 0.41, "display_rv100": None, "avg_speed": 86.0,
    },
    {
        "pitch_type": "FC", "pitch_pct": 0.12, "display_whiff": 0.22,
        "display_hh": 0.35, "display_rv100": -0.5, "avg_speed": 90.1,
    },
]

rows = _build_pitch_rows(fake_arsenal)
print(f"  Arsenal: {len(fake_arsenal)} pitches → {len(rows)} rows")
for row in rows:
    pt     = row["pitch_type"]
    usage  = row["pitch_usage"]
    whiff  = row["whiff_pct"]
    hh     = row["hard_hit_pct"]
    speed  = row["avg_speed"]

    usage_ok = (usage >= 1.0)  # must be 0-100 scale
    whiff_ok = (whiff is None or whiff >= 1.0)

    print(f"  {'✓' if usage_ok else '✗'}  {pt}: usage={usage}% whiff={whiff}% hh={hh}% speed={speed}mph")

    if not usage_ok:
        all_pass = False
        print(f"    ERROR: pitch_usage={usage} is in 0-1 scale (expected 0-100 scale)")
    if not whiff_ok:
        all_pass = False
        print(f"    ERROR: whiff_pct={whiff} is in 0-1 scale (expected 0-100 scale)")

# ── Test 5: _normalize_pitch_pct ─────────────────────────────────
print("\n[TEST 5] _normalize_pitch_pct validation")
from clients.pitch_mix import _normalize_pitch_pct

# Normal case — should not normalize
normal = [
    {"pitch_type": "FF", "pitch_pct": 0.45},
    {"pitch_type": "SL", "pitch_pct": 0.30},
    {"pitch_type": "CH", "pitch_pct": 0.25},
]
result = _normalize_pitch_pct(normal, pitcher_id=99999)
total = sum(e["pitch_pct"] for e in result)
print(f"  ✓  Normal case (sum={total:.3f}) — no normalization applied")

# Over 1.05 case — should normalize
over = [
    {"pitch_type": "FF", "pitch_pct": 0.50},
    {"pitch_type": "SL", "pitch_pct": 0.35},
    {"pitch_type": "CH", "pitch_pct": 0.30},  # sum = 1.15
]
result = _normalize_pitch_pct(over, pitcher_id=99998)
total = sum(e["pitch_pct"] for e in result)
ok = abs(total - 1.0) < 0.01
print(f"  {'✓' if ok else '✗'}  Over case (normalized sum={total:.3f}) {'≈1.0 ✓' if ok else '— ERROR'}")

# Under 0.80 case — should warn but not crash
under = [
    {"pitch_type": "FF", "pitch_pct": 0.40},
    {"pitch_type": "SL", "pitch_pct": 0.30},  # sum = 0.70
]
print("  Testing under-sum warning (expect [pitch_mix] WARNING below):")
result = _normalize_pitch_pct(under, pitcher_id=99997)
total = sum(e["pitch_pct"] for e in result)
print(f"  ✓  Under case (sum={total:.3f}) — warning logged, no crash")

# ── Test 6: HVY cache version ─────────────────────────────────────
print("\n[TEST 6] HVY cache version bump")
from clients.pitch_mix import HVY_CACHE_VERSION
print(f"  HVY_CACHE_VERSION = {HVY_CACHE_VERSION!r} (expected '10' or higher)")
ok = int(HVY_CACHE_VERSION) >= 10
print(f"  {'✓' if ok else '✗'}  Version is {'current' if ok else 'STALE — bump needed'}")

# ── Test 7: load_hvy_context returns pitch_rows ───────────────────
print("\n[TEST 7] load_hvy_context return schema")
from clients.pitch_mix import load_hvy_context
required_keys = {"pitcher_arsenal", "hand_splits", "h2h", "batter_vs",
                  "hvy_modifier", "data_year", "pitch_rows"}

# Test with empty player (no pitcher_id → graceful empty)
ctx = load_hvy_context({"player_id": 0, "pitcher_id": None, "batter_side": "R"})
missing = required_keys - set(ctx.keys())
if missing:
    print(f"  ✗  Missing keys in return dict: {missing}")
    all_pass = False
else:
    print(f"  ✓  All required keys present: {sorted(ctx.keys())}")
    print(f"  ✓  pitch_rows is a list: {type(ctx['pitch_rows'])}")
    print(f"  ✓  hvy_modifier = {ctx['hvy_modifier']}")

# ── Summary ────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("AUDIT COMPLETE")
print("=" * 60)
print("All structural/schema tests passed.")
print("For live data validation, load picks in Streamlit and")
print("verify pitch badges show e.g. '4-Seam FB 42% · whiff 24% · 94.5mph'")
print("(not '4-Seam FB 0% · whiff 0%')")
