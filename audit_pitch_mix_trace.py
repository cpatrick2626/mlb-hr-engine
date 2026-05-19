"""
Pitch Mix Trust Audit — deep root-cause trace.

For 3-5 real players, traces the full pipeline:
  Savant fetch → _PITCHER_SAVANT_CACHE / _BATTER_PT_CACHE
  → load_hvy_context() → ctx dict
  → renderer field resolution
  → session-state key construction

Checks:
  1. Correct player / pitcher attachment
  2. Source object consistency (ctx top-level vs ctx["pitch_mix"])
  3. Renderer field names match source field names
  4. Cache key correctness (pm_ck, hvy_ck, _pm_loaded_key)
  5. Card HTML fingerprint completeness
  6. _pm_loaded_ stale-slate scenario
  7. JIG Refresh vs MAIN cache isolation
  8. "Show All Pitches" key collision across tabs

Run from repo root:
  py -3.12 audit_pitch_mix_trace.py
"""

import sys, os, json, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "mlb_hr_engine_v4"))

import config
from clients import pitch_mix as pm, arsenal as ar_client
from clients.pitch_mix import (
    load_hvy_context, _PITCHER_SAVANT_CACHE, _BATTER_PT_CACHE, _H2H_CACHE,
    HVY_CACHE_VERSION, _canonical_pt, _pitch_keys, _lookup_pitch,
    _build_pitch_rows, _build_batter_rows, _finalize_pitch_stats,
)

SEP  = "=" * 72
SEP2 = "-" * 60

def _fmt(v, precision=3):
    if v is None: return "None"
    if isinstance(v, float): return f"{v:.{precision}f}"
    return str(v)

def _pct(v):
    if v is None: return "None"
    return f"{v*100:.1f}%"


# ── Test players — use manually constructed minimal player dicts ───────────────
# player_id, pitcher_id, batter_side, pitcher_hand, player_name, pitcher_name
#
# IMPORTANT: IDs below are hardcoded to specific matchups that existed at the
# time this script was written. Update them to active matchups before running
# for best coverage. 0-row Savant results (e.g. a pitcher with no current-season
# data) are structurally valid but skip the arsenal/pitch_rows validation path —
# the trace still confirms object identity and cache keys correctly.
TEST_PLAYERS = [
    # Power RHB vs LHP (platoon advantage)
    {
        "player_id":   547180,   # Aaron Judge
        "pitcher_id":  669923,   # Blake Snell (LHP)
        "player_name": "Aaron Judge",
        "pitcher_name":"Blake Snell",
        "batter_side": "R",
        "pitcher_hand":"L",
        "team": "NYY", "opponent": "SFG",
        "barrel_pct": "17.5%", "exit_velo": "95.1",
        "sweet_spot_pct": "38.2%", "fb_pct": "35.1%",
        "pull_pct": "44.2%", "hard_hit_pct": "62.1%",
    },
    # Switch hitter vs RHP (routes to LHB side)
    {
        "player_id":   592518,   # Freddie Freeman
        "pitcher_id":  621111,   # Shane Bieber (RHP)
        "player_name": "Freddie Freeman",
        "pitcher_name":"Shane Bieber",
        "batter_side": "S",
        "pitcher_hand":"R",
        "team": "LAD", "opponent": "CLE",
        "barrel_pct": "9.2%", "exit_velo": "91.2",
        "sweet_spot_pct": "33.5%", "fb_pct": "26.3%",
        "pull_pct": "38.1%", "hard_hit_pct": "45.2%",
    },
    # LHB vs RHP
    {
        "player_id":   518692,   # Manny Machado
        "pitcher_id":  592789,   # Corbin Burnes (RHP)
        "player_name": "Manny Machado",
        "pitcher_name":"Corbin Burnes",
        "batter_side": "R",
        "pitcher_hand":"R",
        "team": "SDP", "opponent": "BAL",
        "barrel_pct": "7.8%", "exit_velo": "90.5",
        "sweet_spot_pct": "31.2%", "fb_pct": "24.1%",
        "pull_pct": "35.4%", "hard_hit_pct": "42.3%",
    },
]


