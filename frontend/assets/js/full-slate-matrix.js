/* HR Engine — FULL SLATE INTELLIGENCE MATRIX
   Dense battlefield-style threat scan: 6-tier system, conic matchup pies,
   5-bucket Statcast heatmap, GAME / PLAYER views. Replaces the legacy
   leaderboard inside the MAIN/JIG "Full Slate" lens. */

const FSM_TIERS = {
  APEX: { color: "#ff3344", glow: "rgba(255,51,68,0.75)", min: 20 },
  ELITE: { color: "#ff8a93", glow: "rgba(255,138,147,0.55)", min: 16 },
  EDGE: { color: "#1aff66", glow: "rgba(26,255,102,0.6)", min: 11 },
  SIGNAL: { color: "#3b6fff", glow: "rgba(59,111,255,0.5)", min: 7 },
  WATCH: { color: "#ffb020", glow: "rgba(255,176,32,0.45)", min: 4 },
  COLD: { color: "#6b7872", glow: "rgba(107,120,114,0.35)", min: 0 }
};
const FSM_TIER_ORDER = ["APEX", "ELITE", "EDGE", "SIGNAL", "WATCH", "COLD"];

/* matchup quality → filled quadrants (of 4) + color */
const FSM_MATCHUP = {
  ELITE: { q: 4, color: "#4ade80" },
  STRONG: { q: 3, color: "#86efac" },
  AVG: { q: 2, color: "#fbbf24" },
  WEAK: { q: 1, color: "#f97316" }
};
const FSM_MATCHUP_ORDER = ["ELITE", "STRONG", "AVG", "WEAK"];

/* TM (true_matchup_score) band thresholds — operator-approved, honest 0–100, do not rescale */
const TM_BANDS = [
  { min: 60, label: "ELITE",  color: "#4ade80" },
  { min: 50, label: "STRONG", color: "#86efac" },
  { min: 38, label: "AVG",    color: "#fbbf24" },
  { min: 25, label: "WEAK",   color: "#f97316" },
  { min:  0, label: "COLD",   color: "#ef4444" },
];
function tmBand(score) {
  if (score == null) return { label: "—", color: "#8a9691" };
  for (const b of TM_BANDS) { if (score >= b.min) return b; }
  return TM_BANDS[TM_BANDS.length - 1];
}
const FSM_TIER_DESC = {
  APEX: "greatest HR threat — model HR probability ≥ 20% this game",
  ELITE: "premium danger — model HR probability ≥ 16%",
  EDGE: "strong advantage — model HR probability ≥ 11%",
  SIGNAL: "positive signal — model HR probability ≥ 7%",
  WATCH: "marginal — model HR probability ≥ 4%",
  COLD: "do not deploy — model HR probability < 4%",
};
const FSM_MATCHUP_DESC = {
  ELITE: "top batter HR-threat tier — model probability + barrel quality",
  STRONG: "strong batter HR-threat — high model probability + barrel quality",
  AVG: "average batter HR-threat — mid-range model probability + barrel quality",
  WEAK: "below-average batter HR-threat — lower model probability + barrel quality",
  TARGET: "pitcher allows 2.2+ HR/9 — most hittable arms on the slate",
};
const FSM_BUILDER_TIER_DESC = {
  APEX: "MAIN model probability tier: APEX — inherited by JIG display",
  ELITE: "MAIN model probability tier: ELITE — inherited by JIG display",
  EDGE: "MAIN model probability tier: EDGE — inherited by JIG display",
  SIGNAL: "MAIN model probability tier: SIGNAL — inherited by JIG display",
  WATCH: "MAIN model probability tier: WATCH — inherited by JIG display",
  COLD: "MAIN model probability tier: COLD — inherited by JIG display",
};

/* JIG tier is server-computed (row.jigTier from config.JIG_TIER_THRESHOLDS,
   0-100 jigScore bands ratified 2026-07-13). No client-side tier thresholds. */

const TEAM_COLOR = {
  MIA: "#00a3e0", TOR: "#1d4f91", NYY: "#8a95a0", BOS: "#bd3039", COL: "#5b48a0",
  CHC: "#0e3386", ATL: "#ce1141", PHI: "#e81828", HOU: "#eb6e1f", TEX: "#003278",
  LAD: "#2f6fc0", SF: "#fd5a1e"
};

/* today's slate — supplied by the data file (window.SLATE_GAMES) */
const getFSMGames = () => window.SLATE_GAMES && window.SLATE_GAMES.length > 0
  ? window.SLATE_GAMES
  : [{ id: "tor-mia", away: "TOR", home: "MIA", park: "loanDepot Park", time: "7:10 PM ET",
       weather: "Roof Closed · 72°F", wind: "Calm", hrFactor: 0.94, teams: ["TOR", "MIA"] }];


/* ET time formatter — same pattern as slate-command-strip.js */
function fsmFmtEt(utc) {
  if (!utc) return null;
  const ms = Date.parse(utc);
  if (isNaN(ms)) return null;
  return new Date(ms).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: true });
}

/* formatters */
const f3d = (v) => v.toFixed(3).replace(/^0/, ""); // .222
const fp = (v) => v.toFixed(1) + "%";
const f1 = (v) => v.toFixed(1);
const f2 = (v) => v.toFixed(2);
const fdeg = (v) => v.toFixed(1) + "°";

/* column defs — bucketsHi = higher is better (4 cuts), bucketsLo = lower is better */
const FSM_COLS = [
{ key: "odds", head: "ODDS", title: "HR prop odds (American)", group: "STATS", mode: "odds", fmt: (v) => String(v) },
{ key: "hr", head: "HR", title: "Home runs — REAL vs-hand split count in VS HAND mode (PA always shown; thin <30 PA tagged amber); season total in SEASON mode", group: "STATS", bucketsHi: [28, 18, 10, 5], fmt: (v) => String(v) },
{ key: "barrel", head: "BARREL%", title: "Barrel rate (Savant brl_pa: barrels per plate appearance, not per batted-ball event) — optimal EV + launch-angle contact, the best HR predictor", group: "STATCAST", bucketsHi: [8, 6, 4.5, 3], fmt: fp },
{ key: "xslg", head: "xSLG", title: "Expected slugging from quality of contact", group: "STATS", bucketsHi: [0.520, 0.450, 0.400, 0.350], fmt: f3d },
{ key: "iso", head: "xISO", title: "Expected isolated power (xSLG − xBA) from quality of contact — season Statcast stat; not split-adjustable", group: "STATS", bucketsHi: [0.250, 0.180, 0.120, 0.070], fmt: f3d },
{ key: "hh", head: "HH%", title: "Hard-hit rate (95+ mph exit velo)", group: "STATCAST", bucketsHi: [45, 40, 34, 28], fmt: fp },
{ key: "pullair", head: "PULLAIR%", title: "Pull-air proxy: pulled FB+LD as share of ALL batted-ball events (pull% × (FB%+LD%)), not pulled air balls only — approximates pulled-air contact tendency", group: "STATCAST", bucketsHi: [26, 21, 16, 12], fmt: fp },
{ key: "blast", head: "BLAST%", title: "Blast rate — fast swing + squared-up contact", group: "STATCAST", bucketsHi: [16, 11, 7, 4], fmt: fp, na: "--" },
{ key: "maxev", head: "MAX EV", title: "Max exit velocity (mph) — peak raw power", group: "STATCAST", bucketsHi: [112, 109, 106, 103], fmt: f1 },
{ key: "squp", head: "SQUP%", title: "Squared-up rate — efficiency of contact vs max EV", group: "STATCAST", bucketsHi: [30, 25, 20, 15], fmt: fp, na: "--" },
{ key: "ev", head: "EV", title: "Average exit velocity (mph)", group: "STATCAST", bucketsHi: [92, 90, 88, 86], fmt: f1 },
{ key: "hrpa", head: "HR/PA", title: "Home runs per plate appearance — REAL vs-hand split when available (thin samples tagged with PA); SZN = season rate fallback", group: "STATS", mode: "headline", fmt: (v) => v.toFixed(3) },
{ key: "sweet", head: "SS%", title: "Launch-angle sweet-spot rate — batted balls at 8–32°", group: "STATCAST", bucketsHi: [38, 34, 30, 26], fmt: fp },
{ key: "la", head: "LA°", title: "Launch angle — HR sweet spot ≈ 15°", group: "STATCAST", special: "la", fmt: fdeg },
{ key: "slg", head: "SLG", title: "Slugging percentage — REAL vs-hand split when available (thin samples tagged with PA); SZN = season-blended fallback", group: "STATS", bucketsHi: [0.520, 0.460, 0.410, 0.370], fmt: f3d },
{ key: "fast", head: "FAST%", title: "Fast-swing rate — swings at 75+ mph bat speed", group: "STATCAST", bucketsHi: [40, 28, 18, 10], fmt: fp, na: "--" },
{ key: "xwoba", head: "xwOBA", title: "Expected weighted on-base average", group: "STATS", bucketsHi: [0.350, 0.330, 0.310, 0.290], fmt: f3d },
{ key: "obp", head: "OBP", title: "On-base percentage — approximation; sacrifice flies (SF) excluded from denominator (source limitation)", group: "STATS", bucketsHi: [0.360, 0.335, 0.310, 0.290], fmt: f3d },
{ key: "avg", head: "AVG", title: "Batting average — REAL vs-hand split when available (thin samples tagged with PA); SZN = season-blended fallback", group: "STATS", bucketsHi: [0.290, 0.265, 0.240, 0.215], fmt: f3d },
{ key: "babip", head: "BABIP", title: "Batting average on balls in play", group: "STATS", bucketsHi: [0.330, 0.300, 0.270, 0.240], fmt: f3d },
{ key: "bbpct", head: "BB%", title: "Walk rate", group: "STATS", bucketsHi: [12, 9, 7, 5], fmt: fp },
{ key: "kpct", head: "K%", title: "Strikeout rate — LOWER is better", group: "STRIKES", bucketsLo: [15, 20, 25, 30], fmt: fp },
{ key: "woba", head: "wOBA", title: "Weighted on-base average — DATA GAP: no real source currently available; hidden by default", group: "STATS", bucketsHi: [0.370, 0.345, 0.320, 0.300], fmt: f3d },
{ key: "pa", head: "PA", title: "Plate appearances — sample size", group: "STATS", mode: "neutral", fmt: (v) => String(v) },
{ key: "whiff", head: "WHIFF%", title: "Whiff rate — DATA GAP: no reliable batter-level source found; hidden by default", group: "STRIKES", bucketsLo: [18, 24, 30, 36], fmt: fp },
{ key: "swstr", head: "SWSTR%", title: "Swinging-strike rate — DATA GAP: no reliable batter-level source found; hidden by default", group: "STRIKES", bucketsLo: [8, 11, 14, 17], fmt: fp },
{ key: "pullbrl", head: "PULLBRL%", title: "Pulled-barrel rate — DATA GAP: no reliable source found; hidden by default", group: "STATCAST", bucketsHi: [6, 4, 2.5, 1.5], fmt: fp },
{ key: "gb", head: "GB%", title: "Ground-ball rate — LOWER is better for HR", group: "STATCAST", bucketsLo: [35, 40, 45, 50], fmt: fp },
{ key: "fb", head: "FB%", title: "Fly-ball rate — more fly balls = more HR chances", group: "STATCAST", bucketsHi: [42, 36, 30, 24], fmt: fp },
{ key: "ld", head: "LD%", title: "Line-drive rate", group: "STATCAST", bucketsHi: [28, 24, 20, 17], fmt: fp },
{ key: "air", head: "AIR%", title: "Air-ball rate — derived display value (FB% + LD%)", group: "STATCAST", bucketsHi: [60, 52, 44, 36], fmt: fp },
{ key: "pull", head: "PULL%", title: "Pull rate — pull-side power", group: "STATCAST", bucketsHi: [45, 40, 35, 30], fmt: fp },
{ key: "center", head: "CENTER%", title: "Center rate — lower favors pull-side power", group: "STATCAST", bucketsLo: [22, 26, 32, 40], fmt: fp },
{ key: "oppo", head: "OPPO%", title: "Opposite-field rate", group: "STATCAST", bucketsLo: [20, 25, 30, 35], fmt: fp },
{ key: "hrfb", head: "HR/FB%", title: "Home-run-per-fly-ball rate", group: "STATCAST", bucketsHi: [20, 14, 9, 5], fmt: fp },
{ key: "opphr", head: "OPP HR/9", title: "Opposing pitcher HR allowed per 9 — HIGHER favors the batter", group: "MATCHUP", danger: true, bucketsHi: [1.5, 1.3, 1.0, 0.7], fmt: f2 }];

const FSM_PICKER_COLS = FSM_COLS.filter((c) => !["woba", "whiff", "swstr", "pullbrl"].includes(c.key));

const FSM_COLSPAN = 3 + FSM_COLS.length; // tier + player + matchup + stats

/* Split scope per column: 'hand' columns display the batter's REAL split vs the
   pitcher hand faced tonight when the payload carries one; every other stat
   column is season-blended (the payload has no hand splits for Statcast quality
   metrics — never fabricate them). ODDS is market-scoped, not season. */
const FSM_SCOPE_HAND_KEYS = ["avg", "slg", "iso", "hrpa", "hr"];
FSM_COLS.forEach((c) => { c.scope = FSM_SCOPE_HAND_KEYS.includes(c.key) ? "hand" : c.key === "odds" ? null : "season"; });

/* vs-hand display keys → payload split fields */
const FSM_VS_HAND_SRC = { avg: "vs_hand_avg", slg: "vs_hand_slg", iso: "vs_hand_iso", hrpa: "vs_hand_hr_pa" };
const FSM_VS_HAND_MIN_PA = 30; // matches the backend's reliable-sample gate

/* Overlay REAL vs-hand splits onto the AVG/SLG/ISO/HR-PA display keys.
   Display-only: `_raw` keeps the untouched row for the batter-card hero and
   slip capture. `_vsScope[key]` records, per column, whether the shown number
   is a real faced-hand split (with PA + thin flag) or the season fallback. */
function fsmSplitRow(row) {
  const hand = row.vs_hand || null;
  const pa = row.vs_hand_pa;
  const o = { ...row, air: fsmAirPct(row), _raw: row, _vsScope: {} };
  Object.keys(FSM_VS_HAND_SRC).forEach((key) => {
    const v = row[FSM_VS_HAND_SRC[key]];
    if (hand && pa > 0 && v != null) {
      o[key] = v;
      o._vsScope[key] = { scope: "hand", hand, pa, thin: pa < FSM_VS_HAND_MIN_PA };
    } else {
      o._vsScope[key] = { scope: "season" };
    }
  });
  /* HR count split — derives from vs_lhp_hr / vs_rhp_hr based on faced hand */
  const vsHr = hand === "L" ? row.vs_lhp_hr : hand === "R" ? row.vs_rhp_hr : null;
  if (hand && pa > 0 && vsHr != null) {
    o.hr = vsHr;
    o._vsScope["hr"] = { scope: "hand", hand, pa, thin: pa < FSM_VS_HAND_MIN_PA };
  } else {
    o._vsScope["hr"] = { scope: "season" };
  }
  return o;
}

function fsmAirPct(row) {
  if (row.fb == null || row.ld == null) return null;
  const air = Number(row.fb) + Number(row.ld);
  return Number.isFinite(air) ? Math.round(air * 10) / 10 : null;
}

/* Honest scope tag under a split-column cell value. Never lets a vs-hand number
   appear without its scope, and never lets a thin sample masquerade as reliable. */
function FsmScopeTag({ scope }) {
  if (!scope) return null;
  if (scope.scope === "season")
    return <span className="fsm-scope fsm-scope--szn" title="Season-blended stat — no reliable vs-hand split for this matchup (no/empty split sample, or pitcher TBD)">SZN</span>;
  if (scope.thin)
    return <span className="fsm-scope fsm-scope--thin" title={`REAL split vs ${scope.hand}HP but THIN sample — only ${scope.pa} PA; not reliable`}>vs {scope.hand} · {scope.pa} PA</span>;
  return <span className="fsm-scope fsm-scope--hand" title={`REAL split vs ${scope.hand}HP — ${scope.pa} PA`}>vs {scope.hand} · {scope.pa} PA</span>;
}

function fsmBucket(col, v) {
  if (v == null) return "NA";
  if (col.special === "la") {
    if (v >= 24 && v <= 30) return "ELITE";
    if (v >= 21 && v <= 33) return "STRONG";
    if (v >= 17 && v <= 37) return "AVERAGE";
    if (v >= 13 && v <= 41) return "WEAK";
    return "DANGER";
  }
  if (col.bucketsHi) {const b = col.bucketsHi;
    if (v >= b[0]) return "ELITE";if (v >= b[1]) return "STRONG";if (v >= b[2]) return "AVERAGE";if (v >= b[3]) return "WEAK";return "DANGER";}
  if (col.bucketsLo) {const b = col.bucketsLo;
    if (v <= b[0]) return "ELITE";if (v <= b[1]) return "STRONG";if (v <= b[2]) return "AVERAGE";if (v <= b[3]) return "WEAK";return "DANGER";}
  return "NEUTRAL";
}
const FSM_BUCKET_CLASS = { ELITE: "is-elite", STRONG: "is-strong", AVERAGE: "is-avg", WEAK: "is-weak", DANGER: "is-danger", NA: "is-na", NEUTRAL: "" };

