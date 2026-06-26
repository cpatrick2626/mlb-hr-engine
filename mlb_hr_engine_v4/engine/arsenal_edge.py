"""
Arsenal Edge Exploit — backend precompute.
Display-only: NOT wired into MAIN/JIG scoring, probability, calibration, or config.

compute_aee_score() is a pure function of already-cached pitch-mix data.
Call AFTER the _jig_score() loop so _PITCHER_SAVANT_CACHE and _BATTER_PT_CACHE
are warm; this function makes no new HTTP requests.
"""

import config
from clients.pull_air import parse_pct_display, resolve_pull_air_pct
from clients.pitch_mix import get_pitcher_pitch_stats, get_batter_vs_pitches

# ── League baselines ───────────────────────────────────────────────────────────
# Read from config wherever a constant exists; LG_SLG defined locally
# (not in config) — same approach as clients/pitch_mix.py uses.
_LG_HR_PA   = config.LEAGUE_AVG_HR_PA               # 0.030  (fraction)
_LG_SLG     = 0.410                                  # MLB 2026; mirrors pitch_mix._LG_SLG
_LG_HH      = config.LEAGUE_AVG_HARD_HIT             # 0.398  (fraction 0-1, for pitch_stats.display_hh)
_LG_HH_PCT  = _LG_HH * 100.0                        # 39.8   (pct scale, for batter hard_hit field)
_LG_BARREL  = config.LEAGUE_AVG_BARREL_RATE * 100.0  # 5.5    (pct scale)
_LG_PULL    = config.LEAGUE_AVG_PULL_PCT * 100.0     # 39.4   (pct scale)
_LG_FB      = config.LEAGUE_AVG_FB_PCT * 100.0       # 26.4   (pct scale)
_LG_LD      = config.LEAGUE_AVG_LD_PCT * 100.0       # 23.6   (pct scale)
_LG_PULLAIR = _LG_PULL * (_LG_FB + _LG_LD) / 100.0  # ~19.7  (pct scale)

# Savant era pitch-code aliases (mirrors pitch_mix._PITCH_CANONICAL)
_PITCH_CANONICAL = {"FA": "FF", "SV": "ST"}


def _canon(pt: str) -> str:
    raw = (pt or "").strip().upper()
    return _PITCH_CANONICAL.get(raw, raw)


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _data_gap() -> dict:
    return {
        "arsenal_edge_score":       None,
        "arsenal_edge_label":       "DATA GAP",
        "arsenal_edge_key_pitch":   None,
        "arsenal_edge_confidence":  None,
        "arsenal_edge_sample_flag": False,
    }


def _aee_label(score: float, overall_conf: float) -> str:
    # VOLATILE overrides positive labels (tunable thresholds)
    if score >= 3.0 and overall_conf < 0.25:
        return "VOLATILE"
    if score >= 1.5 and overall_conf < 0.15:
        return "VOLATILE"
    # Score bands anchored to ×3 scaling (neutral matchup ≈ 3.0)
    if score >= 6.0:
        return "EXPLOSIVE"
    if score >= 4.5:
        return "MISMATCH"
    if score >= 3.0:
        return "LIVE EDGE"
    if score >= 1.5:
        return "WATCH"
    return "SUPPRESSED"


def _shape_modifier(player: dict) -> float:
    """
    Batter-level shape modifier applied once (not per-pitch).
    Symmetric clamp ±0.25. Weights renormalize when a field is absent.
    Default weights: w_brl=0.35, w_hh=0.40, w_pa=0.25.
    """
    barrel  = parse_pct_display(player.get("barrel_pct"), None)
    hh      = parse_pct_display(player.get("hard_hit"), None)
    pullair = resolve_pull_air_pct(player)  # returns 0.0 when absent
    if pullair <= 0:
        pullair = None

    # (value, league_avg, raw_weight)
    terms = []
    if barrel is not None:
        terms.append((barrel, _LG_BARREL, 0.35))
    if hh is not None:
        terms.append((hh, _LG_HH_PCT, 0.40))
    if pullair is not None:
        terms.append((pullair, _LG_PULLAIR, 0.25))

    if not terms:
        return 1.0

    total_w   = sum(t[2] for t in terms)
    composite = sum((w / total_w) * ((val / lg) - 1.0) for val, lg, w in terms if lg > 0)
    return 1.0 + _clamp(composite, -0.25, 0.25)