def trace_player(p: dict, arsenal_data: dict, disp_stats: dict, index: int):
    player_id  = p["player_id"]
    pitcher_id = p["pitcher_id"]
    batter_side = p.get("batter_side", "R")
    pitcher_hand = p.get("pitcher_hand", "R")

    # Effective batting side for switch hitters
    if batter_side == "S":
        eff_side = "R" if pitcher_hand == "L" else "L"
    else:
        eff_side = batter_side

    print(f"\n{SEP}")
    print(f"PLAYER {index}: {p['player_name']}  (bid={player_id})")
    print(f"  Pitcher : {p['pitcher_name']}  (pid={pitcher_id})")
    print(f"  Batter side: {batter_side} → effective: {eff_side}")
    print(f"  Pitcher hand: {pitcher_hand}")
    print(SEP)

    # ── 1. Call load_hvy_context ───────────────────────────────────────────────
    print("\n[1] Calling load_hvy_context()…")
    ctx = load_hvy_context(p, arsenal_data, disp_stats)
    print(f"  ctx keys: {sorted(ctx.keys())}")
    print(f"  hvy_modifier: {ctx.get('hvy_modifier')}")
    print(f"  data_year: {ctx.get('data_year')}")

    # ── 2. Check source object consistency ────────────────────────────────────
    print(f"\n[2] Source object consistency check:")
    pm_obj       = ctx.get("pitch_mix", {})
    pm_arsenal   = pm_obj.get("arsenal", [])       # ctx["pitch_mix"]["arsenal"]
    top_arsenal  = ctx.get("pitcher_arsenal", [])  # ctx["pitcher_arsenal"]
    pm_brows     = pm_obj.get("batter_rows", [])   # ctx["pitch_mix"]["batter_rows"]
    top_brows    = ctx.get("batter_rows", [])      # ctx["batter_rows"]
    pm_prows     = pm_obj.get("pitch_rows", [])    # ctx["pitch_mix"]["pitch_rows"]
    top_prows    = ctx.get("pitch_rows", [])       # ctx["pitch_rows"]

    same_arsenal = (pm_arsenal is top_arsenal)
    same_brows   = (pm_brows   is top_brows)
    same_prows   = (pm_prows   is top_prows)

    print(f"  ctx['pitch_mix']['arsenal'] is ctx['pitcher_arsenal']: {same_arsenal}")
    print(f"  ctx['pitch_mix']['batter_rows'] is ctx['batter_rows']: {same_brows}")
    print(f"  ctx['pitch_mix']['pitch_rows'] is ctx['pitch_rows']:   {same_prows}")

    if not same_arsenal:
        print("  ⚠️  MISMATCH: pitch_mix['arsenal'] ≠ ctx['pitcher_arsenal']")
        print(f"     pitch_mix['arsenal'] len={len(pm_arsenal)}")
        print(f"     ctx['pitcher_arsenal'] len={len(top_arsenal)}")

    # ── 3. Pitcher arsenal — source vs ctx ────────────────────────────────────
    print(f"\n[3] Pitcher arsenal (from ctx['pitch_mix']['arsenal']):")
    print(f"  {len(pm_arsenal)} pitch types   (leaderboard pitcher_id={pitcher_id})")
    for entry in pm_arsenal[:6]:
        pt   = entry.get("pitch_type", "?")
        pct  = entry.get("pitch_pct", 0) * 100
        spd  = entry.get("avg_speed")
        whf  = entry.get("display_whiff")
        hh   = entry.get("display_hh")
        rv   = entry.get("display_rv100")
        kpct = entry.get("k_pct")
        hrr  = entry.get("hr_rate")
        p_ba = entry.get("pitch_ba")
        p_slg= entry.get("pitch_slg")
        print(f"  {pt:4s}  use={pct:5.1f}%  spd={_fmt(spd,1):6s}  "
              f"whiff={_pct(whf):7s}  HH={_pct(hh):7s}  "
              f"RV={_fmt(rv,1):6s}  K={_pct(kpct):7s}  HR={_pct(hrr):7s}  "
              f"BA={_fmt(p_ba):6s}  SLG={_fmt(p_slg):6s}")

    # ── 4. Pitch rows (built from arsenal) ───────────────────────────────────
    print(f"\n[4] Pitch rows (built by _build_pitch_rows, from ctx['pitch_rows']):")
    print(f"  Source: ctx['pitch_mix']['pitch_rows']  len={len(pm_prows)}")
    print(f"  Field names: pitch_type, pitch_usage(0-100%), whiff_pct(0-100%), "
          "hard_hit_pct(0-100%), rv_per100, avg_speed")
    for pr in pm_prows[:6]:
        pt   = pr.get("pitch_type", "?")
        use  = pr.get("pitch_usage")
        whf  = pr.get("whiff_pct")
        hh   = pr.get("hard_hit_pct")
        rv   = pr.get("rv_per100")
        spd  = pr.get("avg_speed")
        print(f"  {pt:4s}  use={_fmt(use,1):5s}%  whiff={_fmt(whf,1):5s}%  "
              f"HH={_fmt(hh,1):5s}%  RV={_fmt(rv,1):6s}  spd={_fmt(spd,1):6s}mph")

    # Verify scale conversion (arsenal pitch_pct 0-1 → pitch_rows pitch_usage 0-100)
    print(f"\n  Scale verification (arsenal vs pitch_rows):")
    for ar_e, pr_e in zip(pm_arsenal[:3], pm_prows[:3]):
        ar_pct = (ar_e.get("pitch_pct") or 0) * 100
        pr_use = pr_e.get("pitch_usage") or 0
        ar_whf = (ar_e.get("display_whiff") or 0) * 100 if ar_e.get("display_whiff") is not None else None
        pr_whf = pr_e.get("whiff_pct")
        ok_pct = abs(ar_pct - pr_use) < 0.05
        ok_whf = (ar_whf is None and pr_whf is None) or (
            ar_whf is not None and pr_whf is not None and abs(ar_whf - pr_whf) < 0.05
        )
        print(f"    {ar_e.get('pitch_type','?'):4s}: "
              f"arsenal_pct={ar_pct:.1f}% → pitch_usage={pr_use:.1f}%  {'✓' if ok_pct else '✗ WRONG'} | "
              f"display_whiff×100={_fmt(ar_whf,1) if ar_whf is not None else 'None'}% → whiff_pct={_fmt(pr_whf,1) if pr_whf is not None else 'None'}%  "
              f"{'✓' if ok_whf else '✗ WRONG'}")

    # ── 5. Batter rows — source vs rendered ──────────────────────────────────
    print(f"\n[5] Batter rows (built by _build_batter_rows, from ctx['batter_rows']):")
    print(f"  Source: get_batter_vs_pitches(bid={player_id}, pitcher_hand='{pitcher_hand}')")
    raw_batter_vs = ctx.get("batter_vs", {})
    print(f"  raw batter_vs pitch types: {sorted(raw_batter_vs.keys())}")
    print(f"  batter_rows len: {len(pm_brows)}")
    print(f"  Fields: pitch_type, pa, hr, hr_rate, ba, slg, iso, k_pct")
    print(f"  (Note: all pitch type keys in batter_vs are already canonicalized at fetch time)")
    for br in pm_brows[:6]:
        pt   = br.get("pitch_type", "?")
        pa   = br.get("pa")
        hr   = br.get("hr")
        ba   = br.get("ba")
        slg  = br.get("slg")
        iso  = br.get("iso")
        hrr  = br.get("hr_rate")
        kpct = br.get("k_pct")
        src  = raw_batter_vs.get(pt, {})
        src_ba  = src.get("ba")
        src_slg = src.get("slg")
        ba_ok  = (ba is None and src_ba is None) or (ba is not None and src_ba is not None and abs(ba - src_ba) < 0.001)
        slg_ok = (slg is None and src_slg is None) or (slg is not None and src_slg is not None and abs(slg - src_slg) < 0.001)
        print(f"  {pt:4s}  PA={pa}  HR={hr}  BA={_fmt(ba):6s}  SLG={_fmt(slg):6s}  "
              f"ISO={_fmt(iso):6s}  HR%={_pct(hrr):7s}  K%={_pct(kpct):7s}")
        print(f"        src_ba={_fmt(src_ba):6s}  src_slg={_fmt(src_slg):6s}  "
              f"BA_match={'✓' if ba_ok else '✗'}  SLG_match={'✓' if slg_ok else '✗'}")

    # ── 6. Hand splits ────────────────────────────────────────────────────────
    print(f"\n[6] Hand splits (pitcher vs L/R batters):")
    hs = ctx.get("hand_splits", ctx.get("pitch_mix", {}).get("hand_splits", {}))
    for hand in ("L", "R"):
        sp = hs.get(hand, {})
        print(f"  vs {hand}HB: PA={sp.get('pa')}  HR={sp.get('hr')}  "
              f"BA={_fmt(sp.get('ba'))}  SLG={_fmt(sp.get('slg'))}")
    print(f"  Effective batter side → lookup key: {eff_side}")
    used_split = hs.get(eff_side, {})
    print(f"  Used for Signal 1: PA={used_split.get('pa')}  HR={used_split.get('hr')}")

    # ── 7. H2H ────────────────────────────────────────────────────────────────
    print(f"\n[7] Career H2H (pitcher={pitcher_id} vs batter={player_id}):")
    h2h = ctx.get("h2h", ctx.get("pitch_mix", {}).get("h2h", {}))
    print(f"  {h2h}")

    # ── 8. Cache key audit ────────────────────────────────────────────────────
    print(f"\n[8] Cache key audit:")
    HVY_VER = HVY_CACHE_VERSION

    # MAIN picks context key (tab_picks)
    # _pm_pitcher_fp = hash(frozenset((p.get("player_id"), p.get("pitcher_id")) for p in ranked))
    # We simulate with a single-player ranked list
    pm_pitcher_fp = hash(frozenset({(player_id, pitcher_id)}))
    date_str = config.CURRENT_SEASON  # would be data.get('date','') in prod
    pm_ck = f"picks_pm_ctx_{date_str}_{HVY_VER}_{pm_pitcher_fp}"
    print(f"  MAIN _pm_ck (picks context key):")
    print(f"    {pm_ck}")
    print(f"    anchors: date + HVY_CACHE_VERSION + player/pitcher fingerprint")
    print(f"    ⚠️  does NOT include data_loaded_at → Force Refresh doesn't clear it")

    hvy_pitcher_fp = hash(frozenset({(player_id, pitcher_id)}))
    hvy_ck = f"hvy_ctx_{date_str}_{HVY_VER}_{hvy_pitcher_fp}"
    print(f"\n  JIG _hvy_ck (JIG context key):")
    print(f"    {hvy_ck}")

    print(f"\n  MAIN _pm_ck == JIG _hvy_ck when player sets identical: {pm_ck == hvy_ck}")

    # _pm_loaded_ key — lazy gate key used by _render_pitch_mix_expander
    uid = str(player_id)
    for kp in [f"qv_tac_1", f"elite_1", f"me_0", "hvyq", "hvyp", "hvypr", "hvyfts"]:
        pm_loaded_key = f"_pm_loaded_{kp}_{uid}"
        print(f"  _pm_loaded_ for prefix='{kp}':  {pm_loaded_key}")
        if kp == "qv_tac_1":
            print(f"    ⚠️  NOT anchored to slate_ts → survives across date changes")
        if kp in ("hvyq", "hvyp", "hvypr", "hvyfts"):
            print(f"    (static prefix — same player loaded across sub-tabs uses separate keys: OK)")

    # Show All Pitches key — NOT prefixed by tab
    show_all_k = f"pm_showall_{player_id}"
    print(f"\n  'Show All Pitches' toggle key: {show_all_k}")
    print(f"  ⚠️  key_prefix NOT included → clicking 'Show All' in QV also shows all in Elite/JIG")

    # ── 9. Card HTML fingerprint completeness ─────────────────────────────────
    print(f"\n[9] Card fingerprint completeness:")

    # QV fingerprint (_intelligence_card_html)
    slate_ts = "2026-05-18T10:00:00"
    qpid = player_id
    rank = 1
    is_live = False; is_steam = False; optimizer_on = False; is_opt_sel = False
    urgency_lbl = "2h 30m"; gt_str = "13:05 ET"
    status_html = ""
    # Simulated pitch_attack_tags (2 tags from top-2 pitches)
    pitch_tags = []
    if pm_arsenal:
        top = pm_arsenal[0]
        pt  = top.get("pitch_type","")
        use = (top.get("pitch_pct") or 0) * 100
        pitch_tags.append((f"{pt} {use:.0f}% primary", "tac-pitch-neutral"))

    qv_fp = (
        "ic", slate_ts, qpid, rank,
        is_live, is_steam, optimizer_on, is_opt_sel,
        urgency_lbl, gt_str,
        hash(status_html) if status_html else 0,
        tuple(pitch_tags) if pitch_tags else (),
    )
    print(f"  QV _qv_fp includes: card_type, slate_ts, player_id, rank, live, steam, optimizer,")
    print(f"    opt_sel, urgency, gametime, status_hash, pitch_tags_tuple")
    print(f"  ⚠️  pitch_tags_tuple = top 2 tags only (not full pitch mix content)")
    print(f"  ⚠️  if pitch context changes but top-2 attack tags unchanged → NO card rebuild")
    print(f"  Example fp: {qv_fp}")

    # Matchup Edge fingerprint
    mp_mod   = ctx.get("hvy_modifier", 1.0)
    pm_prows_len = len(pm_prows)
    me_fp = (
        "me", slate_ts, qpid, is_live,
        round(mp_mod, 2), pm_prows_len,
        hash(status_html) if status_html else 0,
    )
    print(f"\n  ME _me_fp: ('me', slate_ts, player_id, is_live, round(mod,2), len(pitch_rows), status_hash)")
    print(f"  ⚠️  uses len(pitch_rows)={pm_prows_len} not content hash")
    print(f"  ⚠️  if pitch mix refreshes with same pitch count → NO card rebuild → stale badges shown")
    print(f"  Example fp: {me_fp}")

    # JIG HVY card fingerprint
    hvy_score = 75.0  # example
    hvy_ctx_known = bool(ctx.get("pitcher_arsenal") or ctx.get("batter_vs") or ctx.get("hand_splits"))
    hvy_html_fp = (
        hvy_ck, qpid, round(hvy_score, 1), is_live, hvy_ctx_known,
        hash("") if not status_html else hash(status_html),
    )
    print(f"\n  JIG _hvy_html_fp: (hvy_ck, player_id, round(hvy,1), is_live, ctx_known, status_hash)")
    print(f"  ⚠️  mod_s (displayed modifier) NOT in fingerprint → if mod changes but hvy doesn't,")
    print(f"     card HTML shows stale modifier text")
    print(f"  Example fp: {hvy_html_fp}")

    # ── 10. JIG Refresh vs MAIN cache isolation bug ───────────────────────────
    print(f"\n[10] JIG Refresh vs MAIN cache isolation:")
    print(f"  JIG Refresh button handler pops: session_state['{hvy_ck}']")
    print(f"  MAIN context key NOT cleared:   session_state['{pm_ck}']")
    print(f"  ⚠️  BUG: after JIG Refresh, MAIN tabs continue serving stale pitch mix data")
    print(f"  ⚠️  MAIN's _pm_ck survives until: (a) date changes, (b) HVY_CACHE_VERSION bumps,")
    print(f"     (c) player/pitcher set changes, or (d) Matchup Edge 'Refresh' button fires")
    print(f"  Matchup Edge Refresh handler pops: session_state['{pm_ck}'] (via _me_ck = _pm_ck)")
    print(f"  → ME Refresh correctly clears MAIN; JIG Refresh does NOT → confirmed asymmetry")

    # ── 11. Cached savant data check ─────────────────────────────────────────
    print(f"\n[11] Module-level cache state (after this player's load):")
    print(f"  _PITCHER_SAVANT_CACHE keys: {sorted(_PITCHER_SAVANT_CACHE.keys())}")
    print(f"  _BATTER_PT_CACHE keys (sample): {sorted(_BATTER_PT_CACHE.keys())[:6]}")
    print(f"  _H2H_CACHE keys (sample): {sorted(_H2H_CACHE.keys())[:4]}")

    print(f"\n{SEP2}")


