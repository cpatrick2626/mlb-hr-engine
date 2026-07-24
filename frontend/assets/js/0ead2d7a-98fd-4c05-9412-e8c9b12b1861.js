/* HR Engine — Master Dashboard data.
   state: "mon" (live, monitoring), "hr" (hit a HR — blue + lightning),
          "dead" (game over, no HR — red). */

window.LIVE_TARGETS = [
  { id: "judge",  name: "JUDGE",      m: "NYY vs BOS", g: "3-1", inn: "BOT 7TH", state: "hr",   hrs: 1 },
  { id: "ohtani", name: "OHTANI",     m: "LAD vs SF",  g: "0-0", inn: "TOP 4TH", state: "mon",  hrs: 0 },
  { id: "acuna",  name: "ACUÑA JR.",  m: "ATL vs PHI", g: "2-4", inn: "FINAL",   state: "hr",   hrs: 1 },
  { id: "betts",  name: "BETTS",      m: "LAD @ SF",   g: "1-3", inn: "FINAL",   state: "dead", hrs: 0 },
  { id: "trout",  name: "TROUT",      m: "LAA vs TEX", g: "1-2", inn: "BOT 2ND", state: "mon",  hrs: 0 },
  { id: "turner", name: "TREA TURNER",m: "PHI vs ATL", g: "0-1", inn: "TOP 2ND", state: "mon",  hrs: 0 },
  { id: "soto",   name: "SOTO",       m: "NYM vs WSH", g: "2-2", inn: "BOT 5TH", state: "mon",  hrs: 0 },
  { id: "harper", name: "HARPER",     m: "PHI vs ATL", g: "0-1", inn: "TOP 2ND", state: "hr",   hrs: 2 },
  { id: "alvarez",name: "ÁLVAREZ",    m: "HOU @ SEA",  g: "4-1", inn: "FINAL",   state: "dead", hrs: 0 },
  { id: "witt",   name: "WITT JR.",   m: "KC vs CLE",  g: "1-1", inn: "TOP 6TH", state: "mon",  hrs: 0 },
];

/* Team-cap colors for the generic headshot avatars. */
window.CAP_COLORS = ["#c8102e", "#005a9c", "#fd5a1e", "#e81828", "#003087", "#ce1141", "#27251f", "#005c5c"];

/* Rotating Quick Picks pool (strategy suggestions from Strategy room). */
window.QUICK_PICKS = [
  { id: "elite",  label: "ELITE SPOT",   icon: "crosshair", color: "#1aff66", score: "9.6", tag: "Top 3 HR Prop Edge",     caps: [0,1,2,3] },
  { id: "power",  label: "POWER STACK",  icon: "target",    color: "#ffb020", score: "8.9", tag: "Stack for Maximum Power", caps: [4,0,5,1] },
  { id: "value",  label: "VALUE SPOT",   icon: "star",      color: "#3b6fff", score: "7.8", tag: "High Value, Leverage Spot",caps: [6,2,7,4] },
  { id: "park",   label: "PARK BOOST",   icon: "diamond",   color: "#00d9ff", score: "8.4", tag: "Coors-Type Air Density",  caps: [2,5,0,6] },
  { id: "streak", label: "HOT STREAK",   icon: "trend",     color: "#1aff66", score: "9.1", tag: "5+ Barrels, Last 7 G",    caps: [1,3,4,7] },
  { id: "lefty",  label: "PLATOON EDGE", icon: "bolt",      color: "#ffb020", score: "8.0", tag: "LHB vs RHP Soft Arsenal", caps: [5,1,6,0] },
];