def compute_aee_score(player: dict, arsenal_data: dict | None) -> dict:
    """
    Compute Arsenal Edge Exploit display fields for one player.
    Always returns a dict with 5 keys — null-safe for serialization.
    Call after _jig_score() so pitch-mix caches are already warm.

    Inputs used:
      - arsenal_data[pitcher_id]          usage% per pitch (from clients/arsenal)
      - get_pitcher_pitch_stats()         pa/hr/display_hh per pitch (cached Savant)
      - get_batter_vs_pitches()           pa/hr/slg per pitch vs pitcher hand (cached Savant)
      - player barrel_pct/hard_hit/pull_air_pct  batter shape (from all_players dict)
    """
    pitcher_id   = player.get("pitcher_id")
    batter_id    = player.get("player_id") or player.get("batter_id")
    pitcher_hand = player.get("pitcher_hand", "")
    batter_side  = player.get("batter_side", "")

    if batter_side == "S" and pitcher_hand:
        effective_side = "R" if pitcher_hand == "L" else "L"
    else:
        effective_side = batter_side

    if not pitcher_id or not batter_id:
        return _data_gap()

    raw_arsenal = (arsenal_data or {}).get(pitcher_id, [])
    if not raw_arsenal:
        return _data_gap()

    # Cache hits — populated during the _jig_score() pass
    pitch_stats = get_pitcher_pitch_stats(pitcher_id, effective_side)
    batter_vs   = get_batter_vs_pitches(batter_id, pitcher_hand)

    # (pitch_code, usage_w, blended_exploit, conf, weighted_contrib, bvp_pa)
    contributions: list[tuple] = []

    for entry in raw_arsenal:
        pt_raw = (entry.get("pitch_type") or "").strip().upper()
        if not pt_raw:
            continue
        pt      = _canon(pt_raw)
        usage_w = float(entry.get("pitch_pct") or 0.0)
        if usage_w < 0.01:
            continue

        # ── Batter vs this pitch ─────────────────────────────────────────────
        bvp    = batter_vs.get(pt) or batter_vs.get(pt_raw) or {}
        bvp_pa = int(bvp.get("pa") or 0)
        if bvp_pa < 3:
            continue  # not eligible

        bvp_hr  = int(bvp.get("hr") or 0)
        bvp_slg = bvp.get("slg")  # None when ab < 3

        bvp_hr_rate = bvp_hr / bvp_pa
        if bvp_slg is not None:
            exploit = (1.0
                       + 0.60 * (bvp_hr_rate - _LG_HR_PA) / _LG_HR_PA
                       + 0.40 * (bvp_slg - _LG_SLG) / _LG_SLG)
        else:
            exploit = 1.0 + 1.00 * (bvp_hr_rate - _LG_HR_PA) / _LG_HR_PA
        exploit = _clamp(exploit, 0.0, 3.0)

        # ── Pitcher vulnerability for this pitch ─────────────────────────────
        pst    = pitch_stats.get(pt) or pitch_stats.get(pt_raw) or {}
        pst_pa = int(pst.get("pa") or 0)
        pst_hr = int(pst.get("hr") or 0)

        pst_hr_raw = (pst_hr / pst_pa) if pst_pa >= 5 else None
        pst_hh     = pst.get("display_hh")  # fraction 0-1; None when contact < 5

        if pst_hr_raw is not None and pst_hh is not None:
            vuln = (1.0
                    + 0.60 * (pst_hr_raw - _LG_HR_PA) / _LG_HR_PA
                    + 0.40 * (pst_hh - _LG_HH) / _LG_HH)
        elif pst_hr_raw is not None:
            vuln = 1.0 + 1.00 * (pst_hr_raw - _LG_HR_PA) / _LG_HR_PA
        elif pst_hh is not None:
            vuln = 1.0 + 1.00 * (pst_hh - _LG_HH) / _LG_HH
        else:
            vuln = 1.0  # neutral — pitch data absent, not penalized
        vuln = _clamp(vuln, 0.2, 2.5)

        blended = _clamp((exploit + vuln) / 2.0, 0.0, 2.5)
        conf    = _clamp((bvp_pa - 3) / 22.0, 0.0, 1.0)

        contributions.append((pt, usage_w, blended, conf, usage_w * blended * conf, bvp_pa))

    if not contributions:
        return _data_gap()

    raw_score   = sum(c[4] for c in contributions)
    shape_mod   = _shape_modifier(player)
    final_score = _clamp(raw_score * 3.0 * shape_mod, 0.0, 10.0)

    best      = max(contributions, key=lambda x: x[4])
    key_pitch = best[0] if best[4] > 0 else None

    usage_sum    = sum(c[1] for c in contributions)
    overall_conf = (sum(c[1] * c[3] for c in contributions) / usage_sum) if usage_sum > 0 else 0.0

    return {
        "arsenal_edge_score":       round(final_score, 1),
        "arsenal_edge_label":       _aee_label(final_score, overall_conf),
        "arsenal_edge_key_pitch":   key_pitch,
        "arsenal_edge_confidence":  round(overall_conf, 2),
        "arsenal_edge_sample_flag": any(c[5] < 10 for c in contributions),
    }