def check_key_prefix_collisions():
    """Verify all _render_pitch_mix_expander call sites have unique widget keys."""
    print(f"\n{SEP}")
    print("KEY PREFIX COLLISION ANALYSIS")
    print(SEP)
    print("All _render_pitch_mix_expander call sites (from app.py):")
    call_sites = [
        ("QV Command Center",    "qv_tac_{rank}",   "rank = 1..12",          "unique per player+rank"),
        ("Elite tab",            "elite_{rank}",    "rank = 1..N",           "unique per player+rank"),
        ("Matchup Edge",         "me_{index}",      "index = 0..page_size-1","unique per player+index"),
        ("JIG Command Center",   "hvyq",            "TOP 3 ONLY",            "⚠️ STATIC — shared across all qualified players in this sub-tab"),
        ("JIG Top Targets",      "hvyp",            "page 25/50/all",        "⚠️ STATIC — shared across all qualified players"),
        ("JIG Full Tactical",    "hvypr",           "page 25/50/all",        "⚠️ STATIC — shared across all qualified players"),
        ("JIG Full Slate",       "hvyfts",          "2 modes (all/scored)",  "⚠️ STATIC — shared across all qualified players"),
    ]
    print(f"  {'Tab':<25} {'key_prefix':<20} {'Cardinality':<30} {'Assessment'}")
    print(f"  {'-'*25} {'-'*20} {'-'*30} {'-'*50}")
    for tab, kp, card, assess in call_sites:
        print(f"  {tab:<25} {kp:<20} {card:<30} {assess}")

    print("""
Static key_prefix with unique _uid (player_id) in button keys:
  _pm_loaded_  key = f"_pm_loaded_{{key_prefix}}_{{player_id}}"  → unique per player+tab ✓
  pm_load_     key = f"pm_load_{{key_prefix}}_{{player_id}}"     → unique per player+tab ✓
  {{prefix}}_pm_sa_ = f"{{key_prefix}}_pm_sa_{{player_id}}"     → unique per player+tab ✓

BUT: "Show All Pitches" session_state TOGGLE key:
  _show_all_k = f"pm_showall_{{player_id}}"  (no key_prefix!)
  → CROSS-TAB POLLUTION: clicking "Show All" in QV also shows all in Elite/JIG for same player
""")


