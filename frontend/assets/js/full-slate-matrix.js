/* HR Engine — FULL SLATE INTELLIGENCE MATRIX
   Dense battlefield-style threat scan: 6-tier system, conic matchup pies,
   5-bucket Statcast heatmap, GAME / PLAYER views. Replaces the legacy
   leaderboard inside the MAIN/JIG "Full Slate" lens. */

const FSM_TIERS = {
  APEX: { color: "#ff3344", glow: "rgba(255,51,68,0.75)", min: 18 },
  ELITE: { color: "#ff8a93", glow: "rgba(255,138,147,0.55)", min: 13 },
  EDGE: { color: "#1aff66", glow: "rgba(26,255,102,0.6)", min: 9 },
  SIGNAL: { color: "#3b6fff", glow: "rgba(59,111,255,0.5)", min: 6 },
  WATCH: { color: "#ffb020", glow: "rgba(255,176,32,0.45)", min: 3 },
  COLD: { color: "#6b7872", glow: "rgba(107,120,114,0.35)", min: 0 }
};
const FSM_TIER_ORDER = ["APEX", "ELITE", "EDGE", "SIGNAL", "WATCH", "COLD"];

/* matchup quality → filled quadrants (of 4) + color */
const FSM_MATCHUP = {
  ELITE: { q: 4, color: "#4ade80" },
  STRONG: { q: 3, color: "#86efac" },
  AVG: { q: 2, color: "#fbbf24" },
  WEAK: { q: 1, color: "#f97316" },
  DANGER: { q: 0, color: "#ef4444" }
};
const FSM_MATCHUP_ORDER = ["ELITE", "STRONG", "AVG", "WEAK", "DANGER"];
const FSM_TIER_DESC = {
  APEX: "greatest HR threat — model HR probability ≥ 18% this game",
  ELITE: "premium danger — model HR probability ≥ 13%",
  EDGE: "strong advantage — model HR probability ≥ 9%",
  SIGNAL: "positive signal — model HR probability ≥ 6%",
  WATCH: "marginal — model HR probability ≥ 3%",
  COLD: "do not deploy — model HR probability < 3%",
};
const FSM_MATCHUP_DESC = {
  ELITE: "every edge favors the batter (4/4 quadrants)",
  STRONG: "clear batter advantage (3/4)",
  AVG: "neutral matchup (2/4)",
  WEAK: "leans to the pitcher (1/4)",
  DANGER: "pitcher strongly favored (0/4)",
};

const TEAM_COLOR = {
  MIA: "#00a3e0", TOR: "#1d4f91", NYY: "#8a95a0", BOS: "#bd3039", COL: "#5b48a0",
  CHC: "#0e3386", ATL: "#ce1141", PHI: "#e81828", HOU: "#eb6e1f", TEX: "#003278",
  LAD: "#2f6fc0", SF: "#fd5a1e"
};

/* today's slate — supplied by the data file (window.SLATE_GAMES) */
const FSM_GAMES = window.SLATE_GAMES || [
{ id: "tor-mia", away: "TOR", home: "MIA", park: "loanDepot Park", time: "7:10 PM ET",
  weather: "Roof Closed · 72°F", wind: "Calm", hrFactor: 0.94, teams: ["TOR", "MIA"] }];


/* formatters */
const f3d = (v) => v.toFixed(3).replace(/^0/, ""); // .222
const fp = (v) => v.toFixed(1) + "%";
const f1 = (v) => v.toFixed(1);
const f2 = (v) => v.toFixed(2);
const fdeg = (v) => v.toFixed(1) + "°";