/* tier insignia */
function FsmTierIcon({ tier }) {
  const p = { fill: "none", stroke: "currentColor", strokeWidth: 1.6, strokeLinecap: "round", strokeLinejoin: "round" };
  switch (tier) {
    case "APEX":return <svg viewBox="0 0 24 24" width="20" height="20"><path {...p} d="M12 3 4 6v6c0 4.3 3.3 7.6 8 9 4.7-1.4 8-4.7 8-9V6l-8-3Z" /><path {...p} fill="currentColor" stroke="none" d="m12 8 1.3 2.7 3 .3-2.2 2 .6 2.9L12 16.5 9.3 18l.6-2.9-2.2-2 3-.3L12 8Z" /></svg>;
    case "ELITE":return <svg viewBox="0 0 24 24" width="20" height="20"><path {...p} d="m6 13 6-6 6 6" /><path {...p} d="m6 18 6-6 6 6" /></svg>;
    case "EDGE":return <svg viewBox="0 0 24 24" width="20" height="20"><path {...p} d="M12 3 21 12 12 21 3 12 12 3Z" /><path {...p} d="M12 8 16 12 12 16 8 12 12 8Z" /></svg>;
    case "SIGNAL":return <svg viewBox="0 0 24 24" width="20" height="20"><circle cx="12" cy="17" r="1.8" fill="currentColor" stroke="none" /><path {...p} d="M8.4 13.6a5 5 0 0 1 7.2 0" /><path {...p} d="M5.6 10.8a9 9 0 0 1 12.8 0" /></svg>;
    case "WATCH":return <svg viewBox="0 0 24 24" width="20" height="20"><rect {...p} x="3" y="4.5" width="18" height="12" rx="1.5" /><path {...p} d="M9 20h6M12 16.5V20" /><path {...p} d="m7.5 11 2.4 2.4L16 8" /></svg>;
    default:return <svg viewBox="0 0 24 24" width="20" height="20"><circle {...p} cx="12" cy="12" r="8.5" /><path {...p} d="M6.5 6.5 17.5 17.5" /></svg>;
  }
}

/* HR THREAT METER — continuous conic fill driven by model_prob.
   Tier bands mirror FS_TIER_THRESHOLDS from config.py (served via window.FS_TIER_THRESHOLDS). */
const FSM_PROB_TIER_BOUNDS = (() => {
  const src = (typeof window !== "undefined" && window.FS_TIER_THRESHOLDS) || {
    APEX: 0.20, ELITE: 0.16, EDGE: 0.11, SIGNAL: 0.07, WATCH: 0.04, COLD: 0.00
  };
  return [
    { lo: src.APEX,   hi: 0.29,       loFill: 0.85, hiFill: 1.00 }, // 0.29 = MAX_GAME_HR_PROB (config.py); not exposed to frontend
    { lo: src.ELITE,  hi: src.APEX,   loFill: 0.75, hiFill: 0.95 },
    { lo: src.EDGE,   hi: src.ELITE,  loFill: 0.55, hiFill: 0.75 },
    { lo: src.SIGNAL, hi: src.EDGE,   loFill: 0.35, hiFill: 0.55 },
    { lo: src.WATCH,  hi: src.SIGNAL, loFill: 0.15, hiFill: 0.35 },
    { lo: src.COLD,   hi: src.WATCH,  loFill: 0.00, hiFill: 0.15 },
  ];
})();

function fsmThreatFill(model_prob) {
  const p = model_prob || 0;
  for (const band of FSM_PROB_TIER_BOUNDS) {
    if (p >= band.lo) {
      const span = band.hi - band.lo;
      const t = span > 0 ? (p - band.lo) / span : 1;
      return band.loFill + t * (band.hiFill - band.loFill);
    }
  }
  return 0;
}

function FsmGauge({ fraction, color, size }) {
  const f = Math.max(0, Math.min(1, fraction || 0));
  const lg = size === "lg";
  const r  = lg ? 17 : 13;
  const sw = lg ? 5  : 4;
  const w  = lg ? 68 : 56;
  const h  = lg ? 48 : 38;
  const cx = w / 2;
  const cy = lg ? 20 : 16;
  const arc = Math.PI * r;
  const filled = (f * arc).toFixed(2);
  const pct = Math.round(f * 100);
  const x1 = cx - r, x2 = cx + r;
  const d = `M ${x1} ${cy} A ${r} ${r} 0 0 1 ${x2} ${cy}`;
  const ty = lg ? 39 : 31;
  const fs = lg ? 19 : 15;
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} fill="none" className="fsm-gauge" style={{ flexShrink: 0, overflow: "visible" }}>
      <path d={d} stroke="#2a2a3a" strokeWidth={sw} strokeLinecap="round" />
      <path d={d} stroke={color} strokeWidth={sw} strokeLinecap="round" strokeDasharray={`${filled} ${arc.toFixed(2)}`} />
      <text x={cx} y={ty} textAnchor="middle" fill={color} fontSize={fs} fontWeight="500" fontFamily="inherit">{pct}</text>
    </svg>
  );
}

/* TM gauge — arc fill = score/100 (honest), color from TM band, "TM" label inside cup.
   scoreProjected/confirmed: when provisional (projected ≠ current, not confirmed) shows ▸proj below. */
const SHOW_TM_GAUGE = false; // Intentionally hidden for the stacked MATCHUP layout; set true to restore the arc gauge.

function FsmTMGauge({ score, scoreProjected, confirmed, size }) {
  const band = tmBand(score);
  const f = score != null ? Math.max(0, Math.min(1, score / 100)) : 0;
  const lg = size === "lg";
  const r  = lg ? 17 : 13;
  const sw = lg ? 5  : 4;
  const w  = lg ? 68 : 56;
  const h  = lg ? 48 : 38;
  const cx = w / 2;
  const cy = lg ? 20 : 16;
  const arc = Math.PI * r;
  const filled = (f * arc).toFixed(2);
  const d = `M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`;
  const lblY = lg ? 29 : 22;
  const numY = lg ? 39 : 31;
  const lblFs = lg ? 7 : 6;
  const numFs = lg ? 17 : 14;
  const isDual = !confirmed && scoreProjected != null && Number.isFinite(scoreProjected) && scoreProjected !== score;
  const projBand = isDual ? tmBand(scoreProjected) : null;
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} fill="none" className="fsm-gauge" style={{ flexShrink: 0, overflow: "visible" }}>
      <path d={d} stroke="#2a2a3a" strokeWidth={sw} strokeLinecap="round" />
      <path d={d} stroke={band.color} strokeWidth={sw} strokeLinecap="round" strokeDasharray={`${filled} ${arc.toFixed(2)}`} />
      <text x={cx} y={lblY} textAnchor="middle" fill={band.color} fontSize={lblFs} fontWeight="800" fontFamily="inherit" opacity="0.8" letterSpacing="1">
        {score != null ? "TM" : ""}
      </text>
      <text x={cx} y={numY} textAnchor="middle" fill={band.color} fontSize={numFs} fontWeight="500" fontFamily="inherit">
        {score != null ? score : "—"}
      </text>
      {isDual && (
        <text x={cx} y={numY + 12} textAnchor="middle" fill={projBand.color} fontSize={9} fontWeight="600" fontFamily="inherit" opacity="0.75">
          {"▸" + Math.round(scoreProjected)}
        </text>
      )}
    </svg>
  );
}

function FsmCell({ col, row, extra }) {
  const v = row[col.key];
  const lbl = col.head;
  const xc = extra ? " fsm-cell--extra" : "";
  const scope = col.scope === "hand" && row._vsScope ? row._vsScope[col.key] : null;
  const tag = scope ? <FsmScopeTag scope={scope} /> : null;
  const na = col.na || "—";
  if (col.mode === "odds") return <td className={`fsm-cell fsm-cell--odds${xc}`} data-label={lbl}>{v == null ? na : col.fmt(v)}</td>;
  if (col.mode === "headline") return <td className={`fsm-cell fsm-cell--headline${xc}`} data-label={lbl}>{v == null ? na : col.fmt(v)}{tag}</td>;
  if (col.mode === "neutral") return <td className={`fsm-cell fsm-cell--neutral${xc}`} data-label={lbl}>{v == null ? na : col.fmt(v)}</td>;
  /* HR column in VS HAND mode: show "N HR" as value for clarity (PA in scope tag) */
  if (col.key === "hr" && scope && scope.scope === "hand") {
    const b = fsmBucket(col, v);
    return <td className={`fsm-cell ${FSM_BUCKET_CLASS[b] || ""}${xc}`} data-label={lbl}>{v == null ? na : v + " HR"}{tag}</td>;
  }
  const b = fsmBucket(col, v);
  return <td className={`fsm-cell ${FSM_BUCKET_CLASS[b] || ""}${xc}`} data-label={lbl}>{v == null ? na : col.fmt(v)}{tag}</td>;
}

const FSM_FANDUEL_SEARCH_URL = "https://sportsbook.fanduel.com/search";

/* Normalize a display name for FD search URL only — strips generational suffixes
   (Jr./Sr./II/III/IV) and accent-folds to ASCII. Display name is never mutated. */
function fdSearchName(displayName) {
  return (displayName || "")
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/,?\s*(Jr\.?|Sr\.?|II|III|IV)\s*$/i, "")
    .trim();
}

function fsmFanDuelUrl(term) {
  const q = fdSearchName(term);
  return q
    ? `${FSM_FANDUEL_SEARCH_URL}?q=${encodeURIComponent(q)}`
    : "https://sportsbook.fanduel.com/baseball/mlb?tab=player-home-runs";
}

function fsmCopyFanDuelSearch(term) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(term).catch(() => {});
  }
}

function fsmShowFanDuelToast(term) {
  let el = document.getElementById("fsm-fd-toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "fsm-fd-toast";
    el.style.cssText = "position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#1a2030;border:1px solid #3b6fff;color:#e0e8ff;padding:10px 18px;border-radius:8px;font-size:13px;font-family:inherit;z-index:9999;pointer-events:none;transition:opacity .3s;white-space:nowrap;";
    document.body.appendChild(el);
  }
  el.textContent = "Copied FanDuel search: " + term;
  el.style.opacity = "1";
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.style.opacity = "0"; }, 2800);
}

function fsmOpenFanDuelSearch(e, term) {
  e.stopPropagation();
  e.preventDefault();
  fsmCopyFanDuelSearch(term);
  window.open(fsmFanDuelUrl(term), "_blank", "noopener");
  fsmShowFanDuelToast(term);
}

/* FD tier-icon click: prefer captured deep link (bet-level, then event-level —
   lands on the specific game), else Streamlit parity search URL. Links are often
   absent (FD rarely posts outcome links); name search + clipboard stays the fallback. */
function fsmOpenFD(e, row) {
  const deepLink = row.fd_bet_link || row.fd_event_link;
  if (deepLink) {
    e.stopPropagation();
    e.preventDefault();
    fsmCopyFanDuelSearch(row.name);   // keep name on clipboard for manual fallback
    window.open(deepLink, "_blank", "noopener");
    fsmShowFanDuelToast(row.name);
  } else {
    fsmOpenFanDuelSearch(e, row.name);
  }
}

/* Tier badge tooltip — tier name + doctrine description + this row's real model_prob. */
function fsmTierTip(row, isJig, jigLabel, jigRank) {
  const tier = isJig && jigLabel ? jigLabel : row.tier;
  const desc = FSM_TIER_DESC[tier] || tier;
  const probPct = row.model_prob != null ? (row.model_prob * 100).toFixed(1) + "%" : "--";
  const context = isJig && jigLabel
    ? `Model Tier: ${tier} (MAIN probability) · JIG rank ${jigLabel} #${jigRank}`
    : tier;
  return `${context} — ${desc}. Model prob: ${probPct}.`;
}

/* Role badge tooltip — role meaning + this row's real qualifying field values. */
function fsmRoleTip(role, row) {
  const fmtPct = (v) => v != null ? Number(v).toFixed(1) + "%" : "--";
  const fmtX   = (v) => v != null ? Number(v).toFixed(3).replace(/^0/, "") : "--";
  const fmtMph = (v) => v != null ? Number(v).toFixed(1) : "--";
  switch (role) {
    case "prime":
      return `PRIME — Anchor: survives every quality test. barrel ${fmtPct(row.barrel)} · xSLG ${fmtX(row.xslg)} · HH ${fmtPct(row.hh)} · EV ${fmtMph(row.ev)}`;
    case "explosive":
      return `EXPLOSIVE — Slate-breaking upside. maxEV ${fmtMph(row.maxev)} · barrel ${fmtPct(row.barrel)}`;
    case "advantage":
      return `ADVANTAGE — Underpriced quality below top tier. xSLG ${fmtX(row.xslg)} · barrel ${fmtPct(row.barrel)}`;
    case "wildcard": {
      const traits = [];
      if (row.maxev  != null && row.maxev  >= 116)   traits.push(`maxEV ${fmtMph(row.maxev)}`);
      if (row.barrel != null && row.barrel >= 12)    traits.push(`barrel ${fmtPct(row.barrel)}`);
      if (row.xslg   != null && row.xslg   >= 0.520) traits.push(`xSLG ${fmtX(row.xslg)}`);
      if (row.pullair != null && row.pullair >= 30)  traits.push(`pullair ${fmtPct(row.pullair)}`);
      return `WILDCARD — Chaos upside. Elite trait(s): ${traits.length ? traits.join(" · ") : "--"}. Higher variance.`;
    }
  }
  return role.toUpperCase();
}

/* Pick-time signal snapshot (Strategy spec §5, snapshot_version 1).
   Records ONLY what this surface displays — never fabricates or computes.
   Forwarded via buildLegPayload → legs.signal_snapshot (display record; not scoring). */
function fsmBuildSnapshot(row, lane, sortState) {
  const game = (window.SLATE_GAMES || []).find((g) => g.id === row.gameId);
  return {
    snapshot_version: 1,
    surface: "full-slate",
    lane: lane,
    rank_signal_used: sortState && sortState.key ? sortState.key : "rank",
    tm_score: row.true_matchup_score != null ? row.true_matchup_score : null,
    hrprob: row.hrprob != null ? row.hrprob : null,
    tier: row.tier || null,
    dot_state: row.quality || null,
    environment: game ? {
      park_hr_factor: game.hrFactor != null ? game.hrFactor : null,
      weather: game.weather || null,
      wind: game.wind || null,
    } : null,
    generated_at: window.SLATE_GENERATED_AT || null,
  };
}

const FSM_SLIP_COLORS = {
  idle:   { border: 'rgba(59,111,255,0.6)',  color: '#3b6fff' },
  loading:{ border: 'rgba(107,120,114,0.4)', color: '#8a9691' },
  added:  { border: 'rgba(26,255,102,0.6)',  color: '#1aff66' },
  error:  { border: 'rgba(255,51,68,0.6)',   color: '#ff3344' },
  noauth: { border: 'rgba(255,176,32,0.5)',  color: '#ffb020' },
};
const FSM_SLIP_GLYPH = { idle: '+', loading: '…', added: '✓', error: '!', noauth: '⚿' };
const FSM_SLIP_TITLE = { idle: 'Add to slip', loading: 'Adding…', added: 'Added to slip', error: 'Error — retry', noauth: 'Log in to add' };

function FsmSlipBtn({ status, onClick, label }) {
  const s = status || 'idle';
  const c = FSM_SLIP_COLORS[s] || FSM_SLIP_COLORS.idle;
  const disabled = s === 'loading' || s === 'added';
  return (
    <button
      type="button"
      onClick={disabled ? undefined : onClick}
      title={FSM_SLIP_TITLE[s]}
      aria-label={"Add " + label + " to slip"}
      style={{
        background: 'transparent',
        border: '1px solid ' + c.border,
        borderRadius: '3px',
        cursor: disabled ? 'default' : 'pointer',
        fontSize: '13px',
        fontWeight: '700',
        width: '24px',
        height: '24px',
        padding: '0',
        lineHeight: '1',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'inherit',
        color: c.color,
        transition: 'border-color .15s, color .15s',
        flexShrink: 0,
      }}>
      {FSM_SLIP_GLYPH[s]}
    </button>
  );
}