/* Engines + their sub-lenses. lens key "fullSlate" is the default content. */
window.ENGINES = [
  {
    id: "main", name: "MAIN", suffix: "ENGINE", icon: "home",
    color: "#ff3344", glow: "rgba(255,51,68,0.2)", tint: "rgba(255,51,68,0.05)",
    expandable: true,
    subs: [
      { id: "fullSlate",  name: "Full Slate",    tag: "DEFAULT" },
      { id: "topTargets", name: "Top Targets" },
      { id: "matchup",    name: "Matchup Hunter" },
      { id: "power",      name: "Power Profile" },
      { id: "arsenal",    name: "Arsenal" },
      { id: "deploy",     name: "Deploy" },
    ],
  },
  {
    id: "jig", name: "JIG", suffix: "ENGINE", icon: "crosshair",
    color: "#00d9ff", glow: "rgba(0,217,255,0.2)", tint: "rgba(0,217,255,0.05)",
    expandable: true,
    subs: [
      { id: "fullSlate",  name: "Full Slate",    tag: "DEFAULT" },
      { id: "topTargets", name: "Top Targets" },
      { id: "matchup",    name: "Matchup Hunter" },
      { id: "power",      name: "Power Profile" },
      { id: "arsenal",    name: "Arsenal" },
      { id: "deploy",     name: "Deploy" },
      { id: "builder",    name: "JIG Builder",   tag: "BUILD" },
    ],
  },
  {
    id: "e26", name: "26", suffix: "ENGINE", icon: "dashring",
    color: "#3b6fff", glow: "rgba(59,111,255,0.2)", tint: "rgba(59,111,255,0.05)",
    desc: "MLB Home Run Intelligence Engine",
  },
  {
    id: "strategy", name: "STRATEGY", suffix: "", icon: "wrench",
    color: "#ffb020", glow: "rgba(255,176,32,0.2)", tint: "rgba(255,176,32,0.05)",
    desc: "Build custom tactics, filters and models",
  },
  {
    id: "performance", name: "PERFORMANCE", suffix: "", icon: "bar",
    color: "#1aff66", glow: "rgba(26,255,102,0.2)", tint: "rgba(26,255,102,0.05)",
    desc: "Track player and pitcher performance trends",
  },
  {
    id: "command", name: "COMMAND", suffix: "", icon: "target",
    color: "#ff8a93", glow: "rgba(255,138,147,0.2)", tint: "rgba(255,138,147,0.05)",
    desc: "Tactical overview · MAIN / JIG",
  },
];

/* ---- Room filters: how Tactical Command Center values affect a room ---- */
window.FILTER_DEFAULTS = {
  minBarrel: 0, minHH: 0, minEV: 0,
  minISO: 0, minXSLG: 0, minHRFB: 0, minPullAir: 0, minSweet: 0, minFB: 0,
  minLaunchAngle: 0,
  minRHPISO: 0, minLHPISO: 0,
  minMatchupModifier: 75,
  minHR9: 0, minBarrelAllowed: 0, minHHAllowed: 0, minFBAllowed: 0,
  minPitcherHRAllowed: 0,
  minRecentHRs: 0, minStreakFactor: 0.89,
  minTempF: 0, minWindMph: 0, windDirection: "Any",
  minHRProb: 0,
  sortKey: "none", sortDir: "Descending", maxPlayers: 999,
  excludeStarted: false,
  includeLive: true,
  confirmedLineupsOnly: false,
  preLineupPool: true,
};

window.SORT_OPTIONS = [
  { label: "Default (Tier)", key: "none" },
  { label: "Barrel %",       key: "barrel" },
  { label: "Exit Velocity",  key: "ev" },
  { label: "Hard Hit %",     key: "hh" },
  { label: "xwOBA",          key: "xwoba" },
  { label: "HR / PA",        key: "hrpa" },
  { label: "AVG",            key: "avg" },
  { label: "JIG Score",      key: "jigScore" },
];

window.windDegToCompass = function (degrees) {
  if (degrees == null || degrees === "") return null;
  const numeric = Number(degrees);
  if (!Number.isFinite(numeric)) return null;
  const buckets = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  const normalized = ((numeric % 360) + 360) % 360;
  return buckets[Math.round(normalized / 45) % buckets.length];
};