/* column defs — bucketsHi = higher is better (4 cuts), bucketsLo = lower is better */
const FSM_COLS = [
{ key: "odds", head: "ODDS", title: "HR prop odds (American)", group: "STATS", mode: "odds", fmt: (v) => String(v) },
{ key: "hr", head: "HR", title: "Home runs — season total", group: "STATS", bucketsHi: [28, 18, 10, 5], fmt: (v) => String(v) },
{ key: "avg", head: "BA", title: "Batting average", group: "STATS", bucketsHi: [0.290, 0.265, 0.240, 0.215], fmt: f3d },
{ key: "obp", head: "OBP", title: "On-base percentage", group: "STATS", bucketsHi: [0.360, 0.335, 0.310, 0.290], fmt: f3d },
{ key: "slg", head: "SLG", title: "Slugging percentage", group: "STATS", bucketsHi: [0.520, 0.460, 0.410, 0.370], fmt: f3d },
{ key: "iso", head: "ISO", title: "Isolated power (SLG − AVG) — a core HR driver", group: "STATS", bucketsHi: [0.250, 0.180, 0.120, 0.070], fmt: f3d },
{ key: "xslg", head: "xSLG", title: "Expected slugging from quality of contact", group: "STATS", bucketsHi: [0.520, 0.450, 0.400, 0.350], fmt: f3d },
{ key: "woba", head: "wOBA", title: "Weighted on-base average", group: "STATS", bucketsHi: [0.370, 0.345, 0.320, 0.300], fmt: f3d },
{ key: "xwoba", head: "xwOBA", title: "Expected weighted on-base average", group: "STATS", bucketsHi: [0.350, 0.330, 0.310, 0.290], fmt: f3d },
{ key: "babip", head: "BABIP", title: "Batting average on balls in play", group: "STATS", bucketsHi: [0.330, 0.300, 0.270, 0.240], fmt: f3d },
{ key: "bbpct", head: "BB%", title: "Walk rate", group: "STATS", bucketsHi: [12, 9, 7, 5], fmt: fp },
{ key: "pa", head: "PA", title: "Plate appearances — sample size", group: "STATS", mode: "neutral", fmt: (v) => String(v) },
{ key: "hrpa", head: "HR/PA", title: "Home runs per plate appearance (model output)", group: "STATS", mode: "headline", fmt: (v) => v.toFixed(3) },
{ key: "whiff", head: "WHIFF%", title: "Whiff rate — LOWER is better", group: "STRIKES", bucketsLo: [18, 24, 30, 36], fmt: fp },
{ key: "kpct", head: "K%", title: "Strikeout rate — LOWER is better", group: "STRIKES", bucketsLo: [15, 20, 25, 30], fmt: fp },
{ key: "swstr", head: "SWSTR%", title: "Swinging-strike rate — LOWER is better", group: "STRIKES", bucketsLo: [8, 11, 14, 17], fmt: fp },
{ key: "ev", head: "EV", title: "Average exit velocity (mph)", group: "STATCAST", bucketsHi: [92, 90, 88, 86], fmt: f1 },
{ key: "maxev", head: "MAX EV", title: "Max exit velocity (mph) — peak raw power", group: "STATCAST", bucketsHi: [112, 109, 106, 103], fmt: f1 },
{ key: "barrel", head: "BARREL%", title: "Barrel rate — optimal EV + launch-angle contact, the best HR predictor", group: "STATCAST", bucketsHi: [8, 6, 4.5, 3], fmt: fp },
{ key: "pullbrl", head: "PULLBRL%", title: "Pulled-barrel rate — barrels hit to the pull side", group: "STATCAST", bucketsHi: [6, 4, 2.5, 1.5], fmt: fp },
{ key: "pullair", head: "PULLAIR%", title: "Pulled-air rate — fly balls/liners to the pull side, prime HR contact", group: "STATCAST", bucketsHi: [26, 21, 16, 12], fmt: fp },
{ key: "hh", head: "HH%", title: "Hard-hit rate (95+ mph exit velo)", group: "STATCAST", bucketsHi: [45, 40, 34, 28], fmt: fp },
{ key: "gb", head: "GB%", title: "Ground-ball rate — LOWER is better for HR", group: "STATCAST", bucketsLo: [35, 40, 45, 50], fmt: fp },
{ key: "fb", head: "FB%", title: "Fly-ball rate — more fly balls = more HR chances", group: "STATCAST", bucketsHi: [42, 36, 30, 24], fmt: fp },
{ key: "ld", head: "LD%", title: "Line-drive rate", group: "STATCAST", bucketsHi: [28, 24, 20, 17], fmt: fp },
{ key: "la", head: "LA°", title: "Launch angle — HR sweet spot ≈ 15°", group: "STATCAST", special: "la", fmt: fdeg },
{ key: "sweet", head: "LA SS%", title: "Launch-angle sweet-spot rate — batted balls at 8–32°", group: "STATCAST", bucketsHi: [38, 34, 30, 26], fmt: fp },
{ key: "pull", head: "PULL%", title: "Pull rate — pull-side power", group: "STATCAST", bucketsHi: [45, 40, 35, 30], fmt: fp },
{ key: "center", head: "CENTER%", title: "Center rate — lower favors pull-side power", group: "STATCAST", bucketsLo: [22, 26, 32, 40], fmt: fp },
{ key: "hrfb", head: "HR/FB%", title: "Home-run-per-fly-ball rate", group: "STATCAST", bucketsHi: [20, 14, 9, 5], fmt: fp },
{ key: "fast", head: "FAST%", title: "Fast-swing rate — swings at 75+ mph bat speed", group: "STATCAST", bucketsHi: [40, 28, 18, 10], fmt: fp },
{ key: "squp", head: "SQUP%", title: "Squared-up rate — efficiency of contact vs max EV", group: "STATCAST", bucketsHi: [36, 32, 28, 24], fmt: fp },
{ key: "blast", head: "BLAST%", title: "Blast rate — fast swing + squared-up contact", group: "STATCAST", bucketsHi: [16, 11, 7, 4], fmt: fp },
{ key: "opphr", head: "OPP HR/9", title: "Opposing pitcher HR allowed per 9 — HIGHER favors the batter", group: "MATCHUP", danger: true, bucketsHi: [1.5, 1.3, 1.0, 0.7], fmt: f2 }];

const FSM_COLSPAN = 3 + FSM_COLS.length; // tier + player + matchup + stats