function FsmRow({ row, cols, showGame, onBatter, onPitch, builderMode = false, isJigContext = false, jigLabel = null, jigRank = null, onAddLeg, slipStatus = 'idle', sortState = null }) {
  const [expanded, setExpanded] = React.useState(false);
  const displayTier = isJigContext && jigLabel ? jigLabel : row.tier;
  const t = FSM_TIERS[displayTier] || FSM_TIERS.COLD;
  const game = showGame ? (window.SLATE_GAMES || []).find((g) => g.id === row.gameId) : null;
  const confirmed = row.lineup_confirmed === true;
  const tmProj = row.tm_projected ?? null;
  const hrProj = row.hrprob_projected ?? null;
  const jigScore = row.jigScore ?? null;
  const jigProj = row.jigscore_projected ?? null;
  const hasJigScore = jigScore != null && Number.isFinite(Number(jigScore));
  const hasJigProjection = jigProj != null && Number.isFinite(Number(jigProj));
  const jigConfirmed = row.pitcher_confirmed === true || (hasJigScore && hasJigProjection && Number(jigProj) === Number(jigScore));
  const isDualTM = !confirmed && tmProj != null && Number.isFinite(tmProj) && tmProj !== row.true_matchup_score;
  const isDualHR = !confirmed && hrProj != null && Number.isFinite(hrProj) && hrProj !== row.hrprob;
  const isDualJig = !jigConfirmed && hasJigProjection && (!hasJigScore || Number(jigProj) !== Number(jigScore));
  const jigProjectionPending = !jigConfirmed && !hasJigProjection;
  return (
    <tr className={"fsm-row" + (expanded ? " is-expanded" : "")}>
      <td className="fsm-tiercell">
        <button
          type="button"
          className="fsm-tier fsm-tier--btn"
          style={{ "--tc": t.color, "--tg": t.glow }}
          onClick={(e) => { e.stopPropagation(); e.preventDefault(); const board = isJigContext ? 'jig' : (row._board || 'main'); const raw = row._raw || row; window.__hrSlip && window.__hrSlip.requestAdd({ player_id: raw.id, name: raw.name, teamAbbr: raw.teamAbbr, team: raw.teamAbbr, pitcher: raw.pitcher_name, pitcher_name: raw.pitcher_name, model_prob: raw.model_prob, tier: raw.tier, model_tier_rank: raw.model_tier_rank, board: board, hrprob: raw.hrprob, barrel: raw.barrel, hh: raw.hh, fd_bet_link: raw.fd_bet_link, fd_event_link: raw.fd_event_link, signal_snapshot: fsmBuildSnapshot(raw, board, sortState) }); }}
          title={fsmTierTip(row, isJigContext, jigLabel, jigRank) + " · Click: select destination"}
          aria-label={`Select destination for ${row.name}`}>

          <span className="fsm-tier__icon"><FsmTierIcon tier={displayTier} /></span>
          <span className="fsm-tier__label">{isJigContext && jigLabel ? `${jigLabel} #${jigRank}` : row.tier}</span>
          <span className="fsm-tier__add" aria-hidden="true">+ FD</span>
        </button>
        {(row.prime || row.explosive || row.advantage || row.wildcard) && (
          <span className="fsm-tiercell__roles">
            {row.prime && <span className="fsm-role-badge--prime" title={fsmRoleTip("prime", row)}>PRIME</span>}
            {row.explosive && <span className="fsm-role-badge--explosive" title={fsmRoleTip("explosive", row)}>EXPLOSIVE</span>}
            {row.advantage && <span className="fsm-role-badge--advantage" title={fsmRoleTip("advantage", row)}>ADVANTAGE</span>}
            {row.wildcard && <span className="fsm-role-badge--wildcard" title={fsmRoleTip("wildcard", row)}>WILDCARD</span>}
          </span>
        )}
      </td>
      <td className="fsm-player">
        <button type="button" className="fsm-player__in" onClick={() => onBatter(row)} title={`Open ${row.name} batter card`}>
          <span className="fsm-player__dot" title={row.pitcherVuln === "TARGET" ? `BATTER THREAT: ${row.quality || "—"} — batter HR-threat tier (model probability + barrel quality) · GLOW: TARGET pitcher allows 2.2+ HR/9 (separate pitcher-vulnerability signal)` : `BATTER THREAT: ${row.quality || "—"} — batter HR-threat tier based on model probability + barrel quality`} style={{ background: (FSM_MATCHUP[row.quality] || { color: "#6b7872" }).color, boxShadow: row.pitcherVuln === "TARGET" ? "0 0 0 2px #1aff66, 0 0 6px rgba(26,255,102,0.85)" : undefined }} />
          <span className="fsm-player__col">
            <span className="fsm-player__name">{row.name}</span>
            <span className="fsm-player__meta">{row.teamAbbr}<i className="fsm-player__bar">|</i>{row.bats}</span>
            {game
        ? <span className="fsm-player__game"><span className="fsm-player__gm--opp">{game.away}@{game.home}</span><i className="fsm-player__bar">·</i><span className="fsm-player__gm--time">{game.time || fsmFmtEt(row.gameStartUtc)}</span>{row.pitcher_name && <><i className="fsm-player__bar">·</i><span className="fsm-player__gm--pitcher">{row.pitcher_name}</span></>}</span>
        : (row.gameStartUtc || row.pitcher_name) && <span className="fsm-player__game"><span className="fsm-player__gm--time">{fsmFmtEt(row.gameStartUtc)}</span>{row.gameStartUtc && row.pitcher_name && <i className="fsm-player__bar">·</i>}{row.pitcher_name && <span className="fsm-player__gm--pitcher">{row.pitcher_name}</span>}</span>}
          </span>
        </button>
      </td>
      <td className="fsm-matchup">
        <button type="button" className="fsm-matchup__in" onClick={() => onPitch(row)} title="Open Arsenal Edge Intel">
          {SHOW_TM_GAUGE && !isJigContext && <FsmTMGauge score={row.true_matchup_score ?? null} scoreProjected={tmProj} confirmed={confirmed} />}
          <span className="fsm-matchup__metrics">
            <span className="fsm-matchup__metric fsm-matchup__metric--tm">
              <span className="fsm-matchup__lbl">{isJigContext ? "JIG" : "TM"}</span>
              <span className="fsm-matchup__val fsm-matchup__val--hero">
                {isJigContext ? (hasJigScore ? Number(jigScore).toFixed(0) : "—") : (row.true_matchup_score != null ? row.true_matchup_score : "—")}
              </span>
              {isJigContext ? (
                isDualJig ? <span className="fsm-matchup__proj">▸{Number(jigProj).toFixed(2)}</span> :
                jigProjectionPending ? <span className="fsm-matchup__proj" title="Projected JIG score unavailable until a pitcher is known">▸N/A</span> : null
              ) : (isDualTM && <span className="fsm-matchup__proj">▸{Math.round(tmProj)}</span>)}
            </span>
            <span className="fsm-matchup__metric fsm-matchup__metric--hr">
              <span className="fsm-matchup__lbl">HR PROB</span>
              <span className="fsm-matchup__val fsm-matchup__val--hero">{row.hrprob != null ? row.hrprob.toFixed(1) + "%" : "—"}</span>
              {isDualHR && <span className="fsm-matchup__proj">▸{hrProj.toFixed(1)}%</span>}
            </span>
            <span className="fsm-matchup__metric fsm-matchup__metric--single">
              <span className="fsm-matchup__lbl">BATTER EDGE</span>
              <span className="fsm-matchup__val">{row.arsenal_edge_score != null ? Number(row.arsenal_edge_score).toFixed(1) : "—"}</span>
            </span>
            <span className="fsm-matchup__metric fsm-matchup__metric--single">
              <span className="fsm-matchup__lbl">SIGNAL</span>
              <span className="fsm-matchup__val">{row.arsenal_edge_confidence != null ? Math.round(Number(row.arsenal_edge_confidence) * 100) + "%" : "—"}</span>
            </span>
          </span>
        </button>
      </td>
      {cols.map((c, ci) => <FsmCell key={c.key} col={c} row={row} extra={ci >= 12} />)}
      <td className="fsm-cell fsm-cell--slip" style={{ textAlign: 'center', padding: '0 4px' }}>
        <FsmSlipBtn status={slipStatus} onClick={() => onAddLeg && onAddLeg(row)} label={row.name} />
      </td>
      <td className="fsm-expandcell">
        <button type="button" className="fsm-expandbtn" onClick={() => setExpanded(x => !x)}>
          {expanded ? "SHOW LESS" : `+${Math.max(0, cols.length - 12)} MORE STATS`}
        </button>
      </td>
    </tr>);

}

function fsmGroupByTier(list) {
  const groups = [];let cur = null;
  list.forEach((r) => {
    if (!cur || cur.tier !== r.tier) {cur = { tier: r.tier, rows: [] };groups.push(cur);}
    cur.rows.push(r);
  });
  return groups;
}

function FsmGameHeader({ game, n }) {
  const factorCls = game.hrFactor >= 1.05 ? "is-hot" : game.hrFactor <= 0.96 ? "is-cold" : "";
  return (
    <div className="fsm-game">
      <div className="fsm-game__match"><b>{game.away}</b><span>@</span><b>{game.home}</b></div>
      <div className="fsm-game__meta">
        <span>{game.park}</span><i />
        <span>{game.time}</span><i />
        <span>{game.weather}</span><i />
        <span>WIND {game.wind}</span><i />
        <span>PARK HR <b className={`fsm-game__factor ${factorCls}`}>{game.hrFactor.toFixed(2)}×</b></span>
      </div>
      <span className="fsm-game__count">{n} BATTERS</span>
    </div>);

}

const FSM_GROUP_OPTS = [
{ id: "all", label: "All Players", desc: "Every batter in today's slate." },
{ id: "qualified", label: "Qualified", desc: "Batters with 100+ plate appearances (stable sample size)." },
{ id: "elite", label: "Elite Targets", desc: "APEX, ELITE & EDGE tier batters only (model HR% ≥ 9%)." }];
const FSM_BUILDER_GROUP_OPTS = [
{ id: "all", label: "All Players", desc: "Every batter from current JIG-side slate feed." },
{ id: "qualified", label: "Qualified", desc: "Batters with 100+ plate appearances from current scored feed." },
{ id: "elite", label: "Elite Targets", desc: "Inherited top scored tiers from current JIG slate feed; not Builder-native raw ranking." }];

const FSM_FOCUS_OPTS = [
{ id: "all", label: "ALL", desc: "All hitter profiles." },
{ id: "power", label: "POWER", desc: "Sluggers: Barrel% ≥ 4.5 OR SLG ≥ .470." },
{ id: "contact", label: "CONTACT", desc: "Contact hitters: AVG ≥ .255." },
{ id: "matchup", label: "MATCHUP", desc: "Batters in an ELITE or STRONG matchup vs today's pitcher." }];


const FSM_ROLE_OPTS = [
  { id: "prime",     label: "PRIME",     color: "#1aff66", borderColor: "rgba(26,255,102,0.5)" },
  { id: "explosive", label: "EXPLOSIVE", color: "#ff9f1a", borderColor: "rgba(255,159,26,0.5)" },
  { id: "advantage", label: "ADVANTAGE", color: "#3b9eff", borderColor: "rgba(59,158,255,0.5)" },
  { id: "wildcard",  label: "WILDCARD",  color: "#c77dff", borderColor: "rgba(199,125,255,0.5)" },
  { id: "norole",    label: "NO ROLE",   color: "#6b7872", borderColor: "rgba(107,120,114,0.5)" },
];

