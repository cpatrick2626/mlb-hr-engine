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
];

/* ---- Room filters: how Tactical Command Center values affect a room ---- */
window.FILTER_DEFAULTS = { minBarrel: 0, minHH: 0, minEV: 0, sortKey: "none", sortDir: "Descending", maxPlayers: 75 };

window.SORT_OPTIONS = [
  { label: "Default (Tier)", key: "none" },
  { label: "Barrel %",       key: "barrel" },
  { label: "Exit Velocity",  key: "ev" },
  { label: "Hard Hit %",     key: "hh" },
  { label: "xwOBA",          key: "xwoba" },
  { label: "HR / PA",        key: "hrpa" },
  { label: "AVG",            key: "avg" },
];

window.applyRoomFilters = function (rows, f) {
  if (!f) return rows;
  let out = rows.filter((r) => {
    if (f.minBarrel && !(r.barrel >= f.minBarrel)) return false;
    if (f.minHH && !(r.hh >= f.minHH)) return false;
    if (f.minEV && !(r.ev >= f.minEV)) return false;
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
  if (f.minBarrel > d.minBarrel) n++;
  if (f.minHH > d.minHH) n++;
  if (f.minEV > d.minEV) n++;
  if (f.sortKey && f.sortKey !== "none") n++;
  if (f.maxPlayers && f.maxPlayers < d.maxPlayers) n++;
  return n;
};