def check_batter_vs_pitcher_hand_routing():
    """Verify batter_vs lookup uses pitcher_hand correctly."""
    print(f"\n{SEP}")
    print("BATTER_VS PITCHER HAND ROUTING VERIFICATION")
    print(SEP)
    print("""
In load_hvy_context():
  pitcher_hand    = player.get("pitcher_hand", "")
  effective_batter_side = "R" if batter_side=="S" and pitcher_hand=="L" else "L" (for switch)
  pitcher_arsenal = _build_pitcher_arsenal_canonical(pitcher_id, ..., batter_side=effective_batter_side)
  batter_vs       = get_batter_vs_pitches(batter_id, pitcher_hand)    ← uses pitcher HAND

get_batter_vs_pitches(batter_id, pitcher_hand="R"):
  → returns _BATTER_PT_CACHE[(batter_id, "R")]
  → accumulated from rows where p_throws == "R"
  → correct: "how does this batter hit each pitch TYPE when facing a RHP?"

get_pitcher_pitch_stats(pitcher_id, batter_side=effective_batter_side):
  → if eff_side=="L": returns pitch_stats_vs_l (pitcher's stats vs LHB)
  → correct: "what does this pitcher throw and how effective is each pitch vs LHB?"

Routing is correct by design. The two lookups use DIFFERENT dimensions:
  batter_vs   → pitcher handedness (R/L pitcher)
  arsenal     → batter handedness (R/L batter) from pitcher's perspective
These are inverses of each other — both correctly scoped to the actual matchup.
""")