function FsmRoleFilter({ selRoles, onToggle }) {
  return (
    <div className="fsm-rg">
      <span className="fsm-rg__label">ROLE</span>
      <div className="fsm-rg__opts fsm-rg__opts--role">
        {FSM_ROLE_OPTS.map((r) => {
          const on = selRoles.includes(r.id);
          return (
            <button
              key={r.id}
              className={"fsm-rg__opt fsm-role-opt" + (on ? " is-on" : "")}
              style={on ? { "--role-c": r.color, "--role-b": r.borderColor } : {}}
              title={`Filter: ${r.label} role — AND logic`}
              onClick={() => onToggle(r.id)}>
              <span className="fsm-role-opt__dot" style={{ "--role-c": r.color }} />
              {r.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function FsmRadioGroup({ label, value, onChange, options }) {
  return (
    <div className="fsm-rg">
      <span className="fsm-rg__label">{label}</span>
      <div className="fsm-rg__opts" role="radiogroup" aria-label={label}>
        {options.map((o) =>
        <button
          key={o.id}
          className={"fsm-rg__opt" + (value === o.id ? " is-on" : "")}
          role="radio" aria-checked={value === o.id}
          title={o.label + " — " + o.desc}
          onClick={() => onChange(o.id)}>
          
            <span className="fsm-rg__radio" />{o.label}
          </button>
        )}
      </div>
    </div>);

}

let fsmDragKey = null;

function FsmTable({ rows, cols, showGame, onBatter, onPitch, onReorder, onFront, onSort, sortState, builderMode = false, isJigContext = false, splitScope = 'vs_hand', editMode = false }) {
  const [slipState, setSlipState] = React.useState(() => window.__hrSlip ? window.__hrSlip.getState() : { cardStatus: {} });
  React.useEffect(() => {
    if (!window.__hrSlip) return;
    return window.__hrSlip.subscribe(() => setSlipState(window.__hrSlip.getState()));
  }, []);
  const { cardStatus } = slipState;

  const handleAddLeg = (row) => {
    if (!window.__hrSlip) return;
    const board = isJigContext || builderMode ? 'jig' : (row._board || 'main');
    /* Capture always records RAW model values — never the platoon-lens-adjusted row. */
    const raw = row._raw || row;
    window.__hrSlip.requestAdd({
      player_id:       raw.id,
      name:            raw.name,
      teamAbbr:        raw.teamAbbr,
      team:            raw.teamAbbr,
      pitcher:         raw.pitcher_name,
      pitcher_name:    raw.pitcher_name,
      model_prob:      raw.model_prob,
      tier:            raw.tier,
      model_tier_rank: raw.model_tier_rank,
      board:           board,
      hrprob:          raw.hrprob,
      barrel:          raw.barrel,
      hh:              raw.hh,
      fd_bet_link:     raw.fd_bet_link,
      fd_event_link:   raw.fd_event_link,
      signal_snapshot: fsmBuildSnapshot(raw, board, sortState),
    });
  };

  const thProps = (c) => ({
    draggable: editMode,
    onDragStart: editMode ? (e) => { fsmDragKey = c.key; e.dataTransfer.effectAllowed = "move"; } : undefined,
    onDragOver: editMode ? (e) => { e.preventDefault(); e.currentTarget.classList.add("is-drop"); } : undefined,
    onDragLeave: editMode ? (e) => e.currentTarget.classList.remove("is-drop") : undefined,
    onDrop: editMode ? (e) => { e.preventDefault(); e.currentTarget.classList.remove("is-drop"); if (fsmDragKey && fsmDragKey !== c.key) onReorder(fsmDragKey, c.key); fsmDragKey = null; } : undefined,
    onDoubleClick: () => onSort(c.key),
    title: c.title,
  });
  const arrow = (c) => sortState && sortState.key === c.key ? (sortState.dir === "desc" ? " ▼" : " ▲") : "";
  const bands = [];
  cols.forEach((c) => { const g = c.group || "STATS"; const last = bands[bands.length - 1]; if (last && last.label === g) last.span++; else bands.push({ label: g, span: 1 }); });
  return (
    <table className="fsm-table">
      <colgroup>
        <col style={{ width: "72px" }} /><col style={{ width: "128px" }} /><col style={{ width: "220px" }} />
        {cols.map((c) => <col key={c.key} style={{ width: c.key === "pa" ? "46px" : "60px" }} />)}
        <col style={{ width: "36px" }} />
      </colgroup>
      <thead>
        <tr className="fsm-grouprow">
          <th className="fsm-gband fsm-gband--id" colSpan={3}>BATTER</th>
          {bands.map((b, i) => <th key={i} className={"fsm-gband fsm-gband--" + b.label.toLowerCase()} colSpan={b.span}>{b.label}</th>)}
          <th className="fsm-gband" style={{ width: "36px" }} />
        </tr>
        <tr className="fsm-colhead">
          <th className="fsm-th-tier">{isJigContext ? "JIG TIER" : builderMode ? "MODEL TIER" : "TIER"}</th>
          <th className="fsm-th-player">PLAYER</th>
          <th className="fsm-th-matchup">MATCHUP</th>
          {cols.map((c) =>
          <th key={c.key} className={"fsm-th-stat" + (c.danger ? " fsm-th-danger" : "") + (sortState && sortState.key === c.key ? " is-sorted" : "")} {...thProps(c)}><button type="button" className="fsm-statfront" onClick={(e) => { e.stopPropagation(); onFront(c.key); }} title={c.title} aria-label={`Move ${c.head} to the first stat column`}>{c.head}</button>{arrow(c)}{c.scope === "hand" ? (splitScope === 'vs_hand' ? <span className="fsm-th-scope fsm-th-scope--hand">VS HAND</span> : <span className="fsm-th-scope">SZN</span>) : c.scope === "season" ? <span className="fsm-th-scope">SZN</span> : null}</th>
          )}
          <th className="fsm-th-stat" style={{ width: "36px", textAlign: "center", cursor: "default" }} title="Add to slip">SLIP</th>
        </tr>
      </thead>
      <tbody>
        {(() => {
          const tierCounts = {};
          /* Payload can carry the same player id twice (confirmed + projected
             variants). Duplicate React keys silently break row reordering on
             sort changes, so de-dupe keys with a per-render counter. */
          const keySeen = {};
          return rows.map((r) => {
            let jigLabel = null, jigRank = null;
            if (isJigContext) {
              jigLabel = r.jigTier || "COLD";
              tierCounts[jigLabel] = (tierCounts[jigLabel] || 0) + 1;
              jigRank = tierCounts[jigLabel];
            }
            const kBase = `${r.id != null ? r.id : r.name}-${r.game_pk}`;
            const kN = keySeen[kBase] = (keySeen[kBase] || 0) + 1;
            return <FsmRow key={kN > 1 ? `${kBase}__dup${kN}` : kBase} row={r} cols={cols} showGame={showGame} onBatter={onBatter} onPitch={onPitch} builderMode={builderMode} isJigContext={isJigContext} jigLabel={jigLabel} jigRank={jigRank} onAddLeg={handleAddLeg} slipStatus={cardStatus[r.id || r.name] || 'idle'} sortState={sortState} />;
          });
        })()}
      </tbody>
    </table>);

}

/* ---- detail overlays: Batter Card + Pitch Mix Analysis ---- */
const FSM_BUCKET_COLOR = { ELITE: "#1aff66", STRONG: "#6dffae", AVERAGE: "#b8c2c0", WEAK: "#ff8a93", DANGER: "#ff3344", NA: "#6b7872", NEUTRAL: "#b8c2c0" };
const FSM_AEE_PITCH = {
  FF: "4S", FT: "2S", SI: "SNK", FC: "CUT", FS: "SPL",
  FO: "FRK", SL: "SLD", SW: "SWP", ST: "SWP", SV: "SLV",
  CU: "CB", KC: "KC", CH: "CH", SC: "SCR", KN: "KN"
};
const FSM_AEE_LABEL_COLOR = {
  "ARSENAL MISMATCH": FSM_BUCKET_COLOR.DANGER,
  "PITCH MIX EXPLOIT": FSM_BUCKET_COLOR.ELITE,
  "SOFT EDGE": "#ffb020",
  "NEUTRAL": FSM_BUCKET_COLOR.NEUTRAL,
  "DATA GAP": FSM_BUCKET_COLOR.NA,
  "UNKNOWN": FSM_BUCKET_COLOR.NA
};
function fsmAeeIsGap(row) {
  return row.arsenal_edge_score == null || row.arsenal_edge_label === "DATA GAP";
}
function fsmAeeLabel(row) {
  if (fsmAeeIsGap(row)) return "DATA GAP";
  if (row.arsenal_edge_label) return row.arsenal_edge_label;
  const score = Number(row.arsenal_edge_score);
  if (Number.isNaN(score)) return "UNKNOWN";
  if (score >= 8) return "ARSENAL MISMATCH";
  if (score >= 6) return "PITCH MIX EXPLOIT";
  if (score >= 4) return "SOFT EDGE";
  return "NEUTRAL";
}
function fsmAeeColor(label) {
  return FSM_AEE_LABEL_COLOR[label] || FSM_BUCKET_COLOR.NEUTRAL;
}
function fsmAeeScoreText(row) {
  return fsmAeeIsGap(row) ? "—" : Number(row.arsenal_edge_score).toFixed(1);
}
function fsmAeeKeyPitch(row) {
  const code = row.arsenal_edge_key_pitch;
  return code ? (FSM_AEE_PITCH[code] || code) : null;
}
const fsmColFor = (key) => FSM_COLS.find((c) => c.key === key);
function fsmStatColor(key, row) {
  const c = fsmColFor(key);
  if (!c) return "#b8c2c0";
  return FSM_BUCKET_COLOR[fsmBucket(c, row[key])] || "#b8c2c0";
}
function fsmStatVal(key, row) {
  const c = fsmColFor(key);
  const v = row[key];
  return v == null ? "—" : c.fmt(v);
}

/* Arsenal semantic scaling — HR-threat perspective.
   Whiff%/K% high = pitcher suppression (green-safe).
   HR/HH% high = danger (red). Null → neutral dim. */
function fsmArsWhiffCls(v) {
  if (v == null) return "fsm-pt__num";
  if (v >= 32) return "fsm-ht is-strong";
  if (v <= 15) return "fsm-ht is-danger";
  if (v <= 20) return "fsm-ht is-weak";
  return "fsm-pt__num";
}
function fsmArsHrCls(v) {
  if (v == null) return "fsm-pt__num";
  if (v >= 3) return "fsm-ht is-danger";
  if (v >= 2) return "fsm-ht is-weak";
  return "fsm-pt__num";
}
function fsmArsKCls(v) {
  if (v == null) return "fsm-pt__num";
  if (v >= 30) return "fsm-ht is-strong";
  if (v <= 15) return "fsm-ht is-danger";
  if (v <= 20) return "fsm-ht is-weak";
  return "fsm-pt__num";
}
function fsmArsHhCls(v) {
  if (v == null) return "fsm-pt__num";
  if (v >= 45) return "fsm-ht is-danger";
  if (v >= 38) return "fsm-ht is-weak";
  if (v <= 27) return "fsm-ht is-strong";
  return "fsm-pt__num";
}
/* Batter vs pitch semantic scaling — batter-positive perspective. */
function fsmBvpHrCls(v) {
  if (v == null || v === 0) return "fsm-pt__num";
  if (v >= 2) return "fsm-ht is-strong";
  return "fsm-ht is-avg";
}
function fsmBvpKCls(v) {
  if (v == null) return "fsm-pt__num";
  if (v <= 14) return "fsm-ht is-strong";
  if (v >= 30) return "fsm-ht is-weak";
  return "fsm-pt__num";
}

// Module-level cache for on-demand pitcher detail fetches.
const FSM_PITCHER_DETAIL_CACHE = new Map();

const FSM_PITCH_NAMES = {
  FF: "4-Seam", SI: "Sinker", FC: "Cutter", SL: "Slider", ST: "Sweeper",
  CH: "Changeup", FS: "Splitter", CU: "Curveball", KC: "Knuckle-Curve",
  KN: "Knuckleball", EP: "Eephus", SC: "Screwball", FO: "Forkball",
};

function fsmPitchName(code) {
  return FSM_PITCH_NAMES[code] || code;
}

function FsmStat({ label, value, color }) {
  return <div className="fsm-stat"><span className="fsm-stat__l">{label}</span><span className="fsm-stat__v" style={{ color }}>{value}</span></div>;
}

function FsmBatterCard({ row, onClose, onPitch, builderMode = false }) {
  /* Hero MODEL HR PROB is always the raw model value, never the platoon-lens-adjusted row. */
  const rawRow = row._raw || row;
  const t = FSM_TIERS[row.tier] || FSM_TIERS.COLD;
  const m = FSM_MATCHUP[row.quality] || FSM_MATCHUP.AVG;
  const game = getFSMGames().find((g) => g.id === row.gameId);
  const oppTeam = game ? (game.teams.find((t) => t !== row.teamAbbr) || "OPP") : "OPP";
  const pitcherDisplay = row.pitcher_name ? row.pitcher_name : "TBD";
  const pitcherHand = row.pitcher_hand || "?";
  const pitcherConfirmed = row.pitcher_confirmed === true;
  const groups = [
  { title: "POWER & CONTACT — SEASON", keys: ["avg", "slg", "babip", "xwoba", "barrel", "hrpa"] },
  { title: "BATTED-BALL PROFILE — SEASON", keys: ["ev", "la", "hh", "gb", "ld", "pull", "center"] }];

  return (
    <div className="fsm-card">
      <div className="fsm-card__head">
        <span className="fsm-tier fsm-tier--lg" style={{ "--tc": t.color, "--tg": t.glow }}>
          <span className="fsm-tier__icon"><FsmTierIcon tier={row.tier} /></span>
          <span className="fsm-tier__label">{row.tier}</span>
        </span>
        <div className="fsm-card__id">
          <div className="fsm-card__name">{row.name}</div>
          <div className="fsm-card__meta">{row.teamAbbr} · BATS {row.bats}{game ? ` · ${game.away} @ ${game.home}` : ""}</div>
        </div>
        <div className="fsm-card__prob">
          <span className="fsm-card__probval" style={{ color: t.color }}>{rawRow.hrprob.toFixed(1)}%</span>
          <span className="fsm-card__problbl">{builderMode ? "INHERITED SCORE FEED" : "MODEL HR PROB"}</span>
        </div>
        <button className="fsm-card__close" onClick={onClose} aria-label="Close">✕</button>
      </div>
      <div className="fsm-card__matchup">
        <FsmGauge fraction={fsmThreatFill(row.model_prob)} color={t.color} size="lg" />
        <div className="fsm-card__mtext">
          <span className="fsm-card__mq" style={{ color: m.color }}>{row.quality} THREAT{row.pitcherVuln === "TARGET" && <span style={{ color: "#1aff66", marginLeft: "6px", fontWeight: 700 }} title="Pitcher allows 2.2+ HR/9 — most hittable arms on the slate">· TARGET</span>}</span>
          <span className="fsm-card__msub">vs <span className="fsm-pitcher-name">{pitcherDisplay}</span>{!pitcherConfirmed && (<span className="fsm-tbd-badge">TBD</span>)} ({oppTeam} · {pitcherHand}HP) · OPP HR/9 {fsmStatVal("opphr", row)}{game ? ` · PARK HR ${game.hrFactor.toFixed(2)}×` : ""}</span>
        </div>
        <button className="fsm-card__pitchbtn" onClick={onPitch}>PITCH MIX ANALYSIS →</button>
      </div>
      <div className="fsm-card__sec">
        <div className="fsm-card__sectitle">HAND BREAKDOWN — SEASON · vs LHP · vs RHP</div>
        <div className="fsm-hb">
          {/* SEASON column */}
          <div className="fsm-hb__col">
            <div className="fsm-hb__label">SEASON</div>
            <div className="fsm-hb__hr">{rawRow.hr != null ? rawRow.hr + " HR" : "—"}</div>
            <div className="fsm-hb__pa">{rawRow.pa != null ? rawRow.pa + " PA" : "—"}</div>
            <div className="fsm-hb__rates">
              <div><span className="fsm-hb__rval">{fsmS3(rawRow.avg)}</span><span className="fsm-hb__rlbl">AVG</span></div>
              <div><span className="fsm-hb__rval">{fsmS3(rawRow.slg)}</span><span className="fsm-hb__rlbl">SLG</span></div>
              <div><span className="fsm-hb__rval">{rawRow.iso != null ? fsmS3(rawRow.iso) : (rawRow.slg != null && rawRow.avg != null ? fsmS3(+(rawRow.slg - rawRow.avg).toFixed(3)) : "—")}</span><span className="fsm-hb__rlbl">xISO</span></div>
            </div>
          </div>
          {/* vs LHP / vs RHP columns */}
          {["L", "R"].map((h) => {
            const pre = h === "L" ? "vs_lhp" : "vs_rhp";
            const faced = rawRow.vs_hand === h;
            const pa = rawRow[pre + "_pa"];
            const hr = rawRow[pre + "_hr"];
            const avg = rawRow[pre + "_avg"];
            const slg = rawRow[pre + "_slg"];
            const iso = rawRow[pre + "_iso"] != null ? rawRow[pre + "_iso"]
              : (slg != null && avg != null ? +(slg - avg).toFixed(3) : null);
            const has = pa != null && pa > 0;
            const thin = has && pa < FSM_VS_HAND_MIN_PA;
            return (
              <div key={h} className={"fsm-hb__col" + (faced ? " fsm-hb__col--faced" : "")}>
                <div className="fsm-hb__label">
                  vs {h}HP
                  {faced && <span className="fsm-hb__tonight">TONIGHT</span>}
                  {thin && <span className="fsm-scope fsm-scope--thin" style={{ display: "inline", fontSize: "7px" }}>THIN</span>}
                </div>
                {has ? (
                  <>
                    <div className="fsm-hb__hr">{hr != null ? hr + " HR" : "—"}</div>
                    <div className="fsm-hb__pa">{pa} PA</div>
                    <div className="fsm-hb__rates">
                      <div><span className="fsm-hb__rval">{fsmS3(avg)}</span><span className="fsm-hb__rlbl">AVG</span></div>
                      <div><span className="fsm-hb__rval">{fsmS3(slg)}</span><span className="fsm-hb__rlbl">SLG</span></div>
                      <div><span className="fsm-hb__rval">{fsmS3(iso)}</span><span className="fsm-hb__rlbl">ISO</span></div>
                    </div>
                  </>
                ) : (
                  <div className="fsm-split__line fsm-split__line--na">no split data</div>
                )}
              </div>
            );
          })}
        </div>
        {!rawRow.vs_hand && <div className="fsm-split__tbd" style={{ marginTop: 6 }}>Pitcher TBD / unconfirmed — no faced hand; board shows SZN numbers</div>}
      </div>
      {groups.map((g) =>
      <div className="fsm-card__sec" key={g.title}>
          <div className="fsm-card__sectitle">{g.title}</div>
          <div className="fsm-card__stats">
            {g.keys.map((k) => <FsmStat key={k} label={fsmColFor(k).head} value={fsmStatVal(k, rawRow)} color={fsmStatColor(k, rawRow)} />)}
          </div>
        </div>
      )}
      <div className="fsm-card__foot">
        <span className="fsm-card__env">{game ? `${game.park} · ${game.weather} · WIND ${game.wind}` : ""}</span>
        {!builderMode && <a className="fsm-card__fd" href={fsmFanDuelUrl(row.name)} target="_blank" rel="noopener" onClick={(e) => fsmOpenFanDuelSearch(e, row.name)}>+ ADD TO FANDUEL</a>}
      </div>
    </div>);

}


const fsmS3 = (v) => v == null ? "—" : v.toFixed(3).replace(/^0/, "");
const fsmP1 = (v) => v == null ? "—" : v.toFixed(1) + "%";

/* Display-only stat valence. Thresholds are [green, amber]; lower direction is
   for contact-positive stats such as K%. No scoring or source data is changed. */
function hrStatValence(value, thresholds, direction = "higher") {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return undefined;
  const [green, amber] = thresholds;
  if (direction === "binary") return numeric >= green ? "var(--green-500)" : "var(--fg-3)";
  if (direction === "lower") {
    return numeric <= green ? "var(--green-500)" : numeric <= amber ? "var(--amber-500)" : "var(--red-500)";
  }
  return numeric >= green ? "var(--green-500)" : numeric >= amber ? "var(--amber-500)" : "var(--red-500)";
}

function fsmHeatClass(v, hi) {
  if (v == null) return "is-na";
  return v >= hi[0] ? "is-elite" : v >= hi[1] ? "is-strong" : v >= hi[2] ? "is-avg" : v >= hi[3] ? "is-weak" : "is-danger";
}

function FsmStatRail({ title, stats }) {
  return (
    <div className="fsm-h2h__rail">
      <div className="fsm-h2h__railtitle">{title}</div>
      {stats.map(([l, v, hot]) =>
      <div className="fsm-h2h__railrow" key={l}><span>{l}</span><b style={hot ? { color: hot } : null}>{v}</b></div>
      )}
    </div>);

}

/* Arsenal table — pitcher's pitch mix with real Savant stats */
function FsmArsenalTable({ title, arsenal, pitchStats }) {
  if (!arsenal || arsenal.length === 0) return (
    <div className="fsm-pt fsm-pt--red fsm-pt--arsenal">
      <div className="fsm-pt__title">{title}</div>
      <div className="fsm-pt__empty">No arsenal data available</div>
    </div>
  );
  return (
    <div className="fsm-pt fsm-pt--red fsm-pt--arsenal">
      <div className="fsm-pt__title">{title}</div>
      <div className="fsm-pt__grid">
        <div className="fsm-pt__hd"><span>PITCH TYPE</span><span>USAGE</span><span>VELO</span><span>WHIFF%</span><span>HR</span><span>K%</span><span>HH%</span></div>
        {arsenal.map((p, i) => {
          const ps = pitchStats[p.code] || {};
          const velo = p.velo ?? ps.avg_speed;
          const hrVal = ps.hr != null ? ps.hr : null;
          const kPct = ps.k_pct != null ? ps.k_pct * 100 : null;
          const hh = ps.display_hh != null ? ps.display_hh * 100 : null;
          return (
            <div className="fsm-pt__row" key={i}>
              <span className="fsm-pt__type">{p.name || fsmPitchName(p.code)}</span>
              <span className="fsm-pt__usage"><span className="fsm-pt__bar" style={{ width: Math.min(100, p.usage ?? 0) + "%" }} /><i>{p.usage != null ? p.usage.toFixed(1) : "—"}%</i></span>
              <span className="fsm-pt__num">{velo != null ? velo.toFixed(1) : "—"}</span>
              <span className={fsmArsWhiffCls(p.whiff)}>{p.whiff != null ? p.whiff.toFixed(1) + "%" : "—"}</span>
              <span className={fsmArsHrCls(hrVal)}>{hrVal != null ? hrVal : "—"}</span>
              <span className={fsmArsKCls(kPct)}>{kPct != null ? kPct.toFixed(1) + "%" : "—"}</span>
              <span className={fsmArsHhCls(hh)}>{hh != null ? hh.toFixed(1) + "%" : "—"}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* Batter vs pitch type table — real Savant batter splits */
function FsmBatterVsPitchTable({ title, bvp, arsenal }) {
  const pitchCodes = arsenal && arsenal.length > 0
    ? arsenal.map((p) => p.code)
    : Object.keys(bvp || {});
  const rows = pitchCodes.filter((c) => bvp[c]).map((c) => ({ code: c, ...bvp[c] }));
  if (rows.length === 0) return (
    <div className="fsm-pt fsm-pt--blue fsm-pt--bvp">
      <div className="fsm-pt__title">{title}</div>
      <div className="fsm-pt__empty">No batter-vs-pitch data available</div>
    </div>
  );
  return (
    <div className="fsm-pt fsm-pt--blue fsm-pt--bvp">
      <div className="fsm-pt__title">{title}</div>
      <div className="fsm-pt__grid">
        <div className="fsm-pt__hd"><span>PITCH TYPE</span><span>PA</span><span>BA</span><span>SLG</span><span>HR</span><span>K%</span></div>
        {rows.map((p, i) => {
          const ba = parseFloat(p.ba) || null;
          const slg = parseFloat(p.slg) || null;
          const kPct = p.k_pct != null ? p.k_pct * 100 : null;
          const smallSample = (p.pa || 0) < 10;
          return (
            <div className={"fsm-pt__row" + (smallSample ? " fsm-pt__row--dim" : "")} key={i}>
              <span className="fsm-pt__type">{fsmPitchName(p.code)}{smallSample ? <span className="fsm-ss-flag" title="Small sample">·</span> : null}</span>
              <span className="fsm-pt__num">{p.pa != null ? p.pa : "—"}</span>
              <span className={"fsm-ht " + fsmHeatClass(ba, [0.320, 0.275, 0.230, 0.180])}>{ba != null ? ba.toFixed(3).replace(/^0/, "") : "—"}</span>
              <span className={"fsm-ht " + fsmHeatClass(slg, [0.520, 0.430, 0.350, 0.270])}>{slg != null ? slg.toFixed(3).replace(/^0/, "") : "—"}</span>
              <span className={fsmBvpHrCls(p.hr)}>{p.hr != null ? p.hr : "—"}</span>
              <span className={fsmBvpKCls(kPct)}>{kPct != null ? kPct.toFixed(1) + "%" : "—"}</span>
            </div>
          );
        })}
      </div>
      {rows.some((r) => (r.pa || 0) < 10) && <div className="fsm-pt__note">· = small sample (&lt;10 PA)</div>}
    </div>
  );
}

function FsmPitchMix({ row, onClose, onBatter, builderMode = false }) {
  row = row._raw || row; // untagged stat reads here stay season/raw-scoped
  const [detail, setDetail] = React.useState(null);
  const [fetchState, setFetchState] = React.useState("loading");

  const pitcherId = row.pitcher_id;
  const batterId = row.id;
  const batterSide = row.bats || "";
  const pitcherHand = row.pitcher_hand || "";

  React.useEffect(() => {
    const cacheKey = `${pitcherId}:${batterId}:${batterSide}`;
    if (FSM_PITCHER_DETAIL_CACHE.has(cacheKey)) {
      setDetail(FSM_PITCHER_DETAIL_CACHE.get(cacheKey));
      setFetchState("done");
      return;
    }
    if (!pitcherId) {
      setFetchState("error");
      return;
    }
    const url = `https://mlb-hr-api.fly.dev/api/pitcher-detail?pitcher_id=${encodeURIComponent(pitcherId)}&batter_id=${encodeURIComponent(batterId || 0)}&batter_side=${encodeURIComponent(batterSide)}&pitcher_hand=${encodeURIComponent(pitcherHand)}`;
    fetch(url)
      .then((r) => r.json())
      .then((data) => {
        FSM_PITCHER_DETAIL_CACHE.set(cacheKey, data);
        setDetail(data);
        setFetchState("done");
      })
      .catch(() => setFetchState("error"));
  }, [pitcherId, batterId]);

  const game = getFSMGames().find((g) => g.id === row.gameId);
  const oppTeam = game ? (game.teams.find((t) => t !== row.teamAbbr) || "OPP") : "OPP";
  const initials = (n) => (n || "?").replace("…", "").split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase();

  const pitcherName = row.pitcher_name || "TBD";
  const pLast = pitcherName.replace("…", "").split(" ").slice(-1)[0];
  const bLast = (row.name || "").replace("…", "").split(" ").slice(-1)[0];

  // Effective batter side display (switch hitters face opposite hand)
  const batHand = batterSide === "S" ? (pitcherHand === "L" ? "R" : "L") : batterSide;

  const pColor = TEAM_COLOR[oppTeam] || "#ff3344";
  const bColor = TEAM_COLOR[row.teamAbbr] || "#3b6fff";

  const hr9 = row.pitcher_hr9 != null ? row.pitcher_hr9 : null;
  const pTierLabel = hr9 != null ? (hr9 >= 1.45 ? "HR TARGET" : hr9 >= 1.05 ? "VULNERABLE" : "TOUGH") : "—";
  const pTierColor = pTierLabel === "HR TARGET" ? "#1aff66" : pTierLabel === "VULNERABLE" ? "#ffb020" : "#ff3344";

  const iso = (row.slg != null && row.avg != null) ? +(row.slg - row.avg).toFixed(3) : null;

  const h2h = detail && detail.h2h && detail.h2h.pa ? detail.h2h : null;
  const arsenal = detail ? (detail.arsenal || []) : [];
  const pitchStats = detail ? (detail.pitch_stats || {}) : {};
  const bvp = detail ? (detail.batter_vs_pitches || {}) : {};

  return (
    <div className="fsm-card fsm-card--h2h">
      <button className="fsm-card__close fsm-card__close--abs" onClick={onClose} aria-label="Close">✕</button>

      <div className="fsm-h2h__top">
        {/* PITCHER */}
        <div className="fsm-h2h__side" style={{ "--tc": pColor }}>
          <div className="fsm-h2h__nameblock">
            <div className="fsm-h2h__team">{oppTeam}</div>
            <div className="fsm-h2h__name">{pitcherName}</div>
            <span className="fsm-h2h__badge">{pitcherHand || "?"}HP</span>
          </div>
          {arsenal.length === 0 ? (
            <div className="fsm-ah">
              <div className="fsm-ah__title">ARSENAL</div>
              <div className="fsm-ah__empty">{fetchState === "loading" ? "Arsenal loading…" : "No arsenal data"}</div>
            </div>
          ) : (
            <div className="fsm-ah">
              <div className="fsm-ah__title">ARSENAL</div>
              {[...arsenal].sort((a, b) => (b.usage ?? 0) - (a.usage ?? 0)).map((p, i) => {
                const ps = pitchStats[p.code] || {};
                const velo = p.velo ?? ps.avg_speed;
                const isExploit = row.arsenal_edge_key_pitch && p.code === row.arsenal_edge_key_pitch;
                return (
                  <div key={i} className={"fsm-ah__row" + (isExploit ? " fsm-ah__row--hunt" : "")}>
                    <div className="fsm-ah__pname-wrap">
                      <span className="fsm-ah__pname">{p.name || fsmPitchName(p.code)}</span>
                      {isExploit && <span className="fsm-ah__hunt">HUNT THIS</span>}
                    </div>
                    <span className="fsm-ah__bar-wrap"><span className="fsm-ah__bar" style={{ width: Math.min(100, p.usage ?? 0) + "%" }} /></span>
                    <span className="fsm-ah__velo">{velo != null ? velo.toFixed(0) : "—"}</span>
                    <span className="fsm-ah__whiff">{p.whiff != null ? p.whiff.toFixed(0) + "%" : "—"}</span>
                  </div>
                );
              })}
            </div>
          )}
          <FsmStatRail title="PITCHER SEASON STATS" stats={[
            ["ERA",    row.pitcher_era   != null ? row.pitcher_era.toFixed(2)   : "—"],
            ["WHIP",   row.pitcher_whip  != null ? row.pitcher_whip.toFixed(2)  : "—"],
            ["K%",     row.pitcher_k_pct != null ? row.pitcher_k_pct.toFixed(1) : "—"],
            ["BB%",    row.pitcher_bb_pct != null ? row.pitcher_bb_pct.toFixed(1) : "—"],
            ["HR/9",   hr9 != null ? hr9.toFixed(2) : "—", hr9 != null && hr9 >= 1.45 ? "#1aff66" : null],
            ["BARREL%", row.pitcher_barrel_allowed != null ? (row.pitcher_barrel_allowed * 100).toFixed(1) : "—"],
            ["HH%",    row.pitcher_hh_allowed != null ? (row.pitcher_hh_allowed * 100).toFixed(1) : "—"],
          ]} />
          <div className="fsm-h2h__tier"><span>PITCHER TIER</span><b style={{ color: pTierColor }}>{pTierLabel}</b></div>
        </div>

        {/* CENTER — H2H + loading state */}
        <div className="fsm-h2h__center">
          {fetchState === "loading" && (
            <div className="fsm-h2h__loading">Loading pitch data…</div>
          )}
          {fetchState === "error" && !pitcherId && (
            <div className="fsm-h2h__loading">Pitcher TBD — no detail available</div>
          )}
          {fetchState === "error" && pitcherId && (
            <div className="fsm-h2h__loading">Fetch error — showing available stats</div>
          )}
          <div className="fsm-h2h__h2h">
            <div className="fsm-h2h__h2htitle">HEAD TO HEAD <span>CAREER · {bLast} vs {pLast}</span></div>
            {h2h ? (
              <div className="fsm-h2h__h2hstrip">
                {[
                  ["PA",  h2h.pa],
                  ["AVG", h2h.avg || "—"],
                  ["SLG", h2h.slg || "—"],
                  ["HR",  h2h.hr],
                  ["K",   h2h.k],
                  ["OPS", h2h.ops || "—"],
                ].map(([l, v]) =>
                  <div key={l}><span>{l}</span><b>{v}</b></div>
                )}
              </div>
            ) : (
              <div className="fsm-h2h__h2hstrip fsm-h2h__h2hstrip--empty">
                {fetchState === "done" ? "No career H2H on record" : "—"}
              </div>
            )}
            {h2h && h2h.pa < 10 && (
              <div className="fsm-pt__note">Small sample ({h2h.pa} PA) — treat with caution</div>
            )}
          </div>
          <div className="fsm-h2h__btier">
            <div><span>MODEL TIER</span><b>{row.tier}</b></div>
            <div><span>MODEL HR PROB</span><b style={{ color: "#1aff66" }}>{row.hrprob != null ? row.hrprob.toFixed(1) + "%" : "—"}</b></div>
            <div><span>{builderMode ? "SOURCE FEED ODDS" : "HR ODDS"}</span><b style={{ color: "#ffb020" }}>{row.odds || "—"}</b></div>
          </div>
        </div>

        {/* BATTER */}
        <div className="fsm-h2h__side fsm-h2h__side--right" style={{ "--tc": bColor }}>
          <div className="fsm-h2h__nameblock">
            <div className="fsm-h2h__team">{row.teamAbbr}</div>
            <div className="fsm-h2h__name">{row.name}</div>
            <span className="fsm-h2h__badge">BATS {batterSide}</span>
          </div>
          <div className="fsm-h2h__portrait"><span>{initials(row.name)}</span></div>
          <FsmStatRail title={`vs ${pitcherHand || "?"}HP`} stats={[
            ["AVG",     fsmS3(row.avg)],
            ["ISO",     fsmS3(iso)],
            ["HR",      row.hr != null ? row.hr : "—", "#1aff66"],
            ["K%",      row.kpct != null ? row.kpct.toFixed(1) : "—"],
            ["BARREL%", row.barrel != null ? row.barrel.toFixed(1) : "—"],
            ["EV",      row.ev != null ? row.ev.toFixed(1) : "—"],
            ["xwOBA",   fsmS3(row.xwoba)],
          ]} />
          <div className="fsm-h2h__tier"><span>MODEL TIER</span><b style={{ color: (FSM_TIERS[row.tier] || FSM_TIERS.COLD).color }}>{row.tier}</b></div>
        </div>
      </div>

      <div className="fsm-h2h__tables">
        <FsmArsenalTable
          title={`${pLast} ARSENAL vs ${batHand}HB`}
          arsenal={arsenal}
          pitchStats={pitchStats}
        />
        <FsmBatterVsPitchTable
          title={`${bLast} vs ${pitcherHand || "?"}HP — BY PITCH TYPE`}
          bvp={bvp}
          arsenal={arsenal}
        />
      </div>

      <div className="fsm-card__foot">
        <button className="fsm-card__pitchbtn" onClick={onBatter}>← BATTER CARD</button>
        {!builderMode && <a className="fsm-card__fd" href={fsmFanDuelUrl(row.name)} target="_blank" rel="noopener" onClick={(e) => fsmOpenFanDuelSearch(e, row.name)}>+ ADD {bLast.toUpperCase()} TO FANDUEL</a>}
      </div>
    </div>
  );
}

/* ============================================================
   ARSENAL EDGE INTEL — FsmArsenalEdgeIntel
   Replaces FsmPitchMix as the modal.type==="pitch" destination.
   FsmPitchMix is left below (unrouted) for easy rollback.
   ============================================================ */
function FsmArsenalEdgeIntel({ row, onClose, onBatter, builderMode = false, isJigContext = false }) {
  row = row._raw || row; // untagged stat reads here stay season/raw-scoped
  const bvpColsStorageKey = 'hr-engine:aei-bvp-cols:v1';
  const bvpDefaultCols = ['pa', 'ba', 'slg', 'iso', 'hr', 'hr_pct', 'k_pct', 'hh_pct'];
  const bvpCols = [
    { key: 'pa',     head: 'PA',        title: 'Plate appearances versus this pitch type', fmt: b => String(b.pa),                                      gate: b => b && b.pa != null && b.pa > 0 },
    { key: 'ba',     head: 'BA',        title: 'Batting average versus this pitch type (minimum 3 AB)', fmt: b => Number(b.ba).toFixed(3),             gate: b => b && b.ba != null },
    { key: 'slg',    head: 'SLG',       title: 'Slugging percentage versus this pitch type (minimum 3 AB)', fmt: b => Number(b.slg).toFixed(3),        gate: b => b && b.slg != null },
    { key: 'iso',    head: 'ISO',       title: 'ISO versus this pitch type (SLG minus BA; minimum 3 AB)', fmt: b => (Number(b.slg) - Number(b.ba)).toFixed(3), gate: b => b && b.ba != null && b.slg != null },
    { key: 'hr',     head: 'HR',        title: 'Home runs vs this pitch type (count)', fmt: b => String(b.hr) },
    { key: 'hr_pct', head: 'HR%',       title: 'Home-run rate versus this pitch type (minimum 10 PA)', fmt: b => (Number(b.hr || 0) / Number(b.pa) * 100).toFixed(1) + '%', gate: b => b && b.pa != null && b.pa >= 10 },
    { key: 'k_pct',  head: 'K%',        title: 'Strikeout rate versus this pitch type (minimum 5 PA)', fmt: b => (Number(b.k_pct) * 100).toFixed(0) + '%', gate: b => b && b.k_pct != null },
    { key: 'hh_pct', head: 'HH% VS PT', title: 'Hard-hit rate versus this pitch type (minimum 5 contacts)', fmt: b => (Number(b.display_hh) * 100).toFixed(1) + '%', gate: b => b && b.display_hh != null },
  ];
  const readBvpColumns = () => {
    try {
      const saved = window.localStorage.getItem(bvpColsStorageKey);
      if (!saved) return bvpDefaultCols;
      const keys = JSON.parse(saved);
      if (!Array.isArray(keys)) return bvpDefaultCols;
      const valid = keys.filter(key => bvpCols.some(col => col.key === key));
      return valid.length === keys.length ? valid : bvpDefaultCols;
    } catch { return bvpDefaultCols; }
  };
  const [detail, setDetail] = React.useState(null);
  const [fetchState, setFetchState] = React.useState("loading");
  const [activeBvpCols, setActiveBvpCols] = React.useState(() => new Set(readBvpColumns()));
  const visibleBvpCols = bvpCols.filter(col => activeBvpCols.has(col.key));
  const bvpGridTemplate = `minmax(96px, 1.25fr) repeat(${visibleBvpCols.length}, minmax(52px, 0.7fr))`;
  const bvpGridMinWidth = 96 + (visibleBvpCols.length * 52);
  const recentGridTemplate = "minmax(84px, 1.4fr) repeat(4, minmax(46px, 0.7fr))";
  const recentGridMinWidth = 268;
  const toggleBvpCol = key => setActiveBvpCols(prev => { const next = new Set(prev); next.has(key) ? next.delete(key) : next.add(key); try { window.localStorage.setItem(bvpColsStorageKey, JSON.stringify([...next])); } catch {} return next; });

  const pitcherId  = row.pitcher_id;
  const batterId   = row.id;
  const batterSide = row.bats || "";
  const pitcherHand = row.pitcher_hand || "";

  React.useEffect(() => {
    const cacheKey = `${pitcherId}:${batterId}:${batterSide}`;
    if (FSM_PITCHER_DETAIL_CACHE.has(cacheKey)) {
      setDetail(FSM_PITCHER_DETAIL_CACHE.get(cacheKey));
      setFetchState("done");
      return;
    }
    if (!pitcherId) { setFetchState("no-pitcher"); return; }
    const url = `https://mlb-hr-api.fly.dev/api/pitcher-detail?pitcher_id=${encodeURIComponent(pitcherId)}&batter_id=${encodeURIComponent(batterId || 0)}&batter_side=${encodeURIComponent(batterSide)}&pitcher_hand=${encodeURIComponent(pitcherHand)}`;
    fetch(url)
      .then(r => r.json())
      .then(data => { FSM_PITCHER_DETAIL_CACHE.set(cacheKey, data); setDetail(data); setFetchState("done"); })
      .catch(() => setFetchState("error"));
  }, [pitcherId, batterId]);

  const [slipSt, setSlipSt] = React.useState(() => window.__hrSlip ? window.__hrSlip.getState() : { cardStatus: {} });
  React.useEffect(() => {
    if (!window.__hrSlip) return;
    return window.__hrSlip.subscribe(() => setSlipSt(window.__hrSlip.getState()));
  }, []);

  const arsenal    = detail ? (detail.arsenal || []) : [];
  const pitchStats = detail ? (detail.pitch_stats || {}) : {};
  const bvp        = detail ? (detail.batter_vs_pitches || {}) : {};
  const pitcherRecent = detail && Array.isArray(detail.pitcher_recent) ? detail.pitcher_recent : [];
  // TODO: exclude PH-only games when `started` field becomes available from MLB StatsAPI
  const batterRecent  = detail && Array.isArray(detail.batter_recent) ? detail.batter_recent.filter(g => (g.pa ?? 0) >= 1) : [];
  const h2h        = detail && detail.h2h && detail.h2h.pa ? detail.h2h : null;

  const keyPitch     = row.arsenal_edge_key_pitch || null;
  const keyPitchName = keyPitch ? (fsmPitchName(keyPitch) || keyPitch) : "—";
  const isGap        = row.arsenal_edge_score == null || row.arsenal_edge_label === "DATA GAP";
  const score        = row.arsenal_edge_score;
  const edgeLabel    = row.arsenal_edge_label || (isGap ? "DATA GAP" : "—");
  const edgeDisplayLabel = ({ WATCH: "LEAN", "LIVE EDGE": "FAVORABLE" })[edgeLabel] || edgeLabel;
  const confidence   = row.arsenal_edge_confidence;


  /* BARREL PATH — display band derived from row.barrel; NOT a model output, NOT numeric precision */
  const barrelBand = (() => {
    const b = row.barrel;
    if (b == null) return { label: "—",        cls: "" };
    if (b >= 10)   return { label: "PRIME", cls: "v-prime" };
    if (b >= 7)    return { label: "PLUS",  cls: "v-plus" };
    if (b >= 4)    return { label: "EVEN",  cls: "v-even" };
    if (b >= 2)    return { label: "THIN",  cls: "v-thin" };
    return               { label: "FLAT",  cls: "v-flat" };
  })();

  /* MODEL TIER — inherited MAIN probability tier, displayed verbatim. */
  const modelTier = row.tier || "—";
  const modelTierColor = (FSM_TIERS[row.tier] || FSM_TIERS.COLD).color;

  const h2hTrust  = !h2h ? "NO DATA" : h2h.pa < 10 ? "VERY LOW" : h2h.pa < 30 ? "LOW" : "MODERATE";
  const h2hSigCls = !h2h ? "v-flat" : h2h.pa < 10 ? "v-thin" : (h2h.hr > 0 ? "v-plus" : "v-thin");
  const h2hSigLbl = !h2h ? "NO DATA" : h2h.pa < 10 ? "THIN" : (h2h.hr > 0 ? "PLUS" : "THIN");
  const exploitCls = isGap ? "v-flat" : score >= 8 ? "v-prime" : score >= 6 ? "v-plus" : score >= 4 ? "v-even" : "v-flat";
  const exploitLbl = isGap ? "—" : score >= 8 ? "PRIME" : score >= 6 ? "PLUS" : score >= 4 ? "EVEN" : "FLAT";
  const hhBand = row.hh == null ? { label: "—", cls: "" }
    : row.hh >= 45 ? { label: "PLUS", cls: "v-plus" }
    : row.hh >= 38 ? { label: "EVEN", cls: "v-even" }
    : { label: "THIN", cls: "v-thin" };

  const pitcherName = row.pitcher_name || "TBD";
  const batterName  = row.name || row.player || "—";
  const batHand = batterSide === "S" ? (pitcherHand === "L" ? "R" : "L") : batterSide;
  const pLast   = pitcherName.replace("…", "").split(" ").slice(-1)[0];
  const bLast   = batterName.replace("…", "").split(" ").slice(-1)[0];
  const pInit   = pitcherName.replace("…","").split(" ").map(w => w[0] || "").join("").slice(0,2).toUpperCase();
  const bInit   = batterName.replace("…","").split(" ").map(w => w[0] || "").join("").slice(0,2).toUpperCase();

  const hasBvp   = Object.values(bvp).some(b => b && b.pa > 0);
  const anySmall = hasBvp && Object.values(bvp).some(b => b && b.pa > 0 && b.pa < 10);
  const arsorted = [...arsenal].sort((a, b) => (b.usage ?? 0) - (a.usage ?? 0));

  const iso = row.iso != null ? row.iso
    : (row.slg != null && row.avg != null ? +(row.slg - row.avg).toFixed(3) : null);

  const aeiHr9 = row.pitcher_hr9 != null ? row.pitcher_hr9 : null;
  const aeiPTier = aeiHr9 != null ? (aeiHr9 >= 1.45 ? "HITTABLE" : aeiHr9 >= 1.05 ? "AVERAGE" : "STINGY") : "—";
  const aeiPTierColor = aeiPTier === "HITTABLE" ? "#1aff66" : aeiPTier === "AVERAGE" ? "#ffb020" : aeiPTier === "STINGY" ? "#ff3344" : "inherit";

  const isConfirmed = row.lineup_confirmed === true;
  const pitcherConfirmed = row.pitcher_confirmed === true;
  const aeiState = isConfirmed ? "CONFIRMED" : (pitcherConfirmed ? "PROJECTION" : null);

  const aeiBoard = isJigContext || builderMode ? 'jig' : (row._board || 'main');
  const addStatus = (slipSt.cardStatus && row.id && slipSt.cardStatus[row.id]) || 'idle';
  const handlePick = () => {
    if (!window.__hrSlip) return;
    window.__hrSlip.requestAdd({
      player_id:       row.id,
      name:            batterName,
      teamAbbr:        row.teamAbbr,
      team:            row.teamAbbr,
      pitcher:         row.pitcher_name,
      pitcher_name:    row.pitcher_name,
      model_prob:      row.model_prob,
      tier:            row.tier,
      model_tier_rank: row.model_tier_rank,
      board:           aeiBoard,
      hrprob:          row.hrprob,
      barrel:          row.barrel,
      hh:              row.hh,
      fd_bet_link:     row.fd_bet_link,
      fd_event_link:   row.fd_event_link,
      signal_snapshot: fsmBuildSnapshot(row, aeiBoard, null),
    });
  };

  return (
    <div className="fsm-card aei-wrap">
      <div className="aei-top-bar">
        <button className="fsm-card__close" onClick={onClose} aria-label="Close">✕</button>
      </div>
      <div className="aei-scroll-body">
      <div className="aei-header">
        <div className="aei-header__title">ARSENAL EDGE INTEL</div>
        {aeiState && <div className={`aei-header__state aei-header__state--${aeiState.toLowerCase()}`}>{aeiState}</div>}
        <div className="aei-header__sub">{batterName} VS {pitcherName} — PITCH MIX EXPLOITATION</div>
      </div>

      <div className="aei-grid">

        {/* ===== LEFT: PITCHER ARSENAL ===== */}
        <section className="aei-panel aei-panel--pitcher">
          <div className="aei-panel__hd">
            <span className="aei-panel__hd-title">PITCHER ARSENAL</span>
            <span className="aei-panel__hd-tag">THREAT LEVEL</span>
          </div>
          <div className="aei-panel__body">
            <div className="aei-pcard aei-pcard--pitcher">
              <div className="aei-tile aei-tile--pitcher">{pInit}</div>
              <div className="aei-pcard__who">
                <div className="aei-pcard__nm">{pitcherName}</div>
                <div className="aei-pcard__meta">{pitcherHand ? pitcherHand + "HP" : "—"}</div>
                <span className="aei-pcard__scope" style={{display:"block",marginTop:"4px",fontFamily:"var(--font-display)",fontWeight:700,fontSize:"11px",letterSpacing:"0.08em",color:"var(--fg-3)",lineHeight:1.3,opacity:0.85}}>SEASON HR/9: {aeiHr9 != null ? aeiHr9.toFixed(2) : "—"} <span style={{color: aeiPTierColor}}>({aeiPTier})</span></span>
              </div>
            </div>

            <div className="aei-chips">
              {[
                ["ERA",     row.pitcher_era            != null ? row.pitcher_era.toFixed(2)              : "—"],
                ["WHIP",    row.pitcher_whip           != null ? row.pitcher_whip.toFixed(2)             : "—"],
                ["K%",      row.pitcher_k_pct          != null ? row.pitcher_k_pct.toFixed(1)            : "—"],
                ["BB%",     row.pitcher_bb_pct         != null ? row.pitcher_bb_pct.toFixed(1)           : "—"],
                ["BARREL%", row.pitcher_barrel_allowed != null ? (row.pitcher_barrel_allowed*100).toFixed(1) : "—"],
                ["HH%",     row.pitcher_hh_allowed     != null ? (row.pitcher_hh_allowed*100).toFixed(1)    : "—"],
              ].map(([k, v]) => (
                <div key={k} className="aei-chip">
                  <div className="aei-chip__k">{k}</div>
                  <div className="aei-chip__v">{v}</div>
                </div>
              ))}
            </div>

            <div className="aei-tblwrap">
              <div className="aei-tblwrap__cap">{pLast} ARSENAL VS {batHand || "?"}HB</div>
              <div className="aei-ars">
                <div className="aei-ars__hd">
                  <span>PITCH</span><span>USAGE</span><span>VELO</span><span>WHIFF</span><span>HR/PA</span><span>K%</span><span>HH%</span>
                </div>
                {fetchState === "loading" && <div className="aei-empty">Loading arsenal…</div>}
                {fetchState === "no-pitcher" && <div className="aei-empty">Pitcher TBD — no detail available</div>}
                {(fetchState === "done" || fetchState === "error") && arsenal.length === 0 && (
                  <div className="aei-empty">No arsenal data</div>
                )}
                {arsorted.map(p => {
                  const ps    = pitchStats[p.code] || {};
                  const isKey = p.code === keyPitch;
                  const velo  = p.velo != null ? Number(p.velo).toFixed(0)
                    : ps.avg_speed != null ? Number(ps.avg_speed).toFixed(0) : "—";
                  const whiff = p.whiff != null ? Number(p.whiff).toFixed(0) + "%" : "—";
                  const hrPa  = ps.hr_rate != null ? (Number(ps.hr_rate)*100).toFixed(1)+"%"
                    : (ps.hr != null && ps.pa != null && ps.pa >= 10) ? (ps.hr/ps.pa*100).toFixed(1)+"%" : "—";
                  const kPct  = ps.k_pct != null ? (Number(ps.k_pct)*100).toFixed(0)+"%" : "—";
                  const hhPct = ps.display_hh != null ? (Number(ps.display_hh)*100).toFixed(0)+"%" : "—";
                  const barW  = Math.min(100, (p.usage ?? 0) * 2) + "%";
                  return (
                    <div key={p.code} className={"aei-ars__row" + (isKey ? " aei-ars__row--key" : "")}>
                      <div className="aei-ars__pitch">
                        <b>{p.code}</b>
                        <span>{fsmPitchName(p.code)}</span>
                        {isKey && <span className="aei-hunt">HUNT THIS</span>}
                      </div>
                      <div className="aei-usage">
                        <div className="aei-usage__track">
                          <div className="aei-usage__fill" style={{width: barW}} />
                        </div>
                        <div className="aei-usage__lbl">{p.usage != null ? Number(p.usage).toFixed(0)+"%" : "—"}</div>
                      </div>
                      <span className="aei-c">{velo}</span>
                      <span className="aei-c">{whiff}</span>
                      <span className={"aei-c" + (hrPa !== "—" && parseFloat(hrPa) >= 3 ? " aei-c--hg" : "")}>{hrPa}</span>
                      <span className="aei-c">{kPct}</span>
                      <span className="aei-c">{hhPct}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        {/* ===== CENTER: ARSENAL EDGE VERDICT ===== */}
        <section className="aei-panel aei-panel--verdict">
          <div className="aei-panel__hd">
            <span className="aei-panel__hd-title">ARSENAL EDGE VERDICT</span>
          </div>
          <div className="aei-panel__body">

            {/* ARSENAL EDGE VERDICT — primary signal: edge score + label + confidence */}
            <div className="aei-edge-active">
              <div className="aei-ea__title">ARSENAL EDGE: {edgeDisplayLabel}</div>
              <div className="aei-ea__row">
                <span className="aei-ea__lbl">EDGE SCORE</span>
                <span className="aei-ea__val">{isGap ? "—" : Number(score).toFixed(1)}</span>
              </div>
              <div className="aei-ea__row">
                <span className="aei-ea__lbl">CONFIDENCE</span>
                <span className="aei-ea__val">{confidence != null ? Math.round(Number(confidence) * 100) + "%" : "—"}</span>
              </div>
              {keyPitch && (
                <div style={{marginTop:"4px",fontFamily:"var(--font-display)",fontWeight:700,fontSize:"10px",letterSpacing:"0.1em",color:"var(--fg-2)"}}>KEY PITCH: {keyPitchName}</div>
              )}
              {(edgeLabel === "VOLATILE" || (confidence != null && Number(confidence) < 0.5)) && (
                <div style={{marginTop:"6px",fontFamily:"var(--font-display)",fontWeight:700,fontSize:"10px",letterSpacing:"0.1em",color:"var(--fg-2)"}}>LOW CONFIDENCE · SMALL SAMPLE</div>
              )}
            </div>

            {/* H2H HR Signal — career head-to-head */}
            <div className="aei-vcard aei-vcard--h2h">
              <div className="aei-vcard__top">
                <span className="aei-vcard__lbl">H2H HR SIGNAL</span>
                <span className="aei-vcard__big">
                  {h2h ? ((h2h.hr || 0) / h2h.pa * 100).toFixed(1) + "%" : "—"}
                </span>
              </div>
              <div className="aei-vbar">
                <i style={{width: h2h && h2h.pa > 0 ? Math.min(100, ((h2h.hr||0)/h2h.pa)*300)+"%" : "2%"}} />
              </div>
              <div className="aei-vstats">
                {[["PA", h2h?.pa ?? "—"], ["HR", h2h?.hr ?? "—"], ["BA", h2h?.avg || "—"], ["SLG", h2h?.slg || "—"], ["OPS", h2h?.ops || "—"]].map(([k,v]) => (
                  <div key={k} className="aei-vs-cell"><span>{k}</span><b>{v}</b></div>
                ))}
              </div>
              <div className="aei-vcard__bot">
                <span className="aei-vcard__note">
                  {h2h ? `${h2h.pa} PA${h2h.pa < 10 ? " — NOT PREDICTIVE" : ""}` : "NO CAREER H2H ON RECORD"}
                </span>
                <span className="aei-vcard__trust">{h2hTrust}</span>
              </div>
            </div>

            {/* OVERALL EXPLOIT CONFIDENCE — matchup-level arsenal_edge_confidence */}
            <div className="aei-vcard aei-vcard--conf">
              <div className="aei-vcard__top">
                <span className="aei-vcard__lbl">OVERALL EXPLOIT CONFIDENCE</span>
                <span className="aei-vcard__big aei-vcard__big--conf">
                  {confidence != null ? Math.round(Number(confidence) * 100) + "%" : "—"}
                </span>
              </div>
              <div className="aei-vbar">
                <i style={{width: confidence != null ? Math.min(100, Math.round(Number(confidence) * 100)) + "%" : "2%"}} />
              </div>
              <div className="aei-vcard__bot">
                <span className="aei-vcard__note">FULL ARSENAL MATCHUP READ</span>
                <span className="aei-vcard__trust" style={{color:"var(--fg-2)",fontSize:"9px",letterSpacing:"0.08em"}}>WEIGHTED BY PITCH MIX + CONTRIBUTION CONFIDENCE</span>
              </div>
            </div>

            {/* MODEL HR PROB — row.hrprob as-is; no invented adjustment */}
            <div className="aei-vcard aei-vcard--model">
              <div className="aei-vcard__top">
                <span className="aei-vcard__lbl">MODEL HR PROB</span>
                <span className="aei-vcard__big aei-vcard__big--model">
                  {row.hrprob != null ? row.hrprob.toFixed(1) + "%" : "—"}
                </span>
              </div>
              <div className="aei-vbar">
                <i style={{width: row.hrprob != null ? Math.min(100, row.hrprob*3)+"%" : "2%"}} />
              </div>
              <div className="aei-vcard__bot">
                <span className="aei-vcard__note">KEY PITCH: {keyPitchName}</span>
                <span className="aei-odds">HR ODDS <b>{row.odds || "—"}</b></span>
              </div>
            </div>

            {/* Edge stack — display reads; BARREL PATH is a qualitative band. */}
            <div className="aei-stack">
              <div className="aei-stack__cap">EDGE STACK</div>
              <div className="aei-stack__row">
                <div className="aei-stack__item">
                  <div className="aei-stack__k">H2H</div>
                  <div className={"aei-stack__v " + h2hSigCls}>{h2hSigLbl}</div>
                </div>
                <div className="aei-stack__item">
                  <div className="aei-stack__k">PITCH EXPLOIT</div>
                  <div className={"aei-stack__v " + exploitCls}>{exploitLbl}</div>
                </div>
                <div className="aei-stack__item">
                  <div className="aei-stack__k">BARREL PATH</div>
                  <div className={"aei-stack__v " + barrelBand.cls}>{barrelBand.label}</div>
                </div>
                <div className="aei-stack__item">
                  <div className="aei-stack__k">HH POWER</div>
                  <div className={"aei-stack__v " + hhBand.cls}>{hhBand.label}</div>
                </div>
                <div className="aei-stack__item">
                  <div className="aei-stack__k">MODEL TIER</div>
                  <div className="aei-stack__v" style={{ color: modelTierColor }}>{modelTier}</div>
                </div>
              </div>
            </div>

          </div>
        </section>

        {/* ===== RIGHT: BATTER DAMAGE PROFILE ===== */}
        <section className="aei-panel aei-panel--batter">
          <div className="aei-panel__hd">
            <span className="aei-panel__hd-title">BATTER DAMAGE PROFILE</span>
            <span className="aei-panel__hd-tag">THREAT LEVEL</span>
          </div>
          <div className="aei-panel__body">
            <div className="aei-pcard aei-pcard--batter">
              <div className="aei-tile aei-tile--batter">{bInit}</div>
              <div className="aei-pcard__who">
                <div className="aei-pcard__nm">{batterName}</div>
                <div className="aei-pcard__meta">BATS {batterSide || "?"} · {row.teamAbbr || ""}</div>
                <span className="aei-tier">BATTER THREAT TIER <b>{row.tier || "—"}</b></span>
              </div>
            </div>

            <div className="aei-chips">
              {[
                ["AVG",     fsmS3(row.avg)],
                ["xISO",    fsmS3(iso)],
                ["HR",      row.hr     != null ? String(row.hr)        : "—"],
                ["K%",      row.kpct   != null ? row.kpct.toFixed(1)   : "—"],
                ["BARREL%", row.barrel != null ? row.barrel.toFixed(1) : "—"],
                ["EV",      row.ev     != null ? row.ev.toFixed(1)     : "—"],
                ["xwOBA",   fsmS3(row.xwoba)],
              ].map(([k, v]) => (
                <div key={k} className="aei-chip">
                  <div className="aei-chip__k">{k}</div>
                  <div className="aei-chip__v">{v}</div>
                </div>
              ))}
            </div>

            <div className="aei-tblwrap">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 4 }}>
                <div className="aei-tblwrap__cap" style={{ marginBottom: 0 }}>{bLast} VS {pitcherHand || "?"}HP — BY PITCH TYPE</div>
                <details style={{ position: 'relative' }}>
                  <summary style={{ listStyle: 'none', cursor: 'pointer', fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 8, color: '#8a9691', letterSpacing: '0.14em', textTransform: 'uppercase', border: '1px solid rgba(180,220,200,0.18)', borderRadius: 3, padding: '3px 6px', whiteSpace: 'nowrap' }}>COLUMNS</summary>
                  <div style={{ position: 'absolute', zIndex: 2, top: 'calc(100% + 4px)', right: 0, minWidth: 154, padding: 7, background: '#0e1519', border: '1px solid rgba(180,220,200,0.18)', borderRadius: 3, boxShadow: '0 8px 20px rgba(0,0,0,0.28)' }}>
                    {bvpCols.map(col => (
                      <label key={col.key} title={col.title} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '3px 1px', cursor: 'pointer', fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 9, color: '#b8c2c0', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                        <input type="checkbox" checked={activeBvpCols.has(col.key)} onChange={() => toggleBvpCol(col.key)} style={{ accentColor: '#1aff66', margin: 0 }} />
                        {col.head}
                      </label>
                    ))}
                    <div style={{ marginTop: 4, paddingTop: 5, borderTop: '1px solid rgba(180,220,200,0.08)', fontFamily: 'var(--font-display)', fontSize: 8, color: '#3a4642', letterSpacing: '0.1em' }}>PITCH ALWAYS SHOWN</div>
                  </div>
                </details>
              </div>
              <div className="aei-bt aei-bt--scroll">
                <div className="aei-bt__hd" style={{ gridTemplateColumns: bvpGridTemplate, minWidth: bvpGridMinWidth }}>
                  <span>PITCH</span>
                  {visibleBvpCols.map(col => <span key={col.key}>{col.head}</span>)}
                </div>
                {fetchState === "loading" && <div className="aei-empty">Loading…</div>}
                {fetchState !== "loading" && !hasBvp && (
                  <div className="aei-empty">No pitch-type data on record</div>
                )}
                {hasBvp && arsorted.map(p => {
                  const b = bvp[p.code];
                  if (!b || !b.pa) return null;
                  const isKey = p.code === keyPitch;
                  const small = b.pa < 10;
                  return (
                    <div key={p.code} className={"aei-bt__row" + (isKey ? " aei-bt__row--key" : "")} style={{ gridTemplateColumns: bvpGridTemplate, minWidth: bvpGridMinWidth }}>
                      <div className="aei-bt__pitch">
                        <b>{fsmPitchName(p.code)}</b>
                        {small && <span className="aei-bt__ss">SMALL · &lt;10 PA</span>}
                      </div>
                      {visibleBvpCols.map(col => {
                        const hasValue = col.key === 'hr' ? b && b.hr != null : col.gate(b);
                        const value = hasValue ? col.fmt(b) : '—';
                        const valence = col.key === 'ba' ? hrStatValence(b.ba, [0.280, 0.240])
                          : col.key === 'slg' ? hrStatValence(b.slg, [0.450, 0.380])
                          : col.key === 'iso' ? hrStatValence(Number(b.slg) - Number(b.ba), [0.200, 0.140])
                          : col.key === 'hr_pct' ? hrStatValence(Number(b.hr || 0) / Number(b.pa) * 100, [8, 5])
                          : col.key === 'k_pct' ? hrStatValence(Number(b.k_pct) * 100, [18, 27], 'lower')
                          : col.key === 'hh_pct' ? hrStatValence(Number(b.display_hh) * 100, [45, 38])
                          : undefined;
                        return <span key={col.key} className="aei-c" style={{ color: valence }}>{value}{col.key === 'pa' && small ? '*' : ''}</span>;
                      })}
                    </div>
                  );
                }).filter(Boolean)}
                {anySmall && <div className="aei-pt__note">* &lt;10 PA — small sample, treat with caution</div>}
              </div>
            </div>
          </div>
        </section>

        {/* ===== RECENT FORM ===== */}
        <section className="aei-panel" style={{ gridColumn: "1 / -1" }}>
          <div className="aei-panel__hd">
            <span className="aei-panel__hd-title">RECENT FORM</span>
          </div>
          <div className="aei-panel__body aei-recent-form" style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
            <div className="aei-tblwrap">
              <div className="aei-tblwrap__cap">LAST 5 STARTS</div>
              <div className="aei-bt aei-bt--scroll">
                <div className="aei-bt__hd" style={{ gridTemplateColumns: recentGridTemplate, minWidth: recentGridMinWidth }}>
                  <span>DATE</span><span>HR</span><span>K</span><span>IP</span><span>BB</span>
                </div>
                {fetchState === "loading" && <div className="aei-empty">Loading…</div>}
                {fetchState !== "loading" && pitcherRecent.length === 0 && <div className="aei-empty">No recent data</div>}
                {pitcherRecent.map((start, index) => (
                  <div key={`${start.date || "start"}-${index}`} className="aei-bt__row" style={{ gridTemplateColumns: recentGridTemplate, minWidth: recentGridMinWidth }}>
                    <span>{start.date || "—"}</span>
                    {/* Pitcher HR allowed is inverted from the pitcher perspective: more allowed is favorable for this hitter. */}
                    <span className="aei-c" style={{ color: hrStatValence(start.hr, [2, 1]) }}>{start.hr ?? "—"}</span>
                    <span className="aei-c">{start.k ?? "—"}</span>
                    <span className="aei-c">{start.ip != null && Number.isFinite(Number(start.ip)) ? Number(start.ip).toFixed(1) : "—"}</span>
                    <span className="aei-c">{start.bb ?? "—"}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="aei-tblwrap">
              <div className="aei-tblwrap__cap">LAST 5 GAMES</div>
              <div className="aei-bt aei-bt--scroll">
                <div className="aei-bt__hd" style={{ gridTemplateColumns: recentGridTemplate, minWidth: recentGridMinWidth }}>
                  <span>DATE</span><span>HR</span><span>AVG</span><span>SLG</span><span>PA</span>
                </div>
                {fetchState === "loading" && <div className="aei-empty">Loading…</div>}
                {fetchState !== "loading" && batterRecent.length === 0 && <div className="aei-empty">No recent data</div>}
                {batterRecent.map((game, index) => (
                  <div key={`${game.date || "game"}-${index}`} className="aei-bt__row" style={{ gridTemplateColumns: recentGridTemplate, minWidth: recentGridMinWidth }}>
                    <span>{game.date || "—"}</span>
                    <span className="aei-c" style={{ color: hrStatValence(game.hr, [1], 'binary') }}>{game.hr ?? "—"}</span>
                    <span className="aei-c" style={{ color: hrStatValence(game.avg, [0.280, 0.240]) }}>{game.avg == null ? "—" : Number(game.avg).toFixed(3)}</span>
                    <span className="aei-c" style={{ color: hrStatValence(game.slg, [0.450, 0.380]) }}>{game.slg == null ? "—" : Number(game.slg).toFixed(3)}</span>
                    <span className="aei-c">{game.pa ?? "—"}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

      </div>

      <div className="fsm-card__foot">
        <button className="fsm-card__pitchbtn" onClick={onBatter}>← BATTER CARD</button>
        {!builderMode && (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button
              className={"aei-pick-btn" + (addStatus === 'added' ? ' aei-pick-btn--added' : '')}
              onClick={handlePick}
              disabled={addStatus === 'loading'}
            >
              {addStatus === 'added' ? '✓ PICKED' : addStatus === 'loading' ? '…' : '+ PICK'}
            </button>
          </div>
        )}
      </div>
      </div>
    </div>
  );
}

function FsmDetailModal({ modal, onClose, setModal, builderMode = false, isJigContext = false }) {
  React.useEffect(() => {
    const h = (e) => {if (e.key === "Escape") onClose();};
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);
  if (!modal) return null;
  return (
    <div className="fsm-modal" onClick={onClose}>
      <div className="fsm-modal__inner" onClick={(e) => e.stopPropagation()}>
        {modal.type === "batter" ? (() => { const BDC = window.BatterDetailCard || FsmBatterCard; return <BDC row={modal.row} onClose={onClose} onPitch={() => setModal({ type: "pitch", row: modal.row })} builderMode={builderMode} />; })() :
        <FsmArsenalEdgeIntel row={modal.row} onClose={onClose} onBatter={() => setModal({ type: "batter", row: modal.row })} builderMode={builderMode} isJigContext={isJigContext} />}
      </div>
    </div>);

}

/* The fabricated platoon-hand multiplier lens (fsmAdjustRow, 1.06/0.93) was
   retired 2026-07-08 — superseded by REAL vs-hand splits via fsmSplitRow. */

function FullSlateMatrix({ rows, total, onOpen, filterNote, embedded, builderMode = false, isJigContext = false }) {
  const [view, setView] = React.useState("game");
  const [selGame, setSelGame] = React.useState("all");
  const [group, setGroup] = React.useState("all");
  const [focus, setFocus] = React.useState("all");
  const [selRoles, setSelRoles] = React.useState([]);
  const toggleRole = (id) => setSelRoles((prev) => prev.includes(id) ? prev.filter((r) => r !== id) : [...prev, id]);
  const [selMetrics, setSelMetrics] = React.useState([]);
  const toggleMetric = (id) => setSelMetrics((prev) => prev.includes(id) ? prev.filter((m) => m !== id) : [...prev, id]);
  const [modal, setModal] = React.useState(null);
  const FSM_PREF_V = 4;
  const [colPref, setColPref] = useColumnLayout("fsm_shared", { order: FSM_PICKER_COLS.map((c) => c.key), hidden: [], v: FSM_PREF_V });
  const [colOpen, setColOpen] = React.useState(false);
  const [colInfo, setColInfo] = React.useState(null);
  const [editMode, setEditMode] = React.useState(false);
  const [projSortOn, setProjSortOn] = React.useState(false);
  const [sortState, setSortState] = React.useState({ key: '_board_metric', dir: 'desc' });
  const [splitScope, setSplitScope] = React.useState('vs_hand');
  const [dataVersion, setDataVersion] = React.useState(0);
  React.useEffect(() => {
    const handler = () => setDataVersion(v => v + 1);
    window.addEventListener("hrEngineDataLoaded", handler);
    return () => window.removeEventListener("hrEngineDataLoaded", handler);
  }, []);
  const onSort = (key) => setSortState((s) => s && s.key === key ? { key, dir: s.dir === "desc" ? "asc" : "desc" } : { key, dir: "desc" });
  const onReorder = (fromKey, toKey) => setColPref((p) => { if (fromKey === toKey) return p; const o = p.order.filter((k) => k !== fromKey); o.splice(o.indexOf(toKey), 0, fromKey); return { ...p, order: o }; });
  React.useEffect(() => { setColPref((p) => { const missing = FSM_PICKER_COLS.filter((c) => !p.order.includes(c.key)).map((c) => c.key); return missing.length ? { ...p, order: [...p.order, ...missing] } : p; }); }, []);
  const activeCols = colPref.order.map((k) => FSM_COLS.find((c) => c.key === k)).filter((c) => c && !colPref.hidden.includes(c.key));
  const toggleCol = (k) => setColPref((p) => ({ ...p, hidden: p.hidden.includes(k) ? p.hidden.filter((x) => x !== k) : [...p.hidden, k] }));
  const moveCol = (idx, dir) => setColPref((p) => { const o = [...p.order]; const j = idx + dir; if (j < 0 || j >= o.length) return p; [o[idx], o[j]] = [o[j], o[idx]]; return { ...p, order: o }; });
  const resetCols = () => setColPref({ order: FSM_PICKER_COLS.map((c) => c.key), hidden: [], v: FSM_PREF_V });
  const [secs, setSecs] = React.useState(3);
  React.useEffect(() => {const id = setInterval(() => setSecs((s) => (s + 1) % 600), 1000);return () => clearInterval(id);}, []);
  const timer = `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, "0")}`;

  /* Overlay REAL vs-hand splits (display keys only; _raw preserved for capture/hero).
     In 'season' mode skip the overlay — season values already live on the row. */
  const splitRows = React.useMemo(() => {
    if (splitScope === 'season') {
      return rows.map((r) => ({ ...r, air: fsmAirPct(r), _raw: r, _vsScope: Object.fromEntries(FSM_SCOPE_HAND_KEYS.map((k) => [k, { scope: 'season' }])) }));
    }
    return rows.map(fsmSplitRow);
  }, [rows, splitScope]);
  const sorted = React.useMemo(() => {
    const s0 = [...splitRows];
    if (!sortState) return s0;
    if (sortState.key === '_board_metric') {
      const pick = (row, curKey, projKey) => {
        const confirmed = isJigContext ? row.pitcher_confirmed === true : row.lineup_confirmed === true;
        if (confirmed) return row[curKey] ?? -Infinity;
        return (projSortOn ? (row[projKey] ?? row[curKey]) : row[curKey]) ?? -Infinity;
      };
      return [...s0].sort((a, b) => {
        if (!isJigContext && !builderMode) {
          const at = pick(a, 'true_matchup_score', 'tm_projected'), bt = pick(b, 'true_matchup_score', 'tm_projected');
          if (bt !== at) return bt - at;
          return pick(b, 'hrprob', 'hrprob_projected') - pick(a, 'hrprob', 'hrprob_projected');
        }
        return pick(b, 'jigScore', 'jigscore_projected') - pick(a, 'jigScore', 'jigscore_projected');
      });
    }
    return [...s0].sort((a, b) => {
      const av = a[sortState.key], bv = b[sortState.key];
      const an = av == null ? -Infinity : av, bn = bv == null ? -Infinity : bv;
      return sortState.dir === "desc" ? bn - an : an - bn;
    });
  }, [splitRows, sortState, projSortOn, isJigContext, builderMode]);

  const passGroup = (r) =>
  group === "all" ? true : group === "qualified" ? r.pa >= 100 : ["APEX", "ELITE", "EDGE"].includes(r.tier);
  const passFocus = (r) => {
    if (focus === "all") return true;
    if (focus === "power") return r.barrel != null && r.barrel >= 4.5 || r.slg >= 0.470;
    if (focus === "contact") return r.avg >= 0.255;
    if (focus === "matchup") return ["ELITE", "STRONG"].includes(r.quality) || r.pitcherVuln === "TARGET";
    return true;
  };

  const passRole = (r) => {
    if (selRoles.length === 0) return true;
    if (selRoles.includes("norole")) return !r.prime && !r.explosive && !r.advantage && !r.wildcard;
    return selRoles.every((id) => r[id] === true);
  };
  const passMetric = (_r) => true;

  const pool = sorted.filter((r) => (selGame === "all" || r.gameId === selGame) && passGroup(r) && passFocus(r) && passRole(r) && passMetric(r));
  const gamesToShow = selGame === "all" ? getFSMGames() : getFSMGames().filter((g) => g.id === selGame);
  const title = builderMode ? "JIG BUILDER WORKSPACE" : "FULL SLATE INTELLIGENCE MATRIX";
  const subtitle = builderMode ?
  "OPERATOR WORKSPACE USING JIG-SIDE SLATE ROWS. RAW UNSCORED FEED NOT YET EXPOSED." :
  "LIVE HR THREAT SCAN · MATCHUP / BARREL / ENVIRONMENT / DEPLOYMENT READINESS";
  const playerViewTitle = builderMode ?
  "Builder view preserves the current JIG-side source order. Use column controls for manual inspection." :
  "Flat list of every batter on the slate, ranked by model HR probability.";
  const tierDesc = builderMode ? FSM_BUILDER_TIER_DESC : FSM_TIER_DESC;
  const groupOpts = builderMode ? FSM_BUILDER_GROUP_OPTS : FSM_GROUP_OPTS;

  const noteBits = [];
  if (group !== "all") noteBits.push(group === "qualified" ? "QUALIFIED" : "ELITE TARGETS");
  if (focus !== "all") noteBits.push("FOCUS " + focus.toUpperCase());
  if (selGame !== "all") noteBits.push("1 GAME");
  if (projSortOn && sortState && sortState.key === '_board_metric') noteBits.push((!isJigContext && !builderMode) ? "SORT: TM PROJECTED" : "SORT: JIG PROJECTED");
  const note = noteBits.length ? noteBits.join(" · ") : filterNote || "NO ACTIVE FILTERS";

  const openBatter = (row) => setModal({ type: "batter", row });
  const openPitch = (row) => setModal({ type: "pitch", row });

  return (
    <div className={"fsm" + (embedded ? " fsm--embed" : "")} data-comment-anchor="fa19328b4d-div-592-5">
      {/* TOP BAR */}
      {embedded ? (
        <div className="fsm-embed-head">
          <span className="fsm-embed-title">PLAYER TARGETS <b>{pool.length}</b></span>
          <span className="fsm-embed-sub"><span className="fsm-live"><i className="fsm-live__dot" />LIVE</span> · {getFSMGames().length} GAMES · UPD {timer} AGO</span>
        </div>
      ) : (
      <div className="fsm-topbar">
        <div className="fsm-topbar__titles">
          <h1 className="fsm-title">{title}</h1>
          <div className="fsm-sub">{subtitle}</div>
        </div>
        <div className="fsm-topbar__status">
          <span className="fsm-live"><i className="fsm-live__dot" />LIVE</span>
          <span className="fsm-stat-pill">{pool.length} / {total} BATTERS</span>
          <span className="fsm-stat-pill">{getFSMGames().length} GAMES</span>
          <span className="fsm-clock">UPD {timer} AGO</span>
        </div>
      </div>
      )}
      {!embedded && builderMode && (
      <div className="fsm-statusbar">
        <span className="fsm-status__sys">PHASE A SOURCE</span>
        <i />
        <span>JIG SCORED SLATE ROWS</span><i />
        <span>RAW UNSCORED BUILDER FEED PENDING</span><i />
        <span>ORDER PRESERVED FROM CURRENT JIG SOURCE</span>
      </div>
      )}

      {/* CONTROLS + LEGENDS */}
      <div className="fsm-controls">
        <div className="fsm-viewtoggle" role="tablist">
          <button className={view === "game" ? "is-on" : ""} title="Group batters by game, each under its matchup header (park, time, weather, HR factor)." onClick={() => setView("game")}>GAME VIEW</button>
          <button className={view === "player" ? "is-on" : ""} title={playerViewTitle} onClick={() => setView("player")}>PLAYER VIEW</button>
        </div>
        <div className="fsm-legends">
          <div className="fsm-legend">
            <span className="fsm-legend__title">TIER</span>
            {FSM_TIER_ORDER.map((t) =>
            <span className="fsm-tierpill" key={t} style={{ "--tc": FSM_TIERS[t].color, "--tg": FSM_TIERS[t].glow }} title={`${t} tier — ${tierDesc[t]}`}>{t}</span>
            )}
          </div>
          <div className="fsm-legend">
            <span className="fsm-legend__title" title="Batter HR-threat tier: dot color shows how dangerous this hitter is for a HR (model probability + barrel quality). Green glow = TARGET pitcher (HR/9 ≥ 2.2) — a separate pitcher-vulnerability signal layered on top.">BATTER THREAT</span>
            {FSM_MATCHUP_ORDER.map((k) =>
            <span className="fsm-mkey" key={k} title={`${k} batter threat — ${FSM_MATCHUP_DESC[k]}`}><i style={{ background: FSM_MATCHUP[k].color }} />{k}</span>
            )}
            <span className="fsm-mkey" key="TARGET" title={`TARGET — ${FSM_MATCHUP_DESC.TARGET}`}><i style={{ background: "#1aff66" }} />TARGET</span>
          </div>
        </div>
        {/* GAMES — jump straight to any game */}
        <label className="fsm-gamesel fsm-gamesel--inline">
          <span className="fsm-gamesel__label">GAMES</span>
          <span className="fsm-gamesel__field">
            <select value={selGame} onChange={(e) => setSelGame(e.target.value)}>
              <option value="all">All games · {getFSMGames().length}</option>
              {getFSMGames().map((g) =>
              <option key={g.id} value={g.id}>{g.away} @ {g.home} · {g.time}</option>
              )}
            </select>
            <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </span>
        </label>
        {/* COLUMNS — add / remove / reorder stat columns */}
        <div className="fsm-colmenu">
          <button className="fsm-colbtn" onClick={() => setColOpen((o) => !o)} aria-expanded={colOpen}>
            COLUMNS <b>{activeCols.length}</b>
            <svg viewBox="0 0 24 24" width="13" height="13" aria-hidden="true"><path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </button>
          <button className="fsm-colbtn" onClick={() => setEditMode((o) => !o)} title={editMode ? "EDIT mode ON — drag column headers to reorder; click to exit" : "EDIT mode — drag column headers to reorder (persists across sessions)"} style={editMode ? { borderColor: "rgba(26,255,102,0.5)", color: "#1aff66" } : undefined}>
            EDIT{editMode ? " ✓" : ""}
          </button>
          {colOpen &&
          <div className="fsm-colpop">
            <div className="fsm-colpop__head"><span>STAT COLUMNS</span><button onClick={resetCols}>RESET</button></div>
            <div className="fsm-colpop__hint">Hover or tap ⓘ for what each stat means</div>
            <div className="fsm-colpop__list">
              {colPref.order.map((k, idx) => {
                const c = FSM_COLS.find((x) => x.key === k);
                const on = !colPref.hidden.includes(k);
                return (
                  <React.Fragment key={k}>
                  <div className="fsm-colrow" title={c.title}>
                    <label className="fsm-colrow__lbl">
                      <input type="checkbox" checked={on} onChange={() => toggleCol(k)} />
                      <span>{c.head}</span>
                    </label>
                    <span className="fsm-colrow__mv">
                      <button className={"fsm-colinfo" + (colInfo === k ? " is-on" : "")} onClick={() => setColInfo((x) => x === k ? null : k)} title={c.title} aria-label="What is this stat?">ⓘ</button>
                      <button onClick={() => moveCol(idx, -1)} disabled={idx === 0} aria-label="Move up">▲</button>
                      <button onClick={() => moveCol(idx, 1)} disabled={idx === colPref.order.length - 1} aria-label="Move down">▼</button>
                    </span>
                  </div>
                  {colInfo === k && <div className="fsm-coldesc">{c.title}</div>}
                  </React.Fragment>);
              })}
            </div>
          </div>
          }
        </div>
      </div>
      <div className="fsm-pitchbar">
        <span className="fsm-pitchbar__lbl">SPLIT SCOPE</span>
        <div className="fsm-rg__opts" role="radiogroup" aria-label="Split scope" style={{ display: 'inline-flex', padding: '3px', borderRadius: '8px' }}>
          <button className={"fsm-rg__opt" + (splitScope === 'vs_hand' ? " is-on" : "")} role="radio" aria-checked={splitScope === 'vs_hand'} title="Show REAL vs-hand splits for AVG/SLG/ISO/HR-PA/HR-count — PA always shown; thin <30 PA tagged amber; Statcast stays SZN" style={{ padding: '4px 10px', gap: 0 }} onClick={() => setSplitScope('vs_hand')}>VS HAND</button>
          <button className={"fsm-rg__opt" + (splitScope === 'season' ? " is-on" : "")} role="radio" aria-checked={splitScope === 'season'} title="Show season-blended values for AVG/SLG/ISO/HR-PA/HR-count — compare vs-hand vs season by toggling" style={{ padding: '4px 10px', gap: 0 }} onClick={() => setSplitScope('season')}>SEASON</button>
        </div>
        {splitScope === 'vs_hand' && <>
          <span className="fsm-scope fsm-scope--hand fsm-scope--pill" title="Real faced-hand split — reliable sample (30+ PA); PA shown">VS R / VS L · REAL · PA</span>
          <span className="fsm-scope fsm-scope--thin fsm-scope--pill" title="Real faced-hand split — thin sample (<30 PA); treat with caution">THIN &lt;30 PA</span>
          <span className="fsm-scope fsm-scope--szn fsm-scope--pill" title="Season-blended fallback — no hand split or pitcher TBD">SZN FALLBACK</span>
        </>}
        {splitScope === 'season' && <span className="fsm-scope fsm-scope--szn fsm-scope--pill" title="All stat columns showing season-blended values">ALL SZN · AVG / SLG / ISO / HR-PA / HR</span>}
        <span className="fsm-pitchbar__note">{splitScope === 'vs_hand' ? 'AVG · SLG · ISO · HR/PA · HR = real vs-hand when tagged (PA always shown)' : 'AVG · SLG · ISO · HR/PA · HR = season-blended'} · Statcast = season always</span>
      </div>
      <div className="fsm-filters">
        <FsmRadioGroup label="PLAYER GROUP" value={group} onChange={setGroup} options={groupOpts} />
        <span className="fsm-filters__div" />
        <FsmRadioGroup label="FOCUS" value={focus} onChange={setFocus} options={FSM_FOCUS_OPTS} />
        <span className="fsm-filters__div" />
        <FsmRoleFilter selRoles={selRoles} onToggle={toggleRole} />
      </div>
      <div className="fsm-sortbar">
        <span className="fsm-sortbar__lbl">SORT</span>
        <button className={"fsm-sortbar__btn" + (!sortState ? " is-on" : "")} onClick={() => setSortState(null)} title="Default: canonical model rank order">RANK</button>
        {!isJigContext && !builderMode ? (
          <button className={"fsm-sortbar__btn" + (sortState && sortState.key === '_board_metric' ? " is-on" : "")} onClick={() => setSortState({ key: '_board_metric', dir: 'desc' })} title="Sort MAIN board by TM (True Matchup score) descending — HR PROB tiebreak. All players shown.">TM</button>
        ) : (
          <button className={"fsm-sortbar__btn" + (sortState && sortState.key === '_board_metric' ? " is-on" : "")} onClick={() => setSortState({ key: '_board_metric', dir: 'desc' })} title="Sort JIG board by jigScore descending — JIG formula, never TM. All players shown.">JIG SCORE</button>
        )}
        <span className="fsm-sortbar__sep" />
        <button className={"fsm-sortbar__btn fsm-sortbar__toggle" + (projSortOn ? " is-on" : "")} onClick={() => setProjSortOn(v => !v)} title={projSortOn ? "Sorting by projected values — click for current values" : "Sorting by current values — click for projected values"}>{projSortOn ? "PROJECTION" : "CURRENT"}</button>
      </div>

      {/* GAME-NAV CHIPS — one-click jump to each game */}
      {view === "game" &&
      <div className="fsm-gamenav">
          <button className={selGame === "all" ? "is-on" : ""} onClick={() => setSelGame("all")}>ALL · {getFSMGames().length}</button>
          {getFSMGames().map((g) =>
        <button key={g.id} className={selGame === g.id ? "is-on" : ""} onClick={() => setSelGame(g.id)}>
              {g.away} @ {g.home}
            </button>
        )}
        </div>
      }

      {/* BODY */}
      {pool.length === 0 ?
      <div className="fsm-metric-empty">
        <span className="fsm-metric-empty__icon">—</span>
        <span className="fsm-metric-empty__msg">No players on today's slate.</span>
      </div> :
      view === "player" ?
      <div className="fsm-tablewrap fsm-scroll-container"><FsmTable rows={pool} cols={activeCols} showGame={true} onBatter={openBatter} onPitch={openPitch} onReorder={onReorder} onFront={(key) => { const first = activeCols[0]; if (first && first.key !== key) onReorder(key, first.key); }} onSort={onSort} sortState={sortState} builderMode={builderMode} isJigContext={isJigContext} splitScope={splitScope} editMode={editMode} /></div> :

      gamesToShow.map((game) => {
        const gameRows = pool.filter((r) => r.gameId === game.id);
        if (!gameRows.length) return null;
        return (
          <div className="fsm-gameblock" key={game.id} id={`fsm-game-${game.id}`}>
              <FsmGameHeader game={game} n={gameRows.length} />
              <div className="fsm-tablewrap fsm-scroll-container"><FsmTable rows={gameRows} cols={activeCols} onBatter={openBatter} onPitch={openPitch} onReorder={onReorder} onFront={(key) => { const first = activeCols[0]; if (first && first.key !== key) onReorder(key, first.key); }} onSort={onSort} sortState={sortState} builderMode={builderMode} isJigContext={isJigContext} splitScope={splitScope} editMode={editMode} /></div>
            </div>);

      })
      }

      {/* STATUS BAR */}
      {!embedded && (
      <div className="fsm-statusbar">
        <span className="fsm-status__sys">HR ENGINE COMMAND SYSTEM</span>
        <i />
        <span>DATA <b className="ok">LIVE</b></span><i />
        <span>UPD {timer} AGO</span><i />
        <span>STATUS <b className="ok">OPERATIONAL</b></span><i />
        <span>{note}</span><i />
        <span>TACTICAL MODE</span>
        <span className="fsm-status__src">SRC · MLB STATS API / STATCAST</span>
      </div>
      )}

      <FsmDetailModal modal={modal} onClose={() => setModal(null)} setModal={setModal} builderMode={builderMode} isJigContext={isJigContext} />
    </div>);

}

Object.assign(window, { FullSlateMatrix, FSM_TEAM_COLOR: TEAM_COLOR });