function fsmBucket(col, v) {
  if (v == null) return "NA";
  if (col.special === "la") {
    const d = Math.abs(v - 15);
    if (d <= 2) return "ELITE";if (d <= 4) return "STRONG";if (d <= 7) return "AVERAGE";if (d <= 10) return "WEAK";return "DANGER";
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

/* conic-gradient quadrant pie */
function fsmPie(filled, color) {
  const empty = "#2a2a3a",gap = "#04070a";
  const stops = [];
  for (let i = 0; i < 4; i++) {
    const c = i < filled ? color : empty;
    const s = i * 90,e = s + 90;
    stops.push(`${gap} ${s}deg ${s + 3}deg`, `${c} ${s + 3}deg ${e}deg`);
  }
  return `conic-gradient(from -2deg, ${stops.join(", ")})`;
}

function FsmCell({ col, row }) {
  const v = row[col.key];
  if (col.mode === "odds") return <td className="fsm-cell fsm-cell--odds">{v == null ? "—" : col.fmt(v)}</td>;
  if (col.mode === "headline") return <td className="fsm-cell fsm-cell--headline">{v == null ? "—" : col.fmt(v)}</td>;
  if (col.mode === "neutral") return <td className="fsm-cell fsm-cell--neutral">{v == null ? "—" : col.fmt(v)}</td>;
  const b = fsmBucket(col, v);
  return <td className={`fsm-cell ${FSM_BUCKET_CLASS[b] || ""}`}>{v == null ? "—" : col.fmt(v)}</td>;
}

/* Build a FanDuel link for a batter's HR market (demo deep-link). */
function fsmFanduelUrl(row) {
  return "https://sportsbook.fanduel.com/search?query=" + encodeURIComponent(row.name + " home run");
}

function FsmRow({ row, cols, showGame, onBatter, onPitch }) {
  const t = FSM_TIERS[row.tier] || FSM_TIERS.COLD;
  const m = FSM_MATCHUP[row.quality] || FSM_MATCHUP.AVG;
  const game = showGame ? (window.SLATE_GAMES || []).find((g) => g.id === row.gameId) : null;
  const addToFanduel = (e) => {
    e.stopPropagation();
    window.open(fsmFanduelUrl(row), "_blank", "noopener");
  };
  return (
    <tr className="fsm-row">
      <td className="fsm-tiercell">
        <button
          type="button"
          className="fsm-tier"
          style={{ "--tc": t.color, "--tg": t.glow }}
          onClick={addToFanduel}
          title={`Add ${row.name} (${row.tier}) to FanDuel`}
          aria-label={`Add ${row.name} to FanDuel`}>
          
          <span className="fsm-tier__icon"><FsmTierIcon tier={row.tier} /></span>
          <span className="fsm-tier__label">{row.tier}</span>
          <span className="fsm-tier__add" aria-hidden="true">+ FD</span>
        </button>
      </td>
      <td className="fsm-player">
        <button type="button" className="fsm-player__in" onClick={() => onBatter(row)} title={`Open ${row.name} batter card`}>
          <span className="fsm-player__dot" style={{ background: TEAM_COLOR[row.teamAbbr] || t.color, color: TEAM_COLOR[row.teamAbbr] || t.color }} />
          <span className="fsm-player__col">
            <span className="fsm-player__name">{row.name}</span>
            <span className="fsm-player__meta">{row.teamAbbr}<i className="fsm-player__bar">|</i>{row.bats}</span>
            {game && <span className="fsm-player__game">{game.away}@{game.home}<i className="fsm-player__bar">·</i>{game.time}</span>}
          </span>
        </button>
      </td>
      <td className="fsm-matchup">
        <button type="button" className="fsm-matchup__in" onClick={() => onPitch(row)} title="Open Pitch Mix Analysis">
          <span className="fsm-pie" style={{ background: fsmPie(m.q, m.color) }} />
          <span className="fsm-matchup__label" style={{ color: m.color }}>
            <span>{row.quality}</span><span className="fsm-matchup__sub">MATCHUP</span>
          </span>
        </button>
      </td>
      {cols.map((c) => <FsmCell key={c.key} col={c} row={row} />)}
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

const FSM_FOCUS_OPTS = [
{ id: "all", label: "ALL", desc: "All hitter profiles." },
{ id: "power", label: "POWER", desc: "Sluggers: Barrel% ≥ 4.5 OR SLG ≥ .470." },
{ id: "contact", label: "CONTACT", desc: "Contact hitters: AVG ≥ .255." },
{ id: "matchup", label: "MATCHUP", desc: "Batters in an ELITE or STRONG matchup vs today's pitcher." }];


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

function FsmTable({ rows, cols, showGame, onBatter, onPitch, onReorder, onSort, sortState }) {
  const thProps = (c) => ({
    draggable: true,
    onDragStart: (e) => { fsmDragKey = c.key; e.dataTransfer.effectAllowed = "move"; },
    onDragOver: (e) => { e.preventDefault(); e.currentTarget.classList.add("is-drop"); },
    onDragLeave: (e) => e.currentTarget.classList.remove("is-drop"),
    onDrop: (e) => { e.preventDefault(); e.currentTarget.classList.remove("is-drop"); if (fsmDragKey && fsmDragKey !== c.key) onReorder(fsmDragKey, c.key); fsmDragKey = null; },
    onDoubleClick: () => onSort(c.key),
    title: c.title + " — drag to reorder · double-click to sort",
  });
  const arrow = (c) => sortState && sortState.key === c.key ? (sortState.dir === "desc" ? " ▼" : " ▲") : "";
  const bands = [];
  cols.forEach((c) => { const g = c.group || "STATS"; const last = bands[bands.length - 1]; if (last && last.label === g) last.span++; else bands.push({ label: g, span: 1 }); });
  return (
    <table className="fsm-table">
      <colgroup>
        <col style={{ width: "72px" }} /><col style={{ width: "128px" }} /><col style={{ width: "98px" }} />
        {cols.map((c) => <col key={c.key} style={{ width: c.key === "pa" ? "46px" : "60px" }} />)}
      </colgroup>
      <thead>
        <tr className="fsm-grouprow">
          <th className="fsm-gband fsm-gband--id" colSpan={3}>BATTER</th>
          {bands.map((b, i) => <th key={i} className={"fsm-gband fsm-gband--" + b.label.toLowerCase()} colSpan={b.span}>{b.label}</th>)}
        </tr>
        <tr className="fsm-colhead">
          <th className="fsm-th-tier">TIER</th>
          <th className="fsm-th-player">PLAYER</th>
          <th className="fsm-th-matchup">MATCHUP</th>
          {cols.map((c) =>
          <th key={c.key} className={"fsm-th-stat" + (c.danger ? " fsm-th-danger" : "") + (sortState && sortState.key === c.key ? " is-sorted" : "")} {...thProps(c)}>{c.head}{arrow(c)}</th>
          )}
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => <FsmRow key={r.id} row={r} cols={cols} showGame={showGame} onBatter={onBatter} onPitch={onPitch} />)}
      </tbody>
    </table>);

}

/* ---- detail overlays: Batter Card + Pitch Mix Analysis ---- */
const FSM_BUCKET_COLOR = { ELITE: "#1aff66", STRONG: "#6dffae", AVERAGE: "#b8c2c0", WEAK: "#ff8a93", DANGER: "#ff3344", NA: "#6b7872", NEUTRAL: "#b8c2c0" };
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

function fsmHash(str) {let h = 2166136261;for (let i = 0; i < str.length; i++) {h ^= str.charCodeAt(i);h = Math.imul(h, 16777619);}return h >>> 0;}
function fsmSeeded(seed) {let a = seed >>> 0;return () => {a |= 0;a = a + 0x6D2B79F5 | 0;let t = Math.imul(a ^ a >>> 15, 1 | a);t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;return ((t ^ t >>> 14) >>> 0) / 4294967296;};}

const FSM_PITCH_TYPES = [
{ code: "FF", name: "4-Seam", vlo: 92, vhi: 99 },
{ code: "SI", name: "Sinker", vlo: 90, vhi: 96 },
{ code: "FC", name: "Cutter", vlo: 87, vhi: 93 },
{ code: "SL", name: "Slider", vlo: 82, vhi: 89 },
{ code: "CH", name: "Change", vlo: 82, vhi: 89 },
{ code: "CB", name: "Curve", vlo: 76, vhi: 83 }];

const FSM_PFIRST = ["Tanner", "Bryce", "Logan", "Spencer", "Garrett", "Hunter", "Kenji", "Marco", "Dylan", "Easton", "Carlos", "Reese", "Jaden", "Cole", "Aaron", "Miguel"];
const FSM_PLAST = ["Sandoval", "Whitlock", "Karras", "Beaumont", "Okada", "Reyes", "Hollis", "Vargas", "Pemberton", "Costa", "Lindgren", "Mahoney", "Ferro", "Nakamura", "Brennan"];

function fsmPitchData(row) {
  const game = FSM_GAMES.find((g) => g.id === row.gameId);
  const opp = game ? game.teams.find((t) => t !== row.teamAbbr) : "OPP";
  const rng = fsmSeeded(fsmHash(row.gameId + ":" + opp));
  const pick = (a) => a[Math.floor(rng() * a.length)];
  const pitcher = { name: pick(FSM_PFIRST) + " " + pick(FSM_PLAST), team: opp, throws: rng() < 0.5 ? "L" : "R" };
  const rest = [...FSM_PITCH_TYPES.slice(1)].sort(() => rng() - 0.5);
  const chosen = [FSM_PITCH_TYPES[0], ...rest.slice(0, 3 + (rng() < 0.5 ? 1 : 0))];
  const weights = chosen.map((p, i) => i === 0 ? 0.34 + rng() * 0.18 : 0.06 + rng() * 0.22);
  const sum = weights.reduce((a, b) => a + b, 0);
  const power = Math.min(1, Math.max(0, (row.hrprob - 3) / 18));
  const pitches = chosen.map((p, i) => {
    const woba = +Math.max(0.18, Math.min(0.46, 0.255 + power * 0.11 + (rng() - 0.4) * 0.15)).toFixed(3);
    return {
      code: p.code, name: p.name,
      usagePct: Math.round(weights[i] / sum * 100),
      velo: +(p.vlo + rng() * (p.vhi - p.vlo)).toFixed(1),
      whiff: Math.round(8 + rng() * 30),
      woba,
      hrpct: +Math.max(0, power * 4.5 + (rng() - 0.5) * 3.5).toFixed(1),
      verdict: woba >= 0.360 ? "ATTACK" : woba >= 0.300 ? "NEUTRAL" : "AVOID"
    };
  });
  let tot = pitches.reduce((a, p) => a + p.usagePct, 0);
  pitches[0].usagePct += 100 - tot;
  pitches.sort((a, b) => b.usagePct - a.usagePct);
  return { pitcher, pitches };
}

function FsmStat({ label, value, color }) {
  return <div className="fsm-stat"><span className="fsm-stat__l">{label}</span><span className="fsm-stat__v" style={{ color }}>{value}</span></div>;
}

function FsmBatterCard({ row, onClose, onPitch }) {
  const t = FSM_TIERS[row.tier] || FSM_TIERS.COLD;
  const m = FSM_MATCHUP[row.quality] || FSM_MATCHUP.AVG;
  const game = FSM_GAMES.find((g) => g.id === row.gameId);
  const pd = fsmPitchData(row);
  const groups = [
  { title: "POWER & CONTACT", keys: ["avg", "slg", "babip", "xwoba", "barrel", "hrpa"] },
  { title: "BATTED-BALL PROFILE", keys: ["ev", "la", "hh", "gb", "ld", "pull", "center"] }];

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
          <span className="fsm-card__probval" style={{ color: t.color }}>{row.hrprob.toFixed(1)}%</span>
          <span className="fsm-card__problbl">MODEL HR PROB</span>
        </div>
        <button className="fsm-card__close" onClick={onClose} aria-label="Close">✕</button>
      </div>
      <div className="fsm-card__matchup">
        <span className="fsm-pie fsm-pie--lg" style={{ background: fsmPie(m.q, m.color) }} />
        <div className="fsm-card__mtext">
          <span className="fsm-card__mq" style={{ color: m.color }}>{row.quality} MATCHUP</span>
          <span className="fsm-card__msub">vs {pd.pitcher.name} ({pd.pitcher.team} · {pd.pitcher.throws}HP) · OPP HR/9 {fsmStatVal("opphr", row)}{game ? ` · PARK HR ${game.hrFactor.toFixed(2)}×` : ""}</span>
        </div>
        <button className="fsm-card__pitchbtn" onClick={onPitch}>PITCH MIX ANALYSIS →</button>
      </div>
      {groups.map((g) =>
      <div className="fsm-card__sec" key={g.title}>
          <div className="fsm-card__sectitle">{g.title}</div>
          <div className="fsm-card__stats">
            {g.keys.map((k) => <FsmStat key={k} label={fsmColFor(k).head} value={fsmStatVal(k, row)} color={fsmStatColor(k, row)} />)}
          </div>
        </div>
      )}
      <div className="fsm-card__foot">
        <span className="fsm-card__env">{game ? `${game.park} · ${game.weather} · WIND ${game.wind}` : ""}</span>
        <a className="fsm-card__fd" href={fsmFanduelUrl(row)} target="_blank" rel="noopener">+ ADD TO FANDUEL</a>
      </div>
    </div>);

}

/* deterministic head-to-head dataset for a batter vs the opposing starter */
function fsmH2HData(row) {
  const pd = fsmPitchData(row);
  const rng = fsmSeeded(fsmHash(row.id + "|h2h"));
  const power = Math.min(1, Math.max(0, (row.hrprob - 3) / 18));
  const batHand = row.bats === "S" ? pd.pitcher.throws === "L" ? "R" : "L" : row.bats;
  const r = (lo, hi, d = 1) => +(lo + rng() * (hi - lo)).toFixed(d);

  const hr9 = +(0.75 + power * 0.85 + rng() * 0.55).toFixed(2);
  const pitcher = {
    ...pd.pitcher,
    last: pd.pitcher.name.split(" ").slice(-1)[0],
    era: r(2.9, 5.4, 2), whip: r(0.98, 1.46, 2), kpct: r(15, 31, 1), bbpct: r(5, 11.5, 1),
    hr9, xhr9: +(hr9 + (rng() - 0.5) * 0.4).toFixed(2), avg: r(0.212, 0.288, 3),
    tier: hr9 >= 1.45 ? "HR TARGET" : hr9 >= 1.05 ? "VULNERABLE" : "TOUGH"
  };

  const BTIER = { APEX: "S+", ELITE: "S", EDGE: "A", SIGNAL: "B", WATCH: "C", COLD: "D" };
  const batter = {
    name: row.name, last: row.name.replace("…", "").split(" ").slice(-1)[0], team: row.teamAbbr, bats: row.bats,
    avg: row.avg, hr: Math.round(8 + power * 34), iso: +(row.slg - row.avg).toFixed(3),
    kpct: r(13, 30, 1), whiff: r(18, 40, 1), barrel: row.barrel == null ? null : row.barrel, ev: row.ev,
    tier: BTIER[row.tier] || "C", confidence: Math.round(58 + power * 37),
    ev_odds: "+" + Math.round(Math.min(950, Math.max(230, 980 - row.hrprob * 31)))
  };

  // 3x3 strike-zone xSLG (rows top→bottom). Heart of zone runs hotter.
  const zoneBase = 0.44 + power * 0.26;
  const zoneBoost = [0.00, 0.05, -0.01, 0.04, 0.10, 0.02, -0.03, 0.03, -0.05];
  const zone = zoneBoost.map((b) => +Math.min(0.86, Math.max(0.36, zoneBase + b + (rng() - 0.5) * 0.16)).toFixed(3));

  const zoneAvg = zone.reduce((a, b) => a + b, 0) / 9;
  const edge = Math.round((zoneAvg - 0.50) * 100 + (hr9 - 1.0) * 14);

  const h2h = { pa: Math.round(8 + rng() * 32), avg: r(0.205, 0.372, 3), xslg: 0, hr: Math.round(rng() * 3 + power * 2), kpct: r(11, 28, 1), bbpct: r(4, 13, 1) };
  h2h.xslg = +Math.min(0.74, h2h.avg + 0.17 + power * 0.13).toFixed(3);

  // pitcher pitch mix vs this batter's hand
  const mix = pd.pitches.map((p) => {
    const vslg = +Math.min(0.85, Math.max(0.12, 0.20 + power * 0.4 + (rng() - 0.45) * 0.34)).toFixed(3);
    return { name: p.name, usage: p.usagePct, vslg, iso: +Math.max(0, vslg - r(0.16, 0.24, 3)).toFixed(3),
      hr: Math.round(rng() * 3 * power), hh: r(18, 46, 1), whiff: p.whiff, k: r(12, 36, 1) };
  });

  // batter hit profile vs this pitcher's hand (same pitch families, batter perspective)
  const profile = pd.pitches.map((p) => {
    const vslg = +Math.min(0.90, Math.max(0.18, 0.30 + power * 0.42 + (rng() - 0.4) * 0.3)).toFixed(3);
    return { name: p.name, usage: Math.round(45 + rng() * 45), vslg, iso: +Math.max(0, vslg - r(0.14, 0.26, 3)).toFixed(3),
      hr: Math.round(rng() * 6 + power * 12), hh: r(20, 64, 1), whiff: r(11, 64, 1), k: r(9, 28, 1) };
  });

  return { pitcher, batter, zone, edge, h2h, mix, profile, batHand };
}

const fsmS3 = (v) => v == null ? "—" : v.toFixed(3).replace(/^0/, "");
const fsmP1 = (v) => v == null ? "—" : v.toFixed(1) + "%";

/* zone-cell heat (xSLG: high = batter advantage = green) */
function fsmZoneClass(v) {
  if (v >= 0.70) return "is-elite";if (v >= 0.62) return "is-strong";if (v >= 0.54) return "is-avg";if (v >= 0.47) return "is-weak";return "is-danger";
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

function FsmPitchTable({ title, accent, rows }) {
  return (
    <div className={"fsm-pt fsm-pt--" + accent}>
      <div className="fsm-pt__title">{title}</div>
      <div className="fsm-pt__grid">
        <div className="fsm-pt__hd"><span>PITCH TYPE</span><span>USAGE</span><span>vSLG</span><span>ISO</span><span>HR</span><span>HH%</span><span>WHIFF%</span><span>K%</span></div>
        {rows.map((p, i) =>
        <div className="fsm-pt__row" key={i}>
            <span className="fsm-pt__type">{p.name}</span>
            <span className="fsm-pt__usage"><span className="fsm-pt__bar" style={{ width: Math.min(100, p.usage) + "%" }} /><i>{p.usage}%</i></span>
            <span className={"fsm-ht " + fsmHeatClass(p.vslg, [0.520, 0.430, 0.350, 0.270])}>{fsmS3(p.vslg)}</span>
            <span className={"fsm-ht " + fsmHeatClass(p.iso, [0.260, 0.180, 0.120, 0.070])}>{fsmS3(p.iso)}</span>
            <span className="fsm-pt__num">{p.hr}</span>
            <span className="fsm-pt__num">{fsmP1(p.hh)}</span>
            <span className="fsm-pt__num">{fsmP1(p.whiff)}</span>
            <span className="fsm-pt__num">{fsmP1(p.k)}</span>
          </div>
        )}
      </div>
    </div>);

}

function FsmPitchMix({ row, onClose, onBatter }) {
  const d = fsmH2HData(row);
  const pColor = TEAM_COLOR[d.pitcher.team] || "#ff3344";
  const bColor = TEAM_COLOR[d.batter.team] || "#3b6fff";
  const pTierColor = d.pitcher.tier === "HR TARGET" ? "#1aff66" : d.pitcher.tier === "VULNERABLE" ? "#ffb020" : "#ff3344";
  const initials = (n) => n.replace("…", "").split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase();

  return (
    <div className="fsm-card fsm-card--h2h">
      <button className="fsm-card__close fsm-card__close--abs" onClick={onClose} aria-label="Close">✕</button>

      <div className="fsm-h2h__top">
        {/* PITCHER */}
        <div className="fsm-h2h__side" style={{ "--tc": pColor }}>
          <div className="fsm-h2h__nameblock">
            <div className="fsm-h2h__team">{d.pitcher.team}</div>
            <div className="fsm-h2h__name">{d.pitcher.name}</div>
            <span className="fsm-h2h__badge">{d.pitcher.throws}HP</span>
          </div>
          <div className="fsm-h2h__portrait"><span>{initials(d.pitcher.name)}</span></div>
          <FsmStatRail title={`2024 vs ${d.batHand}HB`} stats={[
          ["ERA", d.pitcher.era.toFixed(2)], ["WHIP", d.pitcher.whip.toFixed(2)],
          ["K%", d.pitcher.kpct.toFixed(1)], ["BB%", d.pitcher.bbpct.toFixed(1)],
          ["HR/9", d.pitcher.hr9.toFixed(2), d.pitcher.hr9 >= 1.45 ? "#1aff66" : null],
          ["xHR/9", d.pitcher.xhr9.toFixed(2)], ["AVG", fsmS3(d.pitcher.avg)]]
          } />
          <div className="fsm-h2h__tier"><span>PITCHER TIER</span><b style={{ color: pTierColor }}>{d.pitcher.tier}</b></div>
        </div>

        {/* CENTER */}
        <div className="fsm-h2h__center">
          <div className="fsm-h2h__ctitle">STRIKE ZONE MATCHUP<span>xSLG BY LOCATION</span></div>
          <div className="fsm-h2h__zone">
            {d.zone.map((v, i) => <div key={i} className={"fsm-zcell " + fsmZoneClass(v)}>{fsmS3(v)}</div>)}
          </div>
          <div className="fsm-h2h__edge">
            <span className="fsm-h2h__edgelbl">MATCHUP EDGE</span>
            <b style={{ color: d.edge >= 0 ? "#1aff66" : "#ff3344" }}>{d.edge >= 0 ? "+" : ""}{d.edge}%</b>
            <span className="fsm-h2h__edgeside">{d.edge >= 0 ? "BATTER ADVANTAGE" : "PITCHER ADVANTAGE"}</span>
          </div>
          <div className="fsm-h2h__h2h">
            <div className="fsm-h2h__h2htitle">HEAD TO HEAD <span>CAREER · {d.batter.last} vs {d.pitcher.last}</span></div>
            <div className="fsm-h2h__h2hstrip">
              {[["PA", d.h2h.pa], ["AVG", fsmS3(d.h2h.avg)], ["xSLG", fsmS3(d.h2h.xslg)], ["HR", d.h2h.hr], ["K%", d.h2h.kpct.toFixed(1)], ["BB%", d.h2h.bbpct.toFixed(1)]].map(([l, v]) =>
              <div key={l}><span>{l}</span><b>{v}</b></div>
              )}
            </div>
          </div>
          <div className="fsm-h2h__btier">
            <div><span>BATTER TIER</span><b>{d.batter.tier}</b></div>
            <div><span>CONFIDENCE</span><b style={{ color: "#1aff66" }}>{d.batter.confidence}</b></div>
            <div><span>HR EV</span><b style={{ color: "#ffb020" }}>{d.batter.ev_odds}</b></div>
          </div>
        </div>

        {/* BATTER */}
        <div className="fsm-h2h__side fsm-h2h__side--right" style={{ "--tc": bColor }}>
          <div className="fsm-h2h__nameblock">
            <div className="fsm-h2h__team">{d.batter.team}</div>
            <div className="fsm-h2h__name">{d.batter.name}</div>
            <span className="fsm-h2h__badge">BATS {d.batter.bats}</span>
          </div>
          <div className="fsm-h2h__portrait"><span>{initials(d.batter.name)}</span></div>
          <FsmStatRail title={`2024 vs ${d.pitcher.throws}HP`} stats={[
          ["AVG", fsmS3(d.batter.avg)], ["ISO", fsmS3(d.batter.iso)],
          ["HR", d.batter.hr, "#1aff66"], ["K%", d.batter.kpct.toFixed(1)],
          ["WHIFF%", d.batter.whiff.toFixed(1)], ["BARREL%", d.batter.barrel == null ? "—" : d.batter.barrel.toFixed(1)],
          ["EV", d.batter.ev.toFixed(1)]]
          } />
          <div className="fsm-h2h__tier"><span>BATTER TIER</span><b style={{ color: (FSM_TIERS[row.tier] || FSM_TIERS.COLD).color }}>{row.tier}</b></div>
        </div>
      </div>

      <div className="fsm-h2h__tables">
        <FsmPitchTable title={`${d.pitcher.last} PITCH MIX vs ${d.batHand}HB`} accent="red" rows={d.mix} />
        <FsmPitchTable title={`${d.batter.last} HIT PROFILE vs ${d.pitcher.throws}HP`} accent="blue" rows={d.profile} />
      </div>

      <div className="fsm-card__foot">
        <button className="fsm-card__pitchbtn" onClick={onBatter}>← BATTER CARD</button>
        <a className="fsm-card__fd" href={fsmFanduelUrl(row)} target="_blank" rel="noopener">+ ADD {d.batter.last.toUpperCase()} TO FANDUEL</a>
      </div>
    </div>);

}

function FsmDetailModal({ modal, onClose, setModal }) {
  React.useEffect(() => {
    const h = (e) => {if (e.key === "Escape") onClose();};
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);
  if (!modal) return null;
  return (
    <div className="fsm-modal" onClick={onClose}>
      <div className="fsm-modal__inner" onClick={(e) => e.stopPropagation()}>
        {modal.type === "batter" ?
        <FsmBatterCard row={modal.row} onClose={onClose} onPitch={() => setModal({ type: "pitch", row: modal.row })} /> :
        <FsmPitchMix row={modal.row} onClose={onClose} onBatter={() => setModal({ type: "batter", row: modal.row })} />}
      </div>
    </div>);

}

const FSM_ARSENAL = [
  { code: "FF", name: "4-Seam" }, { code: "SI", name: "Sinker" }, { code: "FC", name: "Cutter" },
  { code: "SL", name: "Slider" }, { code: "CH", name: "Change" }, { code: "CB", name: "Curve" },
];

/* Recompute a batter's stats vs their opposing starter's hand + the selected pitch types.
   Deterministic per batter/pitch; "all pitches selected" = baseline-vs-hand. */
function fsmAdjustRow(row, on) {
  if (!on) return row;
  const pd = fsmPitchData(row);
  const opp = pd.pitcher.throws, bats = row.bats;
  const platoon = bats === "S" ? 1.0 : (bats === "L" && opp === "R") || (bats === "R" && opp === "L") ? 1.06 : 0.93;
  const m = (code) => 0.8 + fsmSeeded(fsmHash(row.id + code))() * 0.45;
  let w = 0, mm = 0;
  pd.pitches.forEach((p) => { w += p.usagePct; mm += m(p.code) * p.usagePct; });
  const arsenal = (w > 0 ? mm / w : 1) / 1.025;
  const factor = platoon * arsenal;
  const o = { ...row, vsPitcher: pd.pitcher, adjFactor: factor };
  const up = (k, min, max, d) => { if (o[k] != null) o[k] = +Math.max(min, Math.min(max, o[k] * factor)).toFixed(d); };
  ["avg", "obp", "slg", "iso", "xslg", "woba", "xwoba", "babip"].forEach((k) => up(k, 0.08, 0.86, 3));
  ["barrel", "hh", "hrfb", "pullbrl", "pullair", "sweet", "blast", "squp", "fast", "ld"].forEach((k) => up(k, 0, 100, 1));
  if (o.hrpa != null) o.hrpa = +Math.max(0, Math.min(0.09, o.hrpa * factor)).toFixed(3);
  o.hrprob = +Math.max(1, Math.min(35, o.hrprob * factor)).toFixed(1);
  const inv = (k) => { if (o[k] != null) o[k] = +Math.max(0, Math.min(100, o[k] / factor)).toFixed(1); };
  ["whiff", "kpct", "swstr", "gb"].forEach(inv);
  if (o.ev != null) o.ev = +Math.max(80, Math.min(96, o.ev * (1 + (factor - 1) * 0.3))).toFixed(1);
  if (o.maxev != null) o.maxev = +Math.max(98, Math.min(122, o.maxev * (1 + (factor - 1) * 0.2))).toFixed(1);
  o.odds = "+" + Math.round(Math.max(150, Math.min(1200, 980 - o.hrprob * 31)));
  return o;
}

function FullSlateMatrix({ rows, total, onOpen, filterNote, embedded }) {
  const [view, setView] = React.useState("game");
  const [selGame, setSelGame] = React.useState("all");
  const [group, setGroup] = React.useState("all");
  const [focus, setFocus] = React.useState("all");
  const [modal, setModal] = React.useState(null);
  const [pmOn, setPmOn] = React.useState(true);
  const [colPref, setColPref] = React.useState(() => {
    try { const s = JSON.parse(localStorage.getItem("fsmColPref")); if (s && Array.isArray(s.order)) return s; } catch (e) {}
    return { order: FSM_COLS.map((c) => c.key), hidden: [] };
  });
  const [colOpen, setColOpen] = React.useState(false);
  const [colInfo, setColInfo] = React.useState(null);
  const [sortState, setSortState] = React.useState(null);
  const [dataVersion, setDataVersion] = React.useState(0);
  React.useEffect(() => {
    const handler = () => setDataVersion(v => v + 1);
    window.addEventListener("hrEngineDataLoaded", handler);
    return () => window.removeEventListener("hrEngineDataLoaded", handler);
  }, []);
  const onSort = (key) => setSortState((s) => s && s.key === key ? { key, dir: s.dir === "desc" ? "asc" : "desc" } : { key, dir: "desc" });
  const onReorder = (fromKey, toKey) => setColPref((p) => { if (fromKey === toKey) return p; const o = p.order.filter((k) => k !== fromKey); o.splice(o.indexOf(toKey), 0, fromKey); return { ...p, order: o }; });
  React.useEffect(() => { try { localStorage.setItem("fsmColPref", JSON.stringify(colPref)); } catch (e) {} }, [colPref]);
  React.useEffect(() => { setColPref((p) => { const missing = FSM_COLS.filter((c) => !p.order.includes(c.key)).map((c) => c.key); return missing.length ? { ...p, order: [...p.order, ...missing] } : p; }); }, []);
  const activeCols = colPref.order.map((k) => FSM_COLS.find((c) => c.key === k)).filter((c) => c && !colPref.hidden.includes(c.key));
  const toggleCol = (k) => setColPref((p) => ({ ...p, hidden: p.hidden.includes(k) ? p.hidden.filter((x) => x !== k) : [...p.hidden, k] }));
  const moveCol = (idx, dir) => setColPref((p) => { const o = [...p.order]; const j = idx + dir; if (j < 0 || j >= o.length) return p; [o[idx], o[j]] = [o[j], o[idx]]; return { ...p, order: o }; });
  const resetCols = () => setColPref({ order: FSM_COLS.map((c) => c.key), hidden: [] });
  const [secs, setSecs] = React.useState(3);
  React.useEffect(() => {const id = setInterval(() => setSecs((s) => (s + 1) % 600), 1000);return () => clearInterval(id);}, []);
  const timer = `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, "0")}`;

  const adjusted = React.useMemo(() => rows.map((r) => fsmAdjustRow(r, pmOn)), [rows, pmOn]);
  const sorted0 = [...adjusted].sort((a, b) => b.hrprob - a.hrprob);
  const sorted = sortState ? [...sorted0].sort((a, b) => {
    const av = a[sortState.key], bv = b[sortState.key];
    const an = av == null ? -Infinity : av, bn = bv == null ? -Infinity : bv;
    return sortState.dir === "desc" ? bn - an : an - bn;
  }) : sorted0;

  const passGroup = (r) =>
  group === "all" ? true : group === "qualified" ? r.pa >= 100 : ["APEX", "ELITE", "EDGE"].includes(r.tier);
  const passFocus = (r) => {
    if (focus === "all") return true;
    if (focus === "power") return r.barrel != null && r.barrel >= 4.5 || r.slg >= 0.470;
    if (focus === "contact") return r.avg >= 0.255;
    if (focus === "matchup") return ["ELITE", "STRONG"].includes(r.quality);
    return true;
  };

  const pool = sorted.filter((r) => (selGame === "all" || r.gameId === selGame) && passGroup(r) && passFocus(r));
  const gamesToShow = selGame === "all" ? FSM_GAMES : FSM_GAMES.filter((g) => g.id === selGame);

  const noteBits = [];
  if (group !== "all") noteBits.push(group === "qualified" ? "QUALIFIED" : "ELITE TARGETS");
  if (focus !== "all") noteBits.push("FOCUS " + focus.toUpperCase());
  if (selGame !== "all") noteBits.push("1 GAME");
  const note = noteBits.length ? noteBits.join(" · ") : filterNote || "NO ACTIVE FILTERS";

  const openBatter = (row) => setModal({ type: "batter", row });
  const openPitch = (row) => setModal({ type: "pitch", row });

  return (
    <div className={"fsm" + (embedded ? " fsm--embed" : "")} data-comment-anchor="fa19328b4d-div-592-5">
      {/* TOP BAR */}
      {embedded ? (
        <div className="fsm-embed-head">
          <span className="fsm-embed-title">PLAYER TARGETS <b>{pool.length}</b></span>
          <span className="fsm-embed-sub"><span className="fsm-live"><i className="fsm-live__dot" />LIVE</span> · {FSM_GAMES.length} GAMES · UPD {timer} AGO</span>
        </div>
      ) : (
      <div className="fsm-topbar">
        <div className="fsm-topbar__titles">
          <h1 className="fsm-title">FULL SLATE INTELLIGENCE MATRIX</h1>
          <div className="fsm-sub">LIVE HR THREAT SCAN · MATCHUP / BARREL / ENVIRONMENT / DEPLOYMENT READINESS</div>
        </div>
        <div className="fsm-topbar__status">
          <span className="fsm-live"><i className="fsm-live__dot" />LIVE</span>
          <span className="fsm-stat-pill">{pool.length} / {total} BATTERS</span>
          <span className="fsm-stat-pill">{FSM_GAMES.length} GAMES</span>
          <span className="fsm-clock">UPD {timer} AGO</span>
        </div>
      </div>
      )}

      {/* CONTROLS + LEGENDS */}
      <div className="fsm-controls">
        <div className="fsm-viewtoggle" role="tablist">
          <button className={view === "game" ? "is-on" : ""} title="Group batters by game, each under its matchup header (park, time, weather, HR factor)." onClick={() => setView("game")}>GAME VIEW</button>
          <button className={view === "player" ? "is-on" : ""} title="Flat list of every batter on the slate, ranked by model HR probability." onClick={() => setView("player")}>PLAYER VIEW</button>
        </div>
        <div className="fsm-legends">
          <div className="fsm-legend">
            <span className="fsm-legend__title">TIER</span>
            {FSM_TIER_ORDER.map((t) =>
            <span className="fsm-tierpill" key={t} style={{ "--tc": FSM_TIERS[t].color, "--tg": FSM_TIERS[t].glow }} title={`${t} tier — ${FSM_TIER_DESC[t]}`}>{t}</span>
            )}
          </div>
          <div className="fsm-legend">
            <span className="fsm-legend__title" title="Matchup quality: the batter's projected edge vs today's starting pitcher & park, shown as a 4-quadrant pie (4 filled = best).">MATCHUP</span>
            {FSM_MATCHUP_ORDER.map((k) =>
            <span className="fsm-mkey" key={k} title={`${k} matchup — ${FSM_MATCHUP_DESC[k]}`}><i style={{ background: FSM_MATCHUP[k].color }} />{k}</span>
            )}
          </div>
        </div>
        {/* GAMES — jump straight to any game */}
        <label className="fsm-gamesel fsm-gamesel--inline">
          <span className="fsm-gamesel__label">GAMES</span>
          <span className="fsm-gamesel__field">
            <select value={selGame} onChange={(e) => setSelGame(e.target.value)}>
              <option value="all">All games · {FSM_GAMES.length}</option>
              {FSM_GAMES.map((g) =>
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
        <span className="fsm-pitchbar__lbl" title="Pitch Mix: when ON, each batter's rate & projection stats are recomputed against the specific pitcher they face today — that pitcher's pitch-type mix and throwing hand (platoon split). When OFF, you see full-season stats vs all pitchers.">PITCH MIX</span>
        <button className={"fsm-pmtoggle" + (pmOn ? " is-on" : "")} role="switch" aria-checked={pmOn} title="Toggle matchup-adjusted stats. ON = vs the pitcher faced (mix + hand). OFF = season stats vs all pitchers. Season totals like HR & PA never change." onClick={() => setPmOn((v) => !v)}>
          <span className="fsm-pmtoggle__track"><span className="fsm-pmtoggle__knob" /></span>
          <span className="fsm-pmtoggle__state">{pmOn ? "ON" : "OFF"}</span>
        </button>
        <span className="fsm-pitchbar__note">{pmOn ? "Stats reflect each batter vs the pitcher they're facing — pitch mix + throwing hand" : "Showing season stats vs all pitchers"}</span>
      </div>
      <div className="fsm-filters">
        <FsmRadioGroup label="PLAYER GROUP" value={group} onChange={setGroup} options={FSM_GROUP_OPTS} />
        <span className="fsm-filters__div" />
        <FsmRadioGroup label="FOCUS" value={focus} onChange={setFocus} options={FSM_FOCUS_OPTS} />
      </div>

      {/* GAME-NAV CHIPS — one-click jump to each game */}
      {view === "game" &&
      <div className="fsm-gamenav">
          <button className={selGame === "all" ? "is-on" : ""} onClick={() => setSelGame("all")}>ALL · {FSM_GAMES.length}</button>
          {FSM_GAMES.map((g) =>
        <button key={g.id} className={selGame === g.id ? "is-on" : ""} onClick={() => setSelGame(g.id)}>
              {g.away} @ {g.home}
            </button>
        )}
        </div>
      }

      {/* BODY */}
      {view === "player" ?
      <div className="fsm-tablewrap"><FsmTable rows={pool} cols={activeCols} showGame={true} onBatter={openBatter} onPitch={openPitch} onReorder={onReorder} onSort={onSort} sortState={sortState} /></div> :

      gamesToShow.map((game) => {
        const gameRows = pool.filter((r) => r.gameId === game.id);
        if (!gameRows.length) return null;
        return (
          <div className="fsm-gameblock" key={game.id} id={`fsm-game-${game.id}`}>
              <FsmGameHeader game={game} n={gameRows.length} />
              <div className="fsm-tablewrap"><FsmTable rows={gameRows} cols={activeCols} onBatter={openBatter} onPitch={openPitch} onReorder={onReorder} onSort={onSort} sortState={sortState} /></div>
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

      <FsmDetailModal modal={modal} onClose={() => setModal(null)} setModal={setModal} />
    </div>);

}

Object.assign(window, { FullSlateMatrix, FSM_TEAM_COLOR: TEAM_COLOR });