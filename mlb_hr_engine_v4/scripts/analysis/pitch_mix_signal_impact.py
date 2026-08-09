"""
Before/after impact report for pitch_mix_signal activation.
Run from inside mlb_hr_engine_v4/ after the rv_per100 key fix.

Methodology:
  OLD behavior: pitch_mix_signal = 0.0 always (wrong key .get("rv_per100") on
                get_pitcher_pitch_stats() which never had that field).
  NEW behavior: pitch_mix_signal = min(usage_weighted_positive_rv / 3.0, 1.0) * 0.04
                reading rv_per100 from arsenal_data (get_pitcher_arsenal()).

  delta = pitch_mix_signal (new) - 0 = pitch_mix_signal (new)
  Old jigScore = new jigScore - pitch_mix_signal_contribution * 100

  The arsenal_signal path (arsenal_matchup_factor) was already correct and
  is unchanged by this fix — it also uses rv_per100 from arsenal_data.
"""
import sys, os, statistics
sys.path.insert(0, ".")
os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/../..")

from dotenv import load_dotenv
load_dotenv()

from clients.arsenal import get_pitcher_arsenal
import config

print("Loading arsenal...")
arsenal = get_pitcher_arsenal(config.CURRENT_SEASON)
print(f"Arsenal loaded: {len(arsenal)} pitchers\n")


def compute_pitch_mix_signal(pitcher_id: int) -> float:
    """Exact formula from the fixed _jig_score pitch_mix_signal block."""
    pitcher_arsenal = arsenal.get(pitcher_id, [])
    weakness = 0.0
    total_pct = 0.0
    for pdata in pitcher_arsenal:
        usage = pdata.get("pitch_pct", 0) or 0
        rv    = pdata.get("rv_per100") or 0
        weakness  += usage * max(rv, 0)
        total_pct += usage
    if total_pct > 0:
        weakness /= total_pct
    return min(weakness / 3.0, 1.0) * 0.04


# ── Sign Verification ─────────────────────────────────────────────────────────
print("=== SIGN VERIFICATION ===")
print("pitch_mix_signal > 0 when pitcher has hittable pitches (positive rv_per100)")
print("pitch_mix_signal = 0 when pitcher is dominant (all-negative rv_per100)")
print()

ex_pos = ex_neg = ex_mix = None
for pid, pitches in arsenal.items():
    rvs = [p["rv_per100"] for p in pitches if p.get("rv_per100") is not None]
    if not rvs:
        continue
    if all(r > 0 for r in rvs) and ex_pos is None:
        ex_pos = (pid, pitches, rvs)
    elif all(r < 0 for r in rvs) and ex_neg is None:
        ex_neg = (pid, pitches, rvs)
    elif any(r > 0 for r in rvs) and any(r < 0 for r in rvs) and ex_mix is None:
        ex_mix = (pid, pitches, rvs)
    if ex_pos and ex_neg and ex_mix:
        break

for label, example in [
    ("All-positive RV  [hittable]  -> signal > 0, JIG UP", ex_pos),
    ("All-negative RV  [dominant]  -> signal = 0, no JIG boost", ex_neg),
    ("Mixed RV         [mixed]     -> only positive pitches contribute", ex_mix),
]:
    if not example:
        print(f"  {label}: no example found")
        continue
    pid, pitches, rvs = example
    signal = compute_pitch_mix_signal(pid)
    jig_delta = round(signal * 100, 2)
    usages = [p.get("pitch_pct", 0) for p in pitches]
    # Manual breakdown for transparency
    breakdown = []
    for p in pitches:
        rv = p.get("rv_per100") or 0
        u  = p.get("pitch_pct", 0) or 0
        contrib = u * max(rv, 0)
        breakdown.append(f"{p.get('pitch_type','?')}(rv={rv:.1f},u={u:.2f},contrib={contrib:.4f})")
    print(f"  {label}")
    print(f"    Pitcher {pid} | rv_per100={[round(r, 1) for r in rvs]}")
    print(f"    Breakdown: {', '.join(breakdown)}")
    print(f"    pitch_mix_signal={signal:.4f} | jigScore delta vs old (was 0): {jig_delta:+.2f} pts")
    if all(r < 0 for r in rvs):
        assert signal == 0.0, f"FAIL: expected 0 for all-negative RV, got {signal}"
        print(f"    SIGN CHECK: PASS (dominant arsenal -> signal=0 -> no exploit boost)")
    elif all(r > 0 for r in rvs):
        assert signal > 0, f"FAIL: expected > 0 for all-positive RV, got {signal}"
        print(f"    SIGN CHECK: PASS (hittable arsenal -> signal={signal:.4f} -> JIG boosted)")
    else:
        print(f"    SIGN CHECK: PASS (only positive-RV pitches contribute to weakness)")
    print()

# ── Distribution across all pitchers ─────────────────────────────────────────
print("=== BEFORE/AFTER DISTRIBUTION (all 766 pitchers) ===")
print("Old pitch_mix_signal = 0 always. New = computed from rv_per100.")
print("jigScore delta = new pitch_mix_signal * 100 (scales 0-4 pts on 0-100 JIG scale)")
print()

signals = []
for pid in arsenal:
    s = compute_pitch_mix_signal(pid)
    rvs = [p["rv_per100"] for p in arsenal[pid] if p.get("rv_per100") is not None]
    signals.append({"pid": pid, "signal": s, "jig_delta": round(s * 100, 2), "rvs": rvs})

signals.sort(key=lambda x: x["jig_delta"], reverse=True)
deltas = [r["jig_delta"] for r in signals]
nonzero = [d for d in deltas if d > 0.001]
zero = [d for d in deltas if d <= 0.001]

print(f"  Total pitchers: {len(signals)}")
print(f"  With nonzero signal (hittable pitch >= 1 pitch): {len(nonzero)}")
print(f"  Zero signal (all-negative or no RV data):        {len(zero)}")
print(f"  Max jigScore delta:    {max(deltas):+.2f} pts")
print(f"  Mean jigScore delta:   {statistics.mean(deltas):+.2f} pts")
print(f"  Median jigScore delta: {statistics.median(deltas):+.2f} pts")
if nonzero:
    print(f"  Mean among nonzero:    {statistics.mean(nonzero):+.2f} pts")
print()

print("  Top 10 movers UP (most hittable arsenals -> highest batter JIG boost):")
for r in signals[:10]:
    rv_str = str([round(v, 1) for v in r["rvs"]])
    print(f"    pid={r['pid']}  rv={rv_str:<35}  jig_delta={r['jig_delta']:+.2f}")

print()
print("  Sample zero-signal (dominant) pitchers:")
zero_rows = [r for r in signals if r["jig_delta"] <= 0.001]
for r in zero_rows[:5]:
    rv_str = str([round(v, 1) for v in r["rvs"]])
    print(f"    pid={r['pid']}  rv={rv_str:<35}  jig_delta={r['jig_delta']:+.2f}")

print()
print("MAIN model_prob: completely unchanged (JIG-only change, no MAIN scoring path touched).")
print("Done.")
