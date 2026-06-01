/* HR Engine — STRATEGY rail. Auto-cycles through a pool of ready-to-deploy
   player groups from the live slate (paused on hover). Player count (1-4) is
   user-selectable; headshots are real-photo drop slots keyed per player.
   Clicking a card sends that strategy's players to FanDuel. */

const STRATEGIES = [
  { id: "elite",  label: "ELITE SPOT",   icon: "crosshair", color: "#1aff66", tag: "Top HR Prop Edge",
    rank: (r) => r.hrprob },
  { id: "power",  label: "POWER STACK",  icon: "target", color: "#ffb020", tag: "Stack for Maximum Power",
    rank: (r) => (r.barrel || 0) * 1.6 + r.slg * 8 + (r.ev - 86) * 0.6 },
  { id: "value",  label: "VALUE SPOT",   icon: "star", color: "#3b6fff", tag: "High Value + Leverage Spot",
    rank: (r) => (["EDGE", "SIGNAL"].includes(r.tier) ? 100 : 0) + r.hrprob + (r.quality === "ELITE" || r.quality === "STRONG" ? 6 : 0) },
  { id: "park",   label: "PARK BOOST",   icon: "diamond", color: "#00d9ff", tag: "Hitter-Friendly Air Density",
    rank: (r) => { const g = (window.SLATE_GAMES || []).find((x) => x.teams.includes(r.teamAbbr)); return (g ? g.hrFactor : 1) * 12 + r.hrprob * 0.3; } },
  { id: "streak", label: "HOT STREAK",   icon: "trend", color: "#1aff66", tag: "Live Barrel + Exit-Velo Surge",
    rank: (r) => (r.barrel || 0) * 2 + (r.ev - 85) * 1.2 + (r.hh || 0) * 0.15 },
  { id: "lefty",  label: "PLATOON EDGE", icon: "bolt", color: "#ffb020", tag: "Platoon Split Advantage",
    rank: (r) => (r.bats === "L" ? 60 : r.bats === "S" ? 30 : 0) + r.hrprob } ,
];

function stratFanduelUrl(strat, players) {
  const q = players.map((p) => p.name.replace("…", "")).join(", ") + " home run";
  return "https://sportsbook.fanduel.com/search?query=" + encodeURIComponent(q);
}

const StratHead = ({ stratId, player }) => {
  const teamColor = (window.FSM_TEAM_COLOR || {})[player.teamAbbr] || "#3b6fff";
  const initials = player.name.replace("…", "").split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase();
  const last = player.name.replace("…", "").split(" ").slice(-1)[0];
  return (
    <div className="md-strat-head" style={{ "--team": teamColor }} title={player.name}>
      <image-slot id={`strat-${stratId}-${player.id}`} shape="circle" placeholder={initials}></image-slot>
      <span className="md-strat-head__name">{last}</span>
    </div>
  );
};

const StratCard = ({ strat, rows, count }) => {
  const players = rows.slice().sort((a, b) => strat.rank(b) - strat.rank(a)).slice(0, count);
  const avg = players.reduce((a, p) => a + p.hrprob, 0) / (players.length || 1);
  const score = Math.min(9.9, 6 + avg * 0.17).toFixed(1);
  const addFD = () => window.open(stratFanduelUrl(strat, players), "_blank", "noopener");
  return (
    <div
      className="md-qp__card"
      role="button"
      tabIndex={0}
      onClick={addFD}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); addFD(); } }}
      title={`Add ${strat.label} — ${players.map((p) => p.name).join(", ")} — to FanDuel`}
      style={{ "--qp-color": strat.color, "--qp-glow": `${strat.color}26` }}
    >
      <span className="md-qp__add" aria-hidden="true">+ FD</span>
      <div className="md-qp__row">
        <span className="md-qp__label"><Icon name={strat.icon} size={13} color="currentColor" strokeWidth={1.9} /> {strat.label}</span>
        <span className="md-qp__score">HR ENV SCORE <b>{score}</b></span>
      </div>
      <div className="md-qp__heads" style={{ gridTemplateColumns: `repeat(${count}, 1fr)` }} onClick={(e) => e.stopPropagation()}>
        {players.map((p) => <StratHead key={p.id} stratId={strat.id} player={p} />)}
      </div>
      <div className="md-qp__tag">{strat.tag}</div>
    </div>
  );
};

const StrategyRail = ({ onViewAll }) => {
  const [count, setCount] = React.useState(3);
  const [start, setStart] = React.useState(0);
  const pausedRef = React.useRef(false);
  const [dataVersion, setDataVersion] = React.useState(0);
  React.useEffect(() => {
    const handler = () => setDataVersion(v => v + 1);
    window.addEventListener("hrEngineDataLoaded", handler);
    return () => window.removeEventListener("hrEngineDataLoaded", handler);
  }, []);
  const rows = window.LEADERBOARD_ROWS || [];

  React.useEffect(() => {
    const id = setInterval(() => { if (!pausedRef.current) setStart((s) => (s + 1) % STRATEGIES.length); }, 4500);
    return () => clearInterval(id);
  }, []);

  const shown = [0, 1, 2].map((i) => STRATEGIES[(start + i) % STRATEGIES.length]);

  return (
    <div className="md-qp">
      <div className="md-qp__head" data-comment-anchor="db8433a23a-div-34-7">
        <span className="md-qp__title">Strategy</span>
        <span className="md-qp__live"><LiveDot size={7} /> LIVE</span>
      </div>
      <div className="md-qp__toprow">
        <label className="md-qp__count">
          <span className="md-qp__count-lbl">SUGGEST</span>
          <span className="md-qp__count-field">
            <select value={count} onChange={(e) => setCount(+e.target.value)}>
              {[1, 2, 3, 4].map((n) => <option key={n} value={n}>{n} player{n > 1 ? "s" : ""}</option>)}
            </select>
            <svg viewBox="0 0 24 24" width="13" height="13" aria-hidden="true"><path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </span>
        </label>
        <button className="md-qp__viewall" onClick={onViewAll}>VIEW ALL »</button>
      </div>
      <div
        className="md-qp__stack"
        onMouseEnter={() => { pausedRef.current = true; }}
        onMouseLeave={() => { pausedRef.current = false; }}
      >
        {shown.map((s, i) => <StratCard key={`${start}-${i}`} strat={s} rows={rows} count={count} />)}
      </div>
    </div>
  );
};

Object.assign(window, { StrategyRail, StratCard, StratHead });
