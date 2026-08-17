/* HR Engine — Live Targets banner (right→left marquee).
   States: mon (amber, in-game), hr (blue + lightning), dead (red, game over no HR). */

/* Jagged electric outline traced around the whole card edge (per-card filter). */
const EdgeBolt = ({ uid }) => {
  const fid = "eb-" + uid;
  const seed = (String(uid).split("").reduce((a, c) => a + c.charCodeAt(0), 0) % 9) + 1;
  return (
    <svg className="md-tgt__edge" viewBox="0 0 188 72" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <filter id={fid} x="-18%" y="-18%" width="136%" height="136%">
          <feTurbulence type="fractalNoise" baseFrequency="0.05 0.085" numOctaves="2" seed={seed} result="n">
            <animate attributeName="seed" values={`${seed};${seed + 3};${seed + 1};${seed + 5};${seed + 2};${seed + 4}`} dur="0.5s" repeatCount="indefinite" calcMode="discrete" />
          </feTurbulence>
          <feDisplacementMap in="SourceGraphic" in2="n" scale="6" xChannelSelector="R" yChannelSelector="G" />
        </filter>
      </defs>
      <rect x="3.5" y="3.5" width="181" height="65" rx="6" fill="none" stroke="currentColor" strokeWidth="1.5" filter={"url(#" + fid + ")"} />
      <rect x="3.5" y="3.5" width="181" height="65" rx="6" fill="none" stroke="currentColor" strokeWidth="0.6" opacity="0.5" filter={"url(#" + fid + ")"} />
      <rect className="md-tgt__arc" x="3.5" y="3.5" width="181" height="65" rx="6" fill="none" stroke="#eaf2ff" strokeWidth="1.4" filter={"url(#" + fid + ")"} />
    </svg>
  );
};

const TargetCard = ({ t, onPick, uid }) => {
  // Real game state comes from live-targets-live.js (Phase 2a), which
  // resolves each target to a game_pk and polls /api/live-state/{game_pk}.
  // "hr"/"dead" badges and the HR-count line stay mock-driven — that's the
  // batter-homered trigger, a separate signal not yet built (later phase).
  const [live, setLive] = React.useState(() => (window.LIVE_TARGETS_STATE || {})[t.id] || null);
  React.useEffect(() => {
    const handler = () => setLive((window.LIVE_TARGETS_STATE || {})[t.id] || null);
    window.addEventListener("liveTargetsStateUpdated", handler);
    return () => window.removeEventListener("liveTargetsStateUpdated", handler);
  }, [t.id]);

  // Real score when resolved; an honest placeholder (never the stale mock
  // number) when the card hasn't resolved to a real game yet.
  const scoreText = live && live.resolved && live.scoreLabel ? live.scoreLabel : "—";

  // build the two info lines based on state
  const cls = `md-tgt md-tgt--${t.state}`;
  const monStatus = t.state === "mon" && live && live.resolved ? live.status : null;
  const statusEl =
    t.state === "hr"        ? <span className="hr">HR</span> :
    t.state === "dead"      ? <span className="no">FINAL</span> :
    monStatus === "Live"    ? <span className="mon">LIVE</span> :
    monStatus === "Final"   ? <span className="no">FINAL</span> :
                               <span className="mon">PREGAME</span>;
  const line2 =
    t.state === "hr" ? (
      <span className="md-tgt__line">
        <span className="k">{t.inn}</span> | <span className="md-tgt__bolt">⚡</span>{" "}
        <span className="hr">HR</span> | <span className="hr">{t.hrs} HR</span>
      </span>
    ) : t.state === "dead" ? (
      <span className="md-tgt__line"><span className="no">NO HR</span> · GAME OVER</span>
    ) : monStatus === "Live" ? (
      <span className="md-tgt__line"><span className="k">{live.inningLabel || "—"}</span> | <span className="mon">MONITORING</span></span>
    ) : monStatus === "Final" ? (
      <span className="md-tgt__line"><span className="no">GAME OVER</span></span>
    ) : (
      <span className="md-tgt__line"><span className="k">PREGAME</span></span>
    );

  return (
    <button className={cls} onClick={() => onPick && onPick(t.id)}>
      {(t.state === "hr" || t.state === "dead") && <EdgeBolt uid={uid} />}
      <span className="md-tgt__name">{t.name}</span>
      <span className="md-tgt__line">
        <span className="k">{t.m}</span> | {statusEl} {scoreText}
      </span>
      {line2}
    </button>
  );
};

const LiveTargets = ({ targets, onPick }) => {
  // duplicate the list so the -50% loop is seamless
  const loop = [...targets, ...targets];
  return (
    <div className="md-banner">
      <div className="md-banner__rail">
        <div className="md-banner__dots"><span /><span /><span /></div>
        <div className="md-banner__label">HR ENGINE<br/>LIVE TARGETS</div>
      </div>
      <div className="md-marquee">
        <div className="md-marquee__track">
          {loop.map((t, i) => <TargetCard key={t.id + "-" + i} uid={t.id + "-" + i} t={t} onPick={onPick} />)}
        </div>
      </div>
    </div>
  );
};

Object.assign(window, { LiveTargets, TargetCard, EdgeBolt });