window.applyRoomFilters = function (rows, f) {
  if (!f) return rows;
  let out = rows.filter((r) => {
    if (f.minBarrel  && !(r.barrel  >= f.minBarrel))  return false;
    if (f.minHH      && !(r.hh      >= f.minHH))      return false;
    if (f.minEV      && !(r.ev      >= f.minEV))       return false;
    if (f.minISO     && !(r.iso     >= f.minISO))      return false;
    if (f.minXSLG    && !(r.xslg    >= f.minXSLG))     return false;
    if (f.minHRFB    && !(r.hrfb    >= f.minHRFB))     return false;
    if (f.minPullAir && !(r.pullair >= f.minPullAir))  return false;
    if (f.minSweet   && !(r.sweet   >= f.minSweet))    return false;
    if (f.minFB      && !(r.fb      >= f.minFB))       return false;
    if (f.minLaunchAngle && !(r.la >= f.minLaunchAngle)) return false;
    if (f.minRHPISO  && !(r.vs_rhp_iso >= f.minRHPISO)) return false;
    if (f.minLHPISO  && !(r.vs_lhp_iso >= f.minLHPISO)) return false;
    if (r._board === "jig" && f.minMatchupModifier > window.FILTER_DEFAULTS.minMatchupModifier &&
        !(r.hvy_modifier != null && r.hvy_modifier * 100 >= f.minMatchupModifier)) return false;
    if (f.minHR9     && !(r.opphr >= f.minHR9))          return false;
    if (f.minPitcherHRAllowed && !(r.pitcher_hr_allowed != null && r.pitcher_hr_allowed >= f.minPitcherHRAllowed)) return false;
    if (f.minBarrelAllowed && !(r.pitcher_barrel_allowed != null && r.pitcher_barrel_allowed * 100 >= f.minBarrelAllowed)) return false;
    if (f.minHHAllowed     && !(r.pitcher_hh_allowed     != null && r.pitcher_hh_allowed     * 100 >= f.minHHAllowed))     return false;
    if (f.minFBAllowed     && !(r.pitcher_fb_allowed     != null && r.pitcher_fb_allowed     * 100 >= f.minFBAllowed))     return false;
    if (f.minRecentHRs && !(r.short_form_hr != null && r.short_form_hr >= f.minRecentHRs)) return false;
    if (f.minStreakFactor > window.FILTER_DEFAULTS.minStreakFactor &&
        !(r.streak_factor != null && r.streak_factor >= f.minStreakFactor)) return false;
    // Environment is display/filter only. Missing weather is explicitly allowed through.
    if (f.minTempF && r.temp_f != null && Number.isFinite(Number(r.temp_f)) &&
        Number(r.temp_f) < f.minTempF) return false;
    if (f.minWindMph && r.wind_mph != null && Number.isFinite(Number(r.wind_mph)) &&
        Number(r.wind_mph) < f.minWindMph) return false;
    if (f.windDirection && f.windDirection !== "Any") {
      const windDirection = window.windDegToCompass(r.wind_deg);
      if (windDirection != null && windDirection !== f.windDirection) return false;
    }
    if (f.minHRProb  && !(r.hrprob  >= f.minHRProb))   return false;
    // Game Context filters
    if (f.confirmedLineupsOnly && !r.pitcher_confirmed) return false;
    if (f.excludeStarted || !f.includeLive) {
      const gs = r.gameStartUtc;
      if (gs) {
        const startMs = Date.parse(gs);
        if (!isNaN(startMs)) {
          const started = startMs <= Date.now();
          if (started) {
            if (!f.includeLive) return false;
            if (f.excludeStarted) return false;
          }
        }
      }
    }
    if (f.preLineupPool === false && !r.pitcher_confirmed) return false;
    return true;
  });
  if (f.sortKey && f.sortKey !== "none") {
    const k = f.sortKey;
    out = [...out].sort((a, b) => {
      const av = a[k] == null ? -Infinity : a[k];
      const bv = b[k] == null ? -Infinity : b[k];
      return f.sortDir === "Ascending" ? av - bv : bv - av;
    });
  }
  if (f.maxPlayers) out = out.slice(0, f.maxPlayers);
  return out;
};

window.countActiveFilters = function (f) {
  if (!f) return 0;
  const d = window.FILTER_DEFAULTS;
  let n = 0;
  if (f.minBarrel  > d.minBarrel)  n++;
  if (f.minHH      > d.minHH)      n++;
  if (f.minEV      > d.minEV)      n++;
  if (f.minISO     > d.minISO)     n++;
  if (f.minXSLG    > d.minXSLG)    n++;
  if (f.minHRFB    > d.minHRFB)    n++;
  if (f.minPullAir > d.minPullAir) n++;
  if (f.minSweet   > d.minSweet)   n++;
  if (f.minFB      > d.minFB)      n++;
  if (f.minLaunchAngle > d.minLaunchAngle) n++;
  if (f.minRHPISO  > d.minRHPISO)  n++;
  if (f.minLHPISO  > d.minLHPISO)  n++;
  if (f.minMatchupModifier > d.minMatchupModifier) n++;
  if (f.minHR9     > d.minHR9)     n++;
  if (f.minPitcherHRAllowed > d.minPitcherHRAllowed) n++;
  if (f.minBarrelAllowed > d.minBarrelAllowed) n++;
  if (f.minHHAllowed     > d.minHHAllowed)     n++;
  if (f.minFBAllowed     > d.minFBAllowed)     n++;
  if (f.minRecentHRs > d.minRecentHRs) n++;
  if (f.minStreakFactor > d.minStreakFactor) n++;
  if (f.minTempF > d.minTempF) n++;
  if (f.minWindMph > d.minWindMph) n++;
  if (f.windDirection && f.windDirection !== d.windDirection) n++;
  if (f.minHRProb  > d.minHRProb)  n++;
  if (f.sortKey && f.sortKey !== "none") n++;
  if (f.maxPlayers != null && f.maxPlayers !== d.maxPlayers) n++;
  if (f.excludeStarted !== d.excludeStarted) n++;
  if (f.includeLive !== d.includeLive) n++;
  if (f.confirmedLineupsOnly !== d.confirmedLineupsOnly) n++;
  if (f.preLineupPool !== d.preLineupPool) n++;
  return n;
};
