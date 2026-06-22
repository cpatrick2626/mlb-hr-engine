# tools/size_conf_bug.py — read-only sizing diagnostic for the confidence-ranking bug.
# Reads the LIVE slate API only. Writes nothing. Imports nothing from app.py / engine.
# Discovers the row schema at runtime; refuses to fabricate counts it cannot compute.

import sys, json, urllib.request

API = "https://mlb-hr-api.fly.dev/api/slate"

# Tier thresholds per ranker.py confidence_tier(): S>=70, A>=55, B>=35.
A_S_FLOOR = 55  # "A/S tier" = confidence_tier >= A

# Candidate field names the row MIGHT use. We probe, never assume.
HR9_CONF_KEYS   = ["hr9_conf", "hr9_confidence", "pitcher_hr9_conf"]
PLAT_CONF_KEYS  = ["plat_conf", "platoon_conf", "handedness_conf"]
PIT_IP_KEYS     = ["pit_ip", "pitcher_ip", "pitcher_innings", "pit_innings"]
PLAT_HAND_KEYS  = ["plat_hand", "matchup_hand", "platoon_state", "bat_vs_throw"]
CONF_KEYS       = ["confidence", "confidence_score", "conf"]
NAME_KEYS       = ["batter", "player", "batter_name", "name", "player_name"]

# Fallback sentinels from probability.py:553/:555 (the bug's signature).
HR9_FALLBACK  = 6.0
PLAT_FALLBACK = 4.0

def first_key(d, keys):
    for k in keys:
        if k in d:
            return k
    return None

def fetch():
    req = urllib.request.Request(API, headers={"User-Agent": "size-conf-bug/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def main():
    try:
        data = fetch()
    except Exception as e:
        print(f"FETCH FAILED: {e}")
        print("Cannot reach live slate. Sizing aborted — do not substitute stale data.")
        sys.exit(1)

    gen = data.get("generated_at", "<missing>")
    rows = data.get("leaderboard_rows", [])
    print(f"generated_at : {gen}")
    print(f"MAIN rows    : {len(rows)}")
    if not rows:
        print("Empty slate. Nothing to size. (Cron may not have fired.)")
        sys.exit(0)

    sample = rows[0]
    print(f"\nRow keys ({len(sample)}): {sorted(sample.keys())}\n")

    # Resolve which schema fields actually exist on this payload.
    k_conf  = first_key(sample, CONF_KEYS)
    k_name  = first_key(sample, NAME_KEYS)
    k_hr9c  = first_key(sample, HR9_CONF_KEYS)
    k_platc = first_key(sample, PLAT_CONF_KEYS)
    k_ip    = first_key(sample, PIT_IP_KEYS)
    k_hand  = first_key(sample, PLAT_HAND_KEYS)

    print("RESOLVED FIELDS")
    print(f"  confidence  -> {k_conf}")
    print(f"  name        -> {k_name}")
    print(f"  hr9_conf    -> {k_hr9c}")
    print(f"  plat_conf   -> {k_platc}")
    print(f"  pit_ip      -> {k_ip}")
    print(f"  plat_hand   -> {k_hand}")

    if k_conf is None:
        print("\nCONFIDENCE FIELD NOT IN PAYLOAD. Cannot identify A/S tier members.")
        print("FINDING: live slate API does not serialize confidence. Sizing must move")
        print("to an engine-side read (probability.py output), not the API payload.")
        sys.exit(0)

    # --- Detection strategy, in priority order ---
    # Direct: if pit_ip / handedness present, count true under-sample + missing-hand.
    # Indirect: if only the conf sub-scores present, match the exact fallback sentinels.
    can_direct_ip   = k_ip   is not None and k_hr9c  is not None
    can_direct_hand = k_hand is not None and k_platc is not None
    can_sentinel    = k_hr9c is not None or k_platc is not None

    a_s = [r for r in rows if isinstance(r.get(k_conf), (int, float)) and r[k_conf] >= A_S_FLOOR]
    print(f"\nA/S tier picks (confidence >= {A_S_FLOOR}): {len(a_s)} of {len(rows)}")

    if not (can_direct_ip or can_direct_hand or can_sentinel):
        print("\nNEITHER pitcher-sample fields NOR conf sub-scores are in the payload.")
        print("FINDING: cannot size from API. The fields live inside the engine and are")
        print("dropped before serialization. Sizing requires an engine-side diagnostic")
        print("(read probability.py confidence output for today's matchups), not the API.")
        sys.exit(0)

    def hits(row):
        flags = []
        if can_direct_ip:
            ip = row.get(k_ip)
            if isinstance(ip, (int, float)) and ip < 5:
                flags.append("under-sampled-pitcher(<5IP)")
        if can_direct_hand:
            h = row.get(k_hand)
            if h in (None, "", "unknown", "UNK", "NA"):
                flags.append("missing-handedness")
        # Sentinel backstop: exact fallback values are the bug's fingerprint.
        if k_hr9c is not None and row.get(k_hr9c) == HR9_FALLBACK:
            flags.append(f"hr9_conf==fallback({HR9_FALLBACK})")
        if k_platc is not None and row.get(k_platc) == PLAT_FALLBACK:
            flags.append(f"plat_conf==fallback({PLAT_FALLBACK})")
        return flags

    inflated = []
    for r in a_s:
        f = hits(r)
        if f:
            inflated.append((r.get(k_name, "<?>"), r.get(k_conf), f))

    print(f"\nINFLATED A/S picks (fallback-driven, no real data): {len(inflated)}")
    if can_direct_ip or can_direct_hand:
        print("  (direct: measured against pit_ip / handedness fields)")
    else:
        print("  (sentinel-only: matched exact fallback values 6.0 / 4.0 — confirm")
        print("   these aren't legitimately-computed 6.0/4.0 before trusting the count)")

    for name, conf, flags in sorted(inflated, key=lambda x: -(x[1] or 0)):
        print(f"  {str(name)[:24]:24}  conf={conf}  {', '.join(flags)}")

    print(f"\nSIZE: {len(inflated)} of {len(a_s)} A/S picks are fallback-driven "
          f"({len(inflated)/len(a_s)*100:.0f}% of A/S).")
    print("Take this number to the operator fix decision: depress / flag+cap / leave.")

if __name__ == "__main__":
    main()