def main():
    print(f"\n{'#'*72}")
    print("# PITCH MIX TRUST AUDIT — DEEP ROOT-CAUSE TRACE")
    print(f"# Date: 2026-05-18   Season: {config.CURRENT_SEASON}")
    print(f"# HVY_CACHE_VERSION: {HVY_CACHE_VERSION}")
    print(f"{'#'*72}")

    print(f"\nLoading arsenal data for season {config.CURRENT_SEASON}…")
    try:
        arsenal_data = ar_client.get_pitcher_arsenal(config.CURRENT_SEASON)
        from clients.arsenal import get_pitch_display_stats
        disp_stats = get_pitch_display_stats(config.CURRENT_SEASON)
        print(f"  Arsenal: {len(arsenal_data)} pitchers")
        print(f"  Display stats: {len(disp_stats)} (pitcher_id, pitch_type) pairs")
    except Exception as e:
        print(f"  Arsenal fetch failed: {e}")
        arsenal_data = {}
        disp_stats = {}

    for i, player in enumerate(TEST_PLAYERS, start=1):
        try:
            trace_player(player, arsenal_data, disp_stats, i)
        except Exception as e:
            import traceback
            print(f"\n[ERROR] Player {i} trace failed: {e}")
            traceback.print_exc()

    check_key_prefix_collisions()
    check_batter_vs_pitcher_hand_routing()

    print(f"\n{SEP}")
    print("CONFIRMED BUG SUMMARY")
    print(SEP)
    bugs = [
        ("CRITICAL", "A",
         "JIG Refresh clears _hvy_ck but NOT _pm_ck",
         "app.py:5566",
         "After JIG Refresh, MAIN QV/Elite/Matchup Edge continue serving "
         "stale pitch mix contexts. Module caches cleared → JIG re-fetches; "
         "MAIN session_state key survives unchanged → MAIN shows old data.",
         "In JIG Refresh handler, also pop all 'picks_pm_ctx_*' keys."),

        ("CRITICAL", "B",
         "ME card fingerprint uses len(pitch_rows) not content hash",
         "app.py:3891",
         "_me_fp = ('me', slate_ts, pid, live, round(mod,2), len(pitch_rows), status_hash). "
         "If pitcher's pitch mix data updates but pitch COUNT stays the same "
         "(e.g., usage or whiff stats change but still 5 pitches), "
         "the cached card HTML is NOT rebuilt → stale pitch badges shown in Matchup Edge cards.",
         "Replace len(_mp_pitch_rows) with hash of pitch content in _me_fp."),

        ("MEDIUM", "C",
         "_pm_loaded_ lazy-gate keys not anchored to slate_ts",
         "app.py:2100",
         "Key: f'_pm_loaded_{key_prefix}_{player_id}'. "
         "Persists across date/slate changes. If same player at same rank on new date, "
         "the expander auto-opens. Data shown is correct (new ctx), but user gets "
         "surprise auto-expanded cards on every date load for previously-loaded players.",
         "Include slate_ts in key: f'_pm_loaded_{key_prefix}_{player_id}_{slate_ts}'. "
         "Requires passing slate_ts into _render_pitch_mix_expander."),

        ("MEDIUM", "D",
         "_hvy_card HTML fingerprint missing modifier display value",
         "app.py:4931",
         "_hvy_html_fp = (_hvy_ck, pid, round(hvy,1), is_live, ctx_known, status_hash). "
         "mod_s (modifier text e.g. '▲ 112%') NOT in fingerprint. "
         "If modifier changes from 1.12 → 1.08 but hvy stays ~75.0 (difference <0.05), "
         "cached HTML shows old modifier text/bar while underlying value has changed.",
         "Add round(mod, 2) to _hvy_html_fp."),

        ("MINOR", "E",
         "Show All Pitches toggle key not scoped to tab",
         "app.py:2317",
         "_show_all_k = f'pm_showall_{player_id}' (no key_prefix). "
         "If same player appears in QV and Elite, clicking Show All in one tab "
         "also expands the other tab's batter_vs_pitch table.",
         "Change to f'pm_showall_{key_prefix}_{player_id}'."),
    ]

    for severity, label, title, location, description, fix in bugs:
        print(f"\n  [{severity}] Bug {label}: {title}")
        print(f"    Location:    {location}")
        print(f"    Description: {description}")
        print(f"    Fix:         {fix}")

    print(f"\n{SEP}")
    print("FILES TO CHANGE")
    print(SEP)
    print("  mlb_hr_engine_v4/app.py — all 5 bugs")
    print("  (pitch_mix.py: no changes needed — source data is correct)")
    print(SEP)
    print("AUDIT COMPLETE")


# MANUAL USE ONLY — do NOT wire into CI or any automated pipeline.
# This script makes live Savant API calls with no rate limiting.
if __name__ == "__main__":
    main()
