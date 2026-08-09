// ============================================================
// BATTER DETAIL CARD  v1 · wired to /api/batter-detail
// Honesty layer: every field checks _meta.availability before
// rendering. Gap fields → "—". No fabricated values.
// ============================================================

const BATTER_DETAIL_CACHE = new Map();

function BatterDetailCard({ row, onClose, onPitch, builderMode = false }) {
  const [fetchState, setFetchState] = React.useState("idle");
  const [detail,     setDetail]     = React.useState(null);
  const [tf,         setTf]         = React.useState("full");
  const [matrix,     setMatrix]     = React.useState(true);
  const [lensId,     setLensId]     = React.useState("loud");
  const [tip,        setTip]        = React.useState(null);
  const [tpos,       setTpos]       = React.useState({x:0,y:0});

  const batterId    = row.id    != null ? row.id    : null;
  const pitcherId   = row.pitcher_id != null ? row.pitcher_id : null;
  const gamePk      = row.game_pk    != null ? row.game_pk    : null;
  const batterName  = row.name  || row.player || "—";
  const teamAbbr    = row.teamAbbr || row.team || "—";
  const pitcherName = row.pitcher_name || "TBD";
  const pitcherHand = row.pitcher_hand || "?";
  const batterSide  = row.bats  || row.batter_side || "R";

  React.useEffect(() => {
    if (!batterId) { setFetchState("error"); return; }
    const key = `${batterId}:${pitcherId}:${gamePk}`;
    if (BATTER_DETAIL_CACHE.has(key)) {
      setDetail(BATTER_DETAIL_CACHE.get(key));
      setFetchState("done");
      return;
    }
    setFetchState("loading");
    const p = new URLSearchParams();
    p.set("batter_id", batterId);
    if (pitcherId) p.set("pitcher_id", pitcherId);
    if (gamePk)    p.set("game_pk",    gamePk);
    const url = `https://mlb-hr-api.fly.dev/api/batter-detail?${p}`;
    const doFetch = (window.__hrAuth && typeof window.__hrAuth.authFetch === "function")
      ? (u) => window.__hrAuth.authFetch(u)
      : (u) => fetch(u);
    doFetch(url)
      .then(r => r.json())
      .then(data => { BATTER_DETAIL_CACHE.set(key, data); setDetail(data); setFetchState("done"); })
      .catch(() => setFetchState("error"));
  }, [batterId, pitcherId, gamePk]);

  // ── Honesty layer ──────────────────────────────────────────
  const isLive = (section, field) => {
    if (!section || !section._meta) return false;
    const av = section._meta.availability;
    if (!av) return false;
    if (av.all === "Live") return true;
    return av[field] === "Live";
  };
  const fv = (section, field, val, fmt) => {
    if (!isLive(section, field)) return "—";
    if (val == null) return "—";
    return fmt ? fmt(val) : String(val);
  };

  // ── Format helpers ─────────────────────────────────────────
  const pct  = n => n != null ? n.toFixed(1) + "%" : "—";
  const fmtD = n => n != null ? (n < 1 ? "." + String(Math.round(n * 1000)).padStart(3,"0") : n.toFixed(3)) : "—";

  // ── Tooltip helpers ────────────────────────────────────────
  const showTip = (e, t) => { if (!t) return; setTip(t); setTpos({x:e.clientX,y:e.clientY}); };
  const moveTip = (e) => setTpos({x:e.clientX,y:e.clientY});
  const hideTip = () => setTip(null);

  // ── Design tokens (canonical HR Engine palette) ────────────
  const T = {
    void:"#04070a", panel:"#0a1014", raised:"#0e1519",
    fg1:"#f4f8f6", fg2:"#c8d2cf", fg3:"#93a09b",
    bd:"rgba(180,220,200,.12)", bd2:"rgba(180,220,200,.2)",
    green:"#1aff66", green2:"#8fffb3", red:"#ff3344",
    cyan:"#00d9ff",  amber:"#ffb020",  blue:"#3b6fff",
    gg:"rgba(26,255,102,.55)",
  };
  const tierColor = t => ({elite:T.green,good:T.green2,mid:T.amber,low:T.red}[t] || T.fg1);

  // ── Sub-components (locally scoped) ───────────────────────
  const Eyebrow = ({children,style:s={}}) =>
    <div style={{fontFamily:"'Barlow Condensed'",fontWeight:600,textTransform:"uppercase",letterSpacing:".07em",color:T.fg2,fontSize:10.5,lineHeight:1.2,...s}}>{children}</div>;

  const Ttl = ({children,color=T.fg1,style:s={}}) =>
    <div style={{fontFamily:"'Barlow Condensed'",fontWeight:800,textTransform:"uppercase",letterSpacing:".05em",fontSize:13,color,...s}}>{children}</div>;

  const Mod = ({children,accent,style:s={}}) => (
    <div style={{
      position:"relative",
      background:accent==="p"?"linear-gradient(180deg,#0b1820,#0a1216)":"linear-gradient(180deg,#0f171c,#0c1216)",
      border:`1px solid ${accent==="g"?"rgba(26,255,102,.28)":accent==="p"?"rgba(0,217,255,.3)":T.bd}`,
      borderRadius:9,padding:12,display:"flex",flexDirection:"column",
      boxShadow:accent==="g"?"0 0 22px rgba(26,255,102,.09)":accent==="p"?"0 0 22px rgba(0,217,255,.08)":"none",...s}}>
      {children}
    </div>
  );

  const Tile = ({d}) => (
    <div onMouseEnter={d.tip?(e=>showTip(e,d.tip)):undefined} onMouseMove={d.tip?moveTip:undefined} onMouseLeave={d.tip?hideTip:undefined}
      style={{position:"relative",background:"linear-gradient(180deg,#0d151a,#0a1014)",
        border:`1px solid ${d.top?"rgba(26,255,102,.5)":T.bd}`,borderRadius:6,padding:10,
        display:"flex",flexDirection:"column",gap:4,cursor:d.tip?"help":"default",minWidth:0,
        boxShadow:d.top?"0 0 18px rgba(26,255,102,.14)":"none"}}>
      <div style={{fontFamily:"'Barlow Condensed'",fontWeight:600,textTransform:"uppercase",letterSpacing:".03em",fontSize:9.5,color:T.fg2,whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{d.k}</div>
      <div style={{fontSize:17,fontWeight:500,lineHeight:1,fontFamily:"'JetBrains Mono'",color:tierColor(d.tier||"mid")}}>{d.v}</div>
      <div style={{fontFamily:"'Barlow Condensed'",fontWeight:600,fontSize:8.5,letterSpacing:".03em",textTransform:"uppercase",color:tierColor(d.tier||"mid")}}>{d.p}</div>
    </div>
  );

  const Bar = ({label,val,pct:pctVal,tone="g",tip:t}) => (
    <div onMouseEnter={t?(e=>showTip(e,t)):undefined} onMouseMove={t?moveTip:undefined} onMouseLeave={t?hideTip:undefined}
      style={{display:"flex",alignItems:"center",gap:8,cursor:t?"help":"default"}}>
      <span style={{fontFamily:"'Barlow Condensed'",fontWeight:600,fontSize:10.5,textTransform:"uppercase",color:T.fg2,width:80,flexShrink:0}}>{label}</span>
      <span style={{height:5,background:"rgba(180,220,200,.12)",borderRadius:3,overflow:"hidden",flex:1}}>
        <span style={{display:"block",height:"100%",width:(pctVal||0)+"%",borderRadius:3,background:tone==="a"?T.amber:tone==="r"?T.red:tone==="c"?T.cyan:T.green}}/>
      </span>
      <span style={{fontFamily:"'JetBrains Mono'",fontSize:12,width:52,textAlign:"right",flexShrink:0,color:tone==="a"?T.amber:tone==="r"?T.red:T.fg1}}>{val}</span>
    </div>
  );

  const Pill = ({children,tone="go"}) => {
    const map={g:{c:"#04140a",b:T.green},go:{c:T.green,b:"rgba(26,255,102,.1)",bd:"rgba(26,255,102,.5)"},a:{c:"#1a1200",b:T.amber},r:{c:"#fff",b:T.red},c:{c:"#02141a",b:T.cyan},dim:{c:T.fg3,b:"rgba(180,220,200,.08)"}};
    const s=map[tone]||map.dim;
    return <span style={{display:"inline-flex",alignItems:"center",fontFamily:"'Barlow Condensed'",fontWeight:700,fontSize:9.5,letterSpacing:".08em",textTransform:"uppercase",padding:"3px 8px",borderRadius:999,lineHeight:1.4,whiteSpace:"nowrap",color:s.c,background:s.b,boxShadow:s.bd?`inset 0 0 0 1px ${s.bd}`:"none"}}>{children}</span>;
  };

  const Dot = ({d}) =>
    <span style={{width:7,height:7,borderRadius:"50%",flexShrink:0,background:d==="g"?T.green:d==="a"?T.amber:"transparent",boxShadow:d==="o"?`inset 0 0 0 1.5px ${T.fg3}`:d==="g"?`0 0 6px ${T.gg}`:"none"}}/>;

  const GrpHdr = ({label,accent="g"}) => (
    <div style={{display:"flex",alignItems:"center",gap:9,margin:"2px 0 -4px"}}>
      <span style={{fontFamily:"'Barlow Condensed'",fontWeight:800,fontSize:11,letterSpacing:".14em",textTransform:"uppercase",color:accent==="g"?T.fg3:T.cyan}}>◈ {label}</span>
      <span style={{height:1,flex:1,background:`linear-gradient(90deg,${accent==="g"?"rgba(180,220,200,.2)":"rgba(0,217,255,.4)"},transparent)`}}/>
    </div>
  );

  // ── Loading / Error ────────────────────────────────────────
  if (fetchState === "loading" || fetchState === "idle") {
    return (
      <div style={{width:"min(1300px,94vw)",background:T.void,borderRadius:12,border:`1px solid ${T.bd2}`,padding:48,display:"flex",flexDirection:"column",alignItems:"center",gap:12,minHeight:280,position:"relative"}}>
        <button onClick={onClose} style={{position:"absolute",top:12,right:12,background:"none",border:`1px solid ${T.bd}`,color:T.fg2,borderRadius:5,padding:"4px 10px",cursor:"pointer",fontSize:13}}>✕</button>
        <div style={{width:28,height:28,border:`3px solid rgba(26,255,102,.2)`,borderTop:`3px solid ${T.green}`,borderRadius:"50%",animation:"bdc-spin .8s linear infinite"}}/>
        <style>{`@keyframes bdc-spin{to{transform:rotate(360deg)}}`}</style>
        <Eyebrow style={{color:T.fg3}}>Loading batter profile…</Eyebrow>
      </div>
    );
  }
  if (fetchState === "error" || !detail) {
    return (
      <div style={{width:"min(1300px,94vw)",background:T.void,borderRadius:12,border:"1px solid rgba(255,51,68,.3)",padding:40,display:"flex",flexDirection:"column",alignItems:"center",gap:12,minHeight:200,position:"relative"}}>
        <button onClick={onClose} style={{position:"absolute",top:12,right:12,background:"none",border:`1px solid ${T.bd}`,color:T.fg2,borderRadius:5,padding:"4px 10px",cursor:"pointer",fontSize:13}}>✕</button>
        <Eyebrow style={{color:T.red}}>Failed to load batter detail</Eyebrow>
        <Eyebrow style={{color:T.fg3}}>Check API · batter_id {batterId}</Eyebrow>
      </div>
    );
  }

  // ── Extract payload sections ───────────────────────────────
  const threat     = detail.threat      || {};
  const sc         = detail.statcast    || {};
  const splits     = detail.splits      || {};
  const disc       = detail.discipline  || {};
  const environ    = detail.environment || {};
  const pitcher    = detail.pitcher     || {};
  const ars        = detail.arsenal     || {};
  const fatigue    = detail.fatigue     || {};
  const ppRows     = (detail.pitch_profile && Array.isArray(detail.pitch_profile.rows)) ? detail.pitch_profile.rows : [];
  const recentRaw  = detail.recent      || {};
  const metaBlock  = detail.meta        || {};
  const verdict    = detail.pitch_mix_verdict;
  const verdictMeta= detail.pitch_mix_verdict_meta || {};

  // Filter batter games: pa >= 1
  // TODO: exclude PH-only games when `started` field becomes available from MLB StatsAPI
  const batterGames   = Array.isArray(recentRaw.batter_games)
    ? recentRaw.batter_games.filter(g => (g.pa ?? 0) >= 1)
    : [];
  const pitcherStarts = Array.isArray(recentRaw.pitcher_starts) ? recentRaw.pitcher_starts : [];

  // ── Derived display values ─────────────────────────────────
  const hrProb    = fv(threat,"hrprob",   threat.hrprob,    n => n.toFixed(1)+"%");
  const tierLabel = fv(threat,"tier",     threat.tier);
  const projProb  = fv(threat,"hrprob_projected",threat.hrprob_projected,n=>n.toFixed(1)+"%");
  const seasPace  = fv(threat,"season_pace_hr",threat.season_pace_hr,n=>n+" HR");
  const rank      = fv(threat,"model_tier_rank",threat.model_tier_rank,n=>"#"+n);
  const headPid   = pitcher.pitcher_id || pitcherId;
  const headSrc   = headPid ? `https://midfield.mlbstatic.com/v1/people/${headPid}/spots/120` : null;
  const pitcherInit = pitcherName.replace("…","").split(" ").map(w=>w[0]||"").join("").slice(0,2).toUpperCase();

  // Pitch pill tone
  const pillTone = p => (!p||p==="—")?"dim":p==="EXPLOIT"?"g":p==="HUNT"?"a":p==="AVOID"?"r":"dim";

  // Verdict display
  const verdictLive = verdictMeta.availability === "Live";
  const verdictLabel= verdictLive && verdict ? verdict : "PENDING";
  const verdictTone = v => (!v||v==="PENDING")?"dim":v==="DEPLOY"?"g":v==="HUNT"?"a":v==="LEAN"?"go":v==="AVOID"?"r":"dim";

  const vulnLabel  = isLive(pitcher,"all") ? (pitcher.pitcherVuln || "—") : "—";
  const vulnTone   = vulnLabel==="TARGET"?"r":vulnLabel==="HIGH"?"a":"dim";
  const platLabel  = isLive(splits,"all")  ? (splits.handedness_edge_label || "—") : "—";
  const arsLabel   = isLive(ars,"all")     ? (ars.arsenal_edge_label || "—") : "—";
  const arsKeyPitch= isLive(ars,"all")     ? (ars.arsenal_edge_key_pitch || "—") : "—";

  // Statcast metric tiles
  const sc_tier = (v,hi,lo) => v==null?"mid":v>=hi?"elite":v>=lo?"good":"mid";
  const statTilesFull = [
    {k:"MAX EV",    v:fv(sc,"maxev",  sc.maxev,  n=>n.toFixed(1)), p:"mph",      tier:sc_tier(sc.maxev,115,108)},
    {k:"AVG EV",    v:fv(sc,"ev",     sc.ev,     n=>n.toFixed(1)), p:"mph",      tier:sc_tier(sc.ev,93,88)},
    {k:"HARD-HIT%", v:fv(sc,"hh",    sc.hh,     pct),             p:"≥95mph",   tier:sc_tier(sc.hh,50,38), top:sc.hh>=50},
    {k:"BARREL%",   v:fv(sc,"barrel",sc.barrel, pct),             p:"per PA", tier:sc_tier(sc.barrel,15,8), top:sc.barrel>=15},
    {k:"SWEET-SPOT",v:fv(sc,"sweet", sc.sweet,  pct),             p:"8–32°",    tier:sc_tier(sc.sweet,35,25)},
    {k:"LA AVG",    v:fv(sc,"la",    sc.la,     n=>n.toFixed(1)+"°"),p:"launch", tier:(sc.la>=18&&sc.la<=28)?"good":"mid"},
    {k:"PULL-AIR%", v:fv(sc,"pullair",sc.pullair,pct),            p:"all-BBE proxy",  tier:sc_tier(sc.pullair,20,12)},
    {k:"xSLG",      v:fv(sc,"xslg", sc.xslg,   fmtD),            p:"expected",  tier:sc_tier(sc.xslg,.600,.480)},
    {k:"xISO",      v:fv(sc,"xiso", sc.xiso,   fmtD),            p:"xpower",    tier:sc_tier(sc.xiso,.280,.200)},
    {k:"ISO",       v:fv(sc,"actual_iso",sc.actual_iso,fmtD),     p:"actual",    tier:sc_tier(sc.actual_iso,.250,.180)},
    {k:"wOBA",      v:fv(sc,"woba", sc.woba,   fmtD),             p:"weighted",  tier:sc_tier(sc.woba,.400,.320)},
    {k:"PACE",      v:seasPace,                                    p:"162g proj", tier:sc_tier(threat.season_pace_hr,40,28)},
  ];
  const statTilesHand = [
    {k:"SLG vRHP",  v:fv(splits,"actual_slg_vs_rhp",splits.actual_slg_vs_rhp,fmtD), p:"vs right", tier:sc_tier(splits.actual_slg_vs_rhp,.580,.450)},
    {k:"SLG vLHP",  v:fv(splits,"actual_slg_vs_lhp",splits.actual_slg_vs_lhp,fmtD), p:"vs left",  tier:sc_tier(splits.actual_slg_vs_lhp,.580,.450)},
    {k:"PLATOON",   v:isLive(splits,"all")?(splits.handedness_edge_label||"—"):"—",  p:"edge",     tier:"good"},
    {k:"PULL%",     v:fv(splits,"pull",  splits.pull,   pct), p:"pull dir",   tier:"mid"},
    {k:"CENTER%",   v:fv(splits,"center",splits.center, pct), p:"center",     tier:"mid"},
    {k:"OPPO%",     v:fv(splits,"oppo_pct",splits.oppo_pct,pct), p:"opposite",tier:"mid"},
    {k:"BB%",       v:fv(disc,"bbpct",  disc.bbpct,    pct), p:"walk rate",  tier:sc_tier(disc.bbpct,12,7)},
    {k:"SQ-UP%",    v:fv(disc,"squp",   disc.squp,     pct), p:"hard zone",  tier:sc_tier(disc.squp,35,22)},
    {k:"BARREL%",   v:fv(sc,"barrel",   sc.barrel,     pct), p:"per PA",   tier:sc_tier(sc.barrel,15,8)},
    {k:"xSLG",      v:fv(sc,"xslg",     sc.xslg,       fmtD),p:"expected",   tier:sc_tier(sc.xslg,.600,.480)},
    {k:"xISO",      v:fv(sc,"xiso",     sc.xiso,       fmtD),p:"xpower",     tier:sc_tier(sc.xiso,.280,.200)},
    {k:"PACE",      v:seasPace,                                p:"162g proj",  tier:sc_tier(threat.season_pace_hr,40,28)},
  ];

  // Edge-combo lenses
  const LENSES = [
    {id:"loud",    name:"LOUD CONTACT",   dot:"g", q:"Is the power real or empty?",
      live:true, stats:[
        ["BARREL%",   fv(sc,"barrel",sc.barrel,pct),     Math.min(100,(sc.barrel||0)*5)],
        ["MAX EV",    fv(sc,"maxev",sc.maxev,n=>n.toFixed(1)),Math.min(100,((sc.maxev||80)-80)*5)],
        ["HARD-HIT%", fv(sc,"hh",sc.hh,pct),             Math.min(100,(sc.hh||0)*2)],
        ["xSLG",      fv(sc,"xslg",sc.xslg,fmtD),        Math.min(100,(sc.xslg||0)*120)],
      ]},
    {id:"platoon", name:"PLATOON HAMMER", dot:"g", q:"Does the split favor him tonight?",
      live:isLive(splits,"all"), stats:[
        ["SLG vRHP",  fv(splits,"actual_slg_vs_rhp",splits.actual_slg_vs_rhp,fmtD), Math.min(100,(splits.actual_slg_vs_rhp||0)*100)],
        ["SLG vLHP",  fv(splits,"actual_slg_vs_lhp",splits.actual_slg_vs_lhp,fmtD), Math.min(100,(splits.actual_slg_vs_lhp||0)*100)],
        ["EDGE",      isLive(splits,"all")?(splits.handedness_edge_label||"—"):"—",  70],
      ]},
    {id:"lift",    name:"LIFT RECIPE",    dot:"g", q:"Is he built to lift it out tonight?",
      live:true, stats:[
        ["HH%",       fv(sc,"hh",sc.hh,pct),             Math.min(100,(sc.hh||0)*2)],
        ["PULL-AIR",  fv(sc,"pullair",sc.pullair,pct),    Math.min(100,(sc.pullair||0)*4)],
        ["LA°",       fv(sc,"la",sc.la,n=>n.toFixed(1)+"°"),Math.min(100,((sc.la||0)/30)*100)],
        ["SWEET",     fv(sc,"sweet",sc.sweet,pct),        Math.min(100,(sc.sweet||0)*2.5)],
      ]},
    {id:"arsenal", name:"ARSENAL EXPLOIT",dot:"a", q:"Does he crush what this guy throws?",
      live:ppRows.some(r=>!r.pill_thin_sample&&r.availability&&r.availability.pill==="Live"),
      stats:ppRows.filter(r=>!r.pill_thin_sample&&r.availability&&r.availability.pill==="Live").slice(0,4).map(r=>[r.pitch_type, r.pill||"—", Math.min(100,r.damage||0)])},
    {id:"whiff",   name:"WHIFF-VS-STUFF", dot:"a", q:"Does the pitcher's best pitch beat him?", live:false, pending:true},
    {id:"riser",   name:"QUIET RISER",    dot:"o", q:"Heating up beneath the results?",          live:false, pending:true},
    {id:"build",   name:"+ BUILD YOUR OWN",dot:"o",q:"Assemble your own stat cluster (coming soon).",live:false,pending:true},
  ];
  const lens = LENSES.find(l=>l.id===lensId) || LENSES[0];

  // Environment tiles
  const envTiles = [
    {k:"TEMP",  v:fv(environ,"temp",         environ.temp,         n=>n+"°"),         c:T.fg1},
    {k:"WIND",  v:fv(environ,"wind",         environ.wind,         String),            c:T.fg1},
    {k:"HUMID", v:fv(environ,"humidity_pct", environ.humidity_pct, n=>n+"%"),          c:T.fg1},
    {k:"PARK",  v:fv(environ,"park_factor",  environ.park_factor,  n=>n.toFixed(3)),   c:(environ.park_factor||1)>=1.05?T.green:T.fg1},
    {k:"HR×",   v:fv(environ,"hrFactor",     environ.hrFactor,     n=>n.toFixed(3)),   c:(environ.hrFactor||1)>=1.05?T.green:T.fg1},
    {k:"ENV",   v:fv(environ,"hr_environment_0_10",environ.hr_environment_0_10,n=>n.toFixed(1)+"/10"), c:(environ.hr_environment_0_10||0)>=6?T.green:T.fg1},
  ];

  // Verdict grid
  const verdictItems = [
    {k:"ARSENAL", v:arsLabel,    tone:arsLabel==="MISMATCH"||arsLabel==="EXPLOIT"?"go":"dim"},
    {k:"PLATOON", v:platLabel,   tone:platLabel.includes("EDGE")?"go":"dim"},
    {k:"PITCHER", v:vulnLabel,   tone:vulnTone},
    {k:"VERDICT", v:verdictLabel,tone:verdictTone(verdictLabel)},
  ];

  // ── Main render ────────────────────────────────────────────
  return (
    <div style={{width:"min(1380px,96vw)",background:T.void,borderRadius:13,border:`1px solid ${T.bd2}`,padding:14,display:"flex",flexDirection:"column",gap:12,boxShadow:"0 60px 130px -40px #000",maxHeight:"92vh",overflowY:"auto",fontFamily:"'Barlow',system-ui,sans-serif"}}>

      {/* Global tooltip */}
      {tip && (
        <div style={{position:"fixed",zIndex:9999,maxWidth:280,left:Math.min(tpos.x+14,window.innerWidth-300),top:tpos.y+14,background:"#0a141a",border:`1px solid ${T.cyan}`,borderRadius:8,padding:"11px 13px",boxShadow:"0 20px 50px -12px #000,0 0 20px rgba(0,217,255,.2)",fontSize:12,color:T.fg1,lineHeight:1.45,pointerEvents:"none"}}>
          <b style={{fontFamily:"'Barlow Condensed'",fontWeight:800,textTransform:"uppercase",letterSpacing:".05em",color:T.cyan,fontSize:12,display:"block",marginBottom:4}}>{tip[0]}</b>
          {tip[1]}
          {tip[2] && <div style={{marginTop:6,fontFamily:"'JetBrains Mono'",fontSize:10.5,color:T.green2}}>◆ {tip[2]}</div>}
          {tip[3] && <div style={{marginTop:5,fontSize:10.5,color:T.fg2,fontStyle:"italic"}}>⚙ {tip[3]}</div>}
        </div>
      )}

      {/* ── IDENTITY BAR ─────────────────────────────────── */}
      <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",gap:16,padding:"12px 16px",borderRadius:10,background:`linear-gradient(115deg,rgba(0,90,180,.2),rgba(10,16,20,.4) 46%,rgba(10,16,20,.6)),${T.panel}`,border:`1px solid ${T.bd2}`}}>
        <div style={{display:"flex",alignItems:"center",gap:12}}>
          <div style={{fontFamily:"'Barlow Condensed'",fontWeight:800,fontSize:42,lineHeight:.8,color:T.blue,textShadow:"0 0 26px rgba(59,111,255,.6)"}}>{row.jersey || "—"}</div>
          <div>
            <div style={{display:"flex",alignItems:"center",gap:10,flexWrap:"wrap"}}>
              <div style={{fontFamily:"'Barlow Condensed'",fontWeight:800,fontSize:30,lineHeight:.9}}>{batterName.toUpperCase()}</div>
              <div style={{fontFamily:"'Barlow Condensed'",fontWeight:800,fontSize:15,border:`1.5px solid ${T.bd2}`,borderRadius:6,padding:"4px 8px",lineHeight:1}}>{teamAbbr}</div>
              <Pill tone={tierLabel==="APEX"?"g":tierLabel==="HIGH"?"go":tierLabel==="WATCH"?"a":"dim"}>{tierLabel}</Pill>
            </div>
            <div style={{fontFamily:"'Barlow Condensed'",fontWeight:600,fontSize:11.5,letterSpacing:".03em",textTransform:"uppercase",color:T.fg2,display:"flex",gap:8,flexWrap:"wrap",marginTop:5}}>
              <span>{row.position||row.pos||"—"}</span>
              <span style={{color:T.fg3,opacity:.5}}>/</span>
              <span>BATS <b style={{color:T.cyan}}>{batterSide}</b></span>
              <span style={{color:T.fg3,opacity:.5}}>/</span>
              <span>vs <b style={{color:pitcherHand==="L"?T.red:T.fg1}}>{pitcherHand}HP</b></span>
              <span style={{color:T.fg3,opacity:.5}}>/</span>
              <span>HR PROB <b style={{color:T.green}}>{hrProb}</b></span>
              <span style={{color:T.fg3,opacity:.5}}>/</span>
              <span>RANK <b style={{color:T.green}}>{rank}</b></span>
            </div>
          </div>
        </div>
        <div style={{display:"flex",alignItems:"center",gap:8}}>
          {builderMode && <Pill tone="a">BUILDER</Pill>}
          <button onClick={onClose} style={{background:"none",border:`1px solid ${T.bd2}`,color:T.fg2,borderRadius:6,padding:"6px 12px",cursor:"pointer",fontSize:12,fontFamily:"'Barlow Condensed'",fontWeight:700,letterSpacing:".05em",textTransform:"uppercase"}}>✕ CLOSE</button>
        </div>
      </div>

      {/* ── CONTROL BAR ──────────────────────────────────── */}
      <div style={{display:"flex",gap:16,alignItems:"flex-start",flexWrap:"wrap",padding:"10px 14px",borderRadius:10,background:`linear-gradient(180deg,rgba(19,27,33,.8),${T.raised})`,border:`1px solid ${T.bd2}`}}>
        <div style={{display:"flex",flexDirection:"column",gap:6}}>
          <div style={{fontFamily:"'Barlow Condensed'",fontWeight:700,fontSize:10,letterSpacing:".12em",textTransform:"uppercase",color:T.cyan}}>① TIMEFRAME</div>
          <div style={{display:"inline-flex",background:T.void,border:`1px solid ${T.bd}`,borderRadius:7,padding:3,gap:3}}>
            {[["full","FULL YEAR"],["platoon","VS HAND"]].map(([id,lbl]) => (
              <button key={id} onClick={()=>setTf(id)} style={{fontFamily:"'Barlow Condensed'",fontWeight:700,fontSize:11,textTransform:"uppercase",color:tf===id?"#04140a":T.fg2,background:tf===id?T.green:"transparent",border:0,padding:"6px 11px",borderRadius:5,cursor:"pointer",lineHeight:1}}>{lbl}</button>
            ))}
          </div>
        </div>
        <div style={{display:"flex",flexDirection:"column",gap:6}}>
          <div style={{fontFamily:"'Barlow Condensed'",fontWeight:700,fontSize:10,letterSpacing:".12em",textTransform:"uppercase",color:T.cyan}}>② PITCH MATRIX</div>
          <button onClick={()=>setMatrix(!matrix)} style={{display:"inline-flex",alignItems:"center",gap:8,background:T.void,border:`1px solid ${matrix?"rgba(0,217,255,.5)":T.bd}`,borderRadius:999,padding:"5px 11px 5px 6px",cursor:"pointer",color:matrix?T.cyan:T.fg2,fontFamily:"'Barlow Condensed'",fontWeight:700,fontSize:11,textTransform:"uppercase",lineHeight:1}}>
            <span style={{width:28,height:15,borderRadius:999,background:matrix?"rgba(0,217,255,.35)":"rgba(180,220,200,.18)",position:"relative",transition:".2s",flexShrink:0}}>
              <span style={{position:"absolute",top:1.5,left:matrix?14:2,width:12,height:12,borderRadius:"50%",background:matrix?T.cyan:T.fg2,transition:".2s",boxShadow:matrix?`0 0 8px ${T.cyan}`:"none"}}/>
            </span>{matrix?"ON":"OFF"}
          </button>
        </div>
        <div style={{display:"flex",flexDirection:"column",gap:6,flex:1,minWidth:300}}>
          <div style={{fontFamily:"'Barlow Condensed'",fontWeight:700,fontSize:10,letterSpacing:".12em",textTransform:"uppercase",color:T.cyan}}>③ EDGE-COMBO LENS <span style={{color:T.fg3}}>· ● LIVE ◐ SOON ○ COMING</span></div>
          <div style={{display:"flex",flexWrap:"wrap",gap:5}}>
            {LENSES.map(l => {
              const active = lensId===l.id;
              return (
                <button key={l.id} onClick={()=>setLensId(l.id)} style={{display:"inline-flex",alignItems:"center",gap:5,background:active?T.green:T.void,border:`1px solid ${active?"transparent":T.bd}`,borderRadius:6,padding:"5px 9px",cursor:"pointer",color:active?"#04140a":T.fg2,fontFamily:"'Barlow Condensed'",fontWeight:700,fontSize:10.5,textTransform:"uppercase",whiteSpace:"nowrap",lineHeight:1}}>
                  <span style={{width:7,height:7,borderRadius:"50%",flexShrink:0,background:active?"#04140a":(l.dot==="g"?T.green:l.dot==="a"?T.amber:"transparent"),boxShadow:l.dot==="o"&&!active?`inset 0 0 0 1.5px ${T.fg3}`:"none"}}/>
                  {l.name}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── GROUP 1: THE HITTER ──────────────────────────── */}
      <GrpHdr label="THE HITTER · POWER PROFILE" accent="g" />

      <div style={{display:"grid",gridTemplateColumns:"260px 1fr 280px",gap:12,alignItems:"stretch"}}>

        {/* HR THREAT */}
        <Mod accent="g">
          <div style={{display:"flex",alignItems:"center",gap:7,marginBottom:10}}><Dot d="g"/><Ttl color={T.green}>HR THREAT</Ttl></div>
          <div style={{display:"flex",flexDirection:"column",alignItems:"center",gap:6}}>
            <div style={{position:"relative",width:108,height:122,display:"grid",placeItems:"center"}}>
              <div style={{position:"absolute",inset:0,clipPath:"polygon(50% 0,100% 21%,100% 66%,50% 100%,0 66%,0 21%)",background:`linear-gradient(180deg,${T.green},#0c9c3f)`}}/>
              <div style={{position:"absolute",inset:3,clipPath:"polygon(50% 0,100% 21%,100% 66%,50% 100%,0 66%,0 21%)",background:"radial-gradient(120% 90% at 50% 20%,#103019,#06120b 74%)"}}/>
              <div style={{position:"relative",zIndex:2,display:"flex",flexDirection:"column",alignItems:"center"}}>
                <div style={{fontFamily:"'Barlow Condensed'",fontWeight:800,fontSize:44,lineHeight:.8,color:T.green,textShadow:`0 0 18px ${T.gg}`}}>{isLive(threat,"hrprob")&&threat.hrprob!=null?threat.hrprob.toFixed(0):"—"}</div>
                <div style={{fontFamily:"'Barlow Condensed'",fontWeight:700,fontSize:11,letterSpacing:".18em",color:T.fg1}}>{tierLabel}</div>
              </div>
            </div>
            {isLive(threat,"hrprob") && <span style={{fontFamily:"'Barlow Condensed'",fontWeight:700,fontSize:10,letterSpacing:".06em",color:T.green,background:"rgba(26,255,102,.1)",border:"1px solid rgba(26,255,102,.4)",borderRadius:999,padding:"3px 9px"}}>RANK {rank} · SLATE</span>}
          </div>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8,marginTop:10}}>
            <Tile d={{k:"HR PROB",   v:hrProb,   p:"tonight",  tier:"elite",  tip:["HR Probability","Model probability of a HR tonight.","Calibrated Poisson"]}} />
            <Tile d={{k:"PROJ",      v:projProb, p:"w/factors",tier:"good",   tip:["HR Prob Projected","Including park + weather multipliers.","Display only"]}} />
            <Tile d={{k:"PACE",      v:seasPace, p:"162g proj",tier:sc_tier(threat.season_pace_hr,40,28)}} />
            <Tile d={{k:"ENV SCORE", v:fv(environ,"hr_environment_0_10",environ.hr_environment_0_10,n=>n.toFixed(1)+"/10"),p:"0–10",tier:(environ.hr_environment_0_10||0)>=7?"elite":"mid"}} />
          </div>
        </Mod>

        {/* POWER · CONTACT METRICS */}
        <Mod>
          <div style={{display:"flex",alignItems:"center",gap:7,marginBottom:10}}>
            <Ttl>POWER · CONTACT METRICS</Ttl>
            <Pill tone={tf==="full"?"go":"c"}>{tf==="full"?"FULL SEASON":"VS HAND"}</Pill>
          </div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:8}}>
            {(tf==="full"?statTilesFull:statTilesHand).map((d,i)=><Tile key={i} d={d}/>)}
          </div>
        </Mod>

        {/* EDGE-COMBO LENS */}
        <Mod accent="g">
          <div style={{display:"flex",alignItems:"center",gap:7,marginBottom:6}}><Dot d="g"/><Ttl color={T.green}>LENS · {lens.name}</Ttl></div>
          <Eyebrow style={{color:T.fg3,marginBottom:9}}>{lens.q}</Eyebrow>
          {(lens.pending || !lens.live || !lens.stats || lens.stats.length===0) ? (
            <div style={{flex:1,display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",gap:8,padding:20,border:"1px dashed rgba(255,176,32,.4)",borderRadius:8,background:"rgba(255,176,32,.04)"}}>
              <div style={{fontFamily:"'Barlow Condensed'",fontWeight:800,fontSize:13,color:T.amber,letterSpacing:".1em"}}>PENDING</div>
              <Eyebrow style={{color:T.fg3}}>No fabricated values — coming soon</Eyebrow>
            </div>
          ) : (
            <>
              <div style={{display:"grid",gridTemplateColumns:`repeat(${Math.min(lens.stats.length,4)},1fr)`,gap:8,flex:1}}>
                {lens.stats.map((s,i) => (
                  <div key={i} style={{background:"linear-gradient(180deg,#0d151a,#0a1014)",border:`1px solid ${T.bd}`,borderRadius:6,padding:10,display:"flex",flexDirection:"column",gap:6}}>
                    <div style={{fontFamily:"'Barlow Condensed'",fontWeight:600,fontSize:9,textTransform:"uppercase",color:T.fg2,whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{s[0]}</div>
                    <div style={{fontSize:15,fontFamily:"'JetBrains Mono'",color:T.green2,lineHeight:1}}>{s[1]}</div>
                    <span style={{height:4,background:"rgba(180,220,200,.12)",borderRadius:2,overflow:"hidden"}}><span style={{display:"block",height:"100%",width:Math.min(100,s[2]||0)+"%",background:T.green,borderRadius:2}}/></span>
                  </div>
                ))}
              </div>
              <div style={{marginTop:9,padding:"7px 10px",background:"rgba(26,255,102,.08)",border:"1px solid rgba(26,255,102,.4)",borderRadius:6}}>
                <Eyebrow style={{color:T.green}}>SIGNAL CONFIRMED · {lens.name}</Eyebrow>
              </div>
            </>
          )}
        </Mod>
      </div>

      {/* SPLITS · PITCH DESTRUCTION · DISCIPLINE */}
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:12}}>

        {/* SPLITS · HANDEDNESS */}
        <Mod>
          <div style={{display:"flex",alignItems:"center",gap:7,marginBottom:10}}><Ttl>SPLITS · HANDEDNESS</Ttl></div>
          <div style={{display:"flex",flexDirection:"column",gap:8,flex:1,justifyContent:"center"}}>
            <Bar label="SLG vRHP" val={fv(splits,"actual_slg_vs_rhp",splits.actual_slg_vs_rhp,fmtD)} pct={Math.min(100,(splits.actual_slg_vs_rhp||0)*120)} />
            <Bar label="SLG vLHP" val={fv(splits,"actual_slg_vs_lhp",splits.actual_slg_vs_lhp,fmtD)} pct={Math.min(100,(splits.actual_slg_vs_lhp||0)*120)} tone={pitcherHand==="L"?"a":"g"}/>
            <Bar label="PULL%"    val={fv(splits,"pull",splits.pull,pct)}       pct={splits.pull||0} />
            <Bar label="CENTER%"  val={fv(splits,"center",splits.center,pct)}   pct={splits.center||0} tone="c"/>
            <Bar label="OPPO%"    val={fv(splits,"oppo_pct",splits.oppo_pct,pct)} pct={splits.oppo_pct||0} tone="a"/>
            <Bar label="BB%"      val={fv(disc,"bbpct",disc.bbpct,pct)}         pct={Math.min(100,(disc.bbpct||0)*5)} tip={["Walk %","Higher = more disciplined plate appearances.","Elite ≥12%"]}/>
            {isLive(splits,"all") && splits.handedness_edge_label && (
              <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"5px 8px",background:"rgba(0,217,255,.06)",border:"1px solid rgba(0,217,255,.3)",borderRadius:5}}>
                <Eyebrow>PLATOON</Eyebrow><Pill tone="c">{splits.handedness_edge_label}</Pill>
              </div>
            )}
          </div>
        </Mod>

        {/* PITCH TYPE DESTRUCTION */}
        <Mod>
          <div style={{display:"flex",alignItems:"center",gap:7,marginBottom:10}}>
            <Ttl>PITCH TYPE DESTRUCTION</Ttl>
            {matrix && <span style={{marginLeft:"auto"}}><Pill tone="c">MATRIX</Pill></span>}
          </div>
          <div style={{display:"flex",flexDirection:"column",gap:7,flex:1,justifyContent:"center"}}>
            {ppRows.length===0
              ? <Eyebrow style={{color:T.fg3}}>No pitch data</Eyebrow>
              : ppRows.slice(0,6).map((r,i) => {
                  const avail = r.availability || {};
                  const xw    = avail.xwoba==="Live" && r.xwoba!=null ? r.xwoba.toFixed(3) : "—";
                  const pill  = !r.pill_thin_sample && avail.pill==="Live" ? (r.pill||"—") : "—";
                  const barPct= !r.pill_thin_sample && avail.damage==="Live" ? Math.min(100,r.damage||0) : 0;
                  const tone  = pill==="EXPLOIT"?"g":pill==="HUNT"?"a":pill==="AVOID"?"r":"dim";
                  return (
                    <div key={i} style={{display:"flex",alignItems:"center",gap:8}}>
                      <span style={{fontFamily:"'Barlow Condensed'",fontWeight:700,fontSize:10.5,color:T.fg2,width:38,flexShrink:0,textTransform:"uppercase"}}>{r.pitch_type}</span>
                      <span style={{height:5,background:"rgba(180,220,200,.12)",borderRadius:3,overflow:"hidden",flex:1}}>
                        <span style={{display:"block",height:"100%",width:barPct+"%",borderRadius:3,background:tone==="g"?T.green:tone==="a"?T.amber:tone==="r"?T.red:"rgba(180,220,200,.2)"}}/>
                      </span>
                      <span style={{fontFamily:"'JetBrains Mono'",fontSize:11,width:42,textAlign:"right",flexShrink:0,color:T.fg1}}>{xw}</span>
                      <Pill tone={pillTone(pill)}>{pill}</Pill>
                    </div>
                  );
                })
            }
          </div>
        </Mod>

        {/* PLATE DISCIPLINE */}
        <Mod>
          <div style={{display:"flex",alignItems:"center",gap:7,marginBottom:10}}><Ttl>PLATE DISCIPLINE</Ttl></div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(2,1fr)",gap:8}}>
            <Tile d={{k:"BB%",    v:fv(disc,"bbpct",disc.bbpct,pct),p:"walk rate",tier:sc_tier(disc.bbpct,12,7), tip:["Walk %","Higher = more patient at the plate.","Elite ≥12%","Current payload"]}}/>
            <Tile d={{k:"SQ-UP%",v:fv(disc,"squp", disc.squp, pct), p:"hard zone",tier:sc_tier(disc.squp,35,22),tip:["Squad Up %","Hard contact in the zone.","Good ≥35%","Current payload"]}}/>
            <Tile d={{k:"K%",    v:"—",                             p:"gap",      tier:"mid",tip:["Strikeout %","Not in current payload · Gap","—"]}}/>
            <Tile d={{k:"WHIFF%",v:"—",                             p:"gap",      tier:"mid",tip:["Whiff %","Not in current payload · Gap","—"]}}/>
            <Tile d={{k:"CHASE%",v:"—",                             p:"gap",      tier:"mid",tip:["Chase %","Not in current payload · Gap","—"]}}/>
            <Tile d={{k:"Z-CONT",v:"—",                             p:"gap",      tier:"mid",tip:["Zone Contact %","Not in current payload · Gap","—"]}}/>
          </div>
        </Mod>
      </div>

      {/* ── GROUP 2: TONIGHT'S MATCHUP ───────────────────── */}
      <GrpHdr label="TONIGHT'S MATCHUP · PITCHER · ENVIRONMENT · VERDICT" accent="p" />

      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr 1fr",gap:12}}>

        {/* UP NEXT · PITCHER */}
        <Mod accent="p">
          <div style={{display:"flex",alignItems:"center",gap:7,marginBottom:10}}>
            <Ttl color={T.cyan}>UP NEXT · PITCHER</Ttl>
            <span style={{marginLeft:"auto"}}><Pill tone={vulnTone}>{vulnLabel}</Pill></span>
          </div>
          <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:10}}>
            {headSrc
              ? <img alt={pitcherName} src={headSrc}
                  style={{width:52,height:52,borderRadius:8,objectFit:"cover",objectPosition:"top",border:`1.5px solid ${T.cyan}`,flexShrink:0}}
                  onError={e=>{e.target.style.display="none";e.target.insertAdjacentHTML("afterend",`<div style="width:52px;height:52px;border-radius:8px;display:grid;place-items:center;font-family:'Barlow Condensed';font-weight:800;font-size:13px;border:1.5px solid ${T.cyan};color:${T.cyan};background:rgba(0,217,255,.06);flex-shrink:0">${pitcherInit}</div>`);}}/>
              : <div style={{width:52,height:52,borderRadius:8,display:"grid",placeItems:"center",fontFamily:"'Barlow Condensed'",fontWeight:800,fontSize:13,border:`1.5px solid ${T.cyan}`,color:T.cyan,background:"rgba(0,217,255,.06)",flexShrink:0}}>{pitcherInit}</div>
            }
            <div style={{flex:1,minWidth:0}}>
              <div style={{fontFamily:"'Barlow Condensed'",fontWeight:800,fontSize:14,lineHeight:1.1,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{pitcherName.toUpperCase()}</div>
              <Eyebrow style={{marginTop:3}}>
                <b style={{color:pitcherHand==="L"?T.red:T.fg1}}>{pitcherHand}HP</b>
                {" · REST "}
                {isLive(fatigue,"all")?fatigue.pitcher_days_rest+"D":"—"}
                {" · HR/9 "}
                {fv(pitcher,"all",pitcher.pitcher_hr9,n=>n.toFixed(2))}
              </Eyebrow>
            </div>
          </div>
          <Eyebrow style={{color:T.fg3,marginBottom:6}}>ARSENAL · {arsKeyPitch} · {arsLabel} (score {isLive(ars,"all")?ars.arsenal_edge_score?.toFixed(1)||"—":"—"})</Eyebrow>
          <div style={{display:"flex",flexDirection:"column",gap:6,flex:1}}>
            {ppRows.slice(0,4).map((r,i) => {
              const avail = r.availability || {};
              const pill  = !r.pill_thin_sample && avail.pill==="Live" ? (r.pill||"NEUT") : "—";
              const barPct= !r.pill_thin_sample && avail.damage==="Live" ? Math.min(100,r.damage||0) : 0;
              const tone  = pill==="EXPLOIT"?"g":pill==="HUNT"?"a":pill==="AVOID"?"r":"dim";
              return <Bar key={i} label={r.pitch_type} val={pill} pct={barPct} tone={tone}/>;
            })}
          </div>
        </Mod>

        {/* HEAD-TO-HEAD (not in batter-detail payload) */}
        <Mod accent="p">
          <div style={{display:"flex",alignItems:"center",gap:7,marginBottom:10}}><Ttl color={T.cyan}>HEAD-TO-HEAD</Ttl><Eyebrow style={{marginLeft:"auto",color:T.fg3}}>CAREER</Eyebrow></div>
          <div style={{flex:1,display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",gap:8,padding:20,border:"1px dashed rgba(0,217,255,.25)",borderRadius:8,background:"rgba(0,217,255,.03)"}}>
            <div style={{fontFamily:"'Barlow Condensed'",fontWeight:800,fontSize:13,color:T.cyan,letterSpacing:".1em"}}>PENDING</div>
            <Eyebrow style={{color:T.fg3,textAlign:"center"}}>Career H2H not in current payload</Eyebrow>
          </div>
        </Mod>

        {/* HR ENVIRONMENT */}
        <Mod accent="p" style={{padding:0,overflow:"hidden"}}>
          <div style={{position:"relative",height:88}}>
            <div style={{width:"100%",height:"100%",background:"linear-gradient(120deg,#0a1a24,#0e2a1a)"}}/>
            <div style={{position:"absolute",inset:0,padding:"8px 11px",display:"flex",flexDirection:"column",justifyContent:"flex-end",background:"linear-gradient(180deg,transparent,rgba(4,7,10,.92))"}}>
              <div style={{display:"flex",alignItems:"baseline",gap:6}}>
                <div style={{fontFamily:"'Barlow Condensed'",fontWeight:800,fontSize:28,color:T.green,textShadow:`0 0 10px ${T.gg}`}}>{fv(environ,"hr_environment_0_10",environ.hr_environment_0_10,n=>n.toFixed(1))}</div>
                <div style={{color:T.fg2,fontSize:11,fontFamily:"'Barlow Condensed'",fontWeight:700}}>/10 · HR ENVIRONMENT</div>
              </div>
              <Eyebrow style={{color:T.fg1,fontSize:9}}>PARK {fv(environ,"park_factor",environ.park_factor,n=>n.toFixed(3))} · HR× {fv(environ,"hrFactor",environ.hrFactor,n=>n.toFixed(3))}</Eyebrow>
            </div>
          </div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:5,padding:10}}>
            {envTiles.map((et,i) => (
              <div key={i} style={{background:T.void,border:`1px solid ${T.bd}`,borderRadius:5,padding:"5px 6px",display:"flex",flexDirection:"column",gap:2,alignItems:"center"}}>
                <Eyebrow style={{fontSize:9}}>{et.k}</Eyebrow>
                <div style={{fontSize:12,fontFamily:"'JetBrains Mono'",color:et.c}}>{et.v}</div>
              </div>
            ))}
          </div>
        </Mod>

        {/* MATCHUP VERDICT */}
        <Mod accent="g">
          <div style={{display:"flex",alignItems:"center",gap:7,marginBottom:10}}><Dot d="g"/><Ttl color={T.green}>MATCHUP VERDICT</Ttl></div>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:6,marginBottom:10}}>
            {verdictItems.map((vi,i) => (
              <div key={i} style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"6px 8px",background:T.void,border:`1px solid ${T.bd}`,borderRadius:5}}>
                <Eyebrow>{vi.k}</Eyebrow><Pill tone={vi.tone}>{vi.v}</Pill>
              </div>
            ))}
          </div>
          <div style={{marginTop:"auto",padding:"10px 12px",background:"rgba(26,255,102,.12)",border:"1px solid rgba(26,255,102,.5)",borderRadius:8,display:"flex",alignItems:"center",justifyContent:"space-between"}}>
            <Ttl color={T.green} style={{fontSize:13}}>OVERALL LEAN</Ttl>
            <Pill tone={verdictTone(verdictLabel)}>{verdictLabel}</Pill>
          </div>
        </Mod>
      </div>

      {/* RECENT FORM */}
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>

        {/* BATTER: LAST 5 APPEARANCES */}
        <Mod>
          <div style={{display:"flex",alignItems:"center",gap:7,marginBottom:10}}><Ttl>RECENT FORM · LAST 5 APPEARANCES</Ttl><Eyebrow style={{marginLeft:"auto",color:T.fg3}}>≥1 PA ONLY</Eyebrow></div>
          {recentRaw._meta?.availability?.batter_games === "Live"
            ? batterGames.length===0
              ? <Eyebrow style={{color:T.fg3}}>No games with ≥1 PA found</Eyebrow>
              : <div style={{display:"flex",flexDirection:"column",gap:6}}>
                  {batterGames.slice(0,5).map((g,i) => (
                    <div key={i} style={{display:"flex",alignItems:"center",gap:8,padding:"7px 10px",background:"rgba(180,220,200,.04)",border:`1px solid ${T.bd}`,borderRadius:6}}>
                      <span style={{fontFamily:"'Barlow Condensed'",fontWeight:700,fontSize:10.5,color:T.fg3,width:70,flexShrink:0}}>{g.date}</span>
                      <span style={{fontFamily:"'JetBrains Mono'",fontSize:11,color:T.fg1,width:32,flexShrink:0}}>{g.pa}PA</span>
                      <span style={{fontFamily:"'Barlow Condensed'",fontWeight:700,fontSize:10.5,color:T.fg2,flex:1}}>AVG {g.avg!=null?g.avg.toFixed(3):"—"} · SLG {g.slg!=null?g.slg.toFixed(3):"—"}</span>
                      {g.hr>0 && <span style={{fontFamily:"'Barlow Condensed'",fontWeight:800,fontSize:10.5,color:T.green,background:"rgba(26,255,102,.12)",border:"1px solid rgba(26,255,102,.4)",borderRadius:4,padding:"2px 7px"}}>⚡ {g.hr} HR</span>}
                    </div>
                  ))}
                </div>
            : <div style={{padding:20,border:"1px dashed rgba(255,176,32,.4)",borderRadius:8,background:"rgba(255,176,32,.04)",textAlign:"center"}}><Eyebrow style={{color:T.amber}}>DATA PENDING</Eyebrow></div>
          }
        </Mod>

        {/* PITCHER: LAST 5 STARTS */}
        <Mod>
          <div style={{display:"flex",alignItems:"center",gap:7,marginBottom:10}}><Ttl>PITCHER · LAST 5 STARTS</Ttl></div>
          {recentRaw._meta?.availability?.pitcher_starts === "Live"
            ? pitcherStarts.length===0
              ? <Eyebrow style={{color:T.fg3}}>No starts found</Eyebrow>
              : <div style={{display:"flex",flexDirection:"column",gap:6}}>
                  {pitcherStarts.slice(0,5).map((g,i) => (
                    <div key={i} style={{display:"flex",alignItems:"center",gap:8,padding:"7px 10px",background:"rgba(180,220,200,.04)",border:`1px solid ${T.bd}`,borderRadius:6}}>
                      <span style={{fontFamily:"'Barlow Condensed'",fontWeight:700,fontSize:10.5,color:T.fg3,width:70,flexShrink:0}}>{g.date}</span>
                      <span style={{fontFamily:"'JetBrains Mono'",fontSize:11,color:T.fg1,width:36,flexShrink:0}}>{g.ip!=null?g.ip.toFixed(1):"—"}IP</span>
                      <span style={{fontFamily:"'Barlow Condensed'",fontWeight:700,fontSize:10.5,color:T.fg2,flex:1}}>{g.k!=null?g.k+"K":"—"} · {g.bb!=null?g.bb+"BB":"—"}</span>
                      {g.hr>0 && <span style={{fontFamily:"'Barlow Condensed'",fontWeight:800,fontSize:10.5,color:T.amber,background:"rgba(255,176,32,.12)",border:"1px solid rgba(255,176,32,.4)",borderRadius:4,padding:"2px 7px"}}>⚡ {g.hr} HR</span>}
                    </div>
                  ))}
                </div>
            : <div style={{padding:20,border:"1px dashed rgba(255,176,32,.4)",borderRadius:8,background:"rgba(255,176,32,.04)",textAlign:"center"}}><Eyebrow style={{color:T.amber}}>DATA PENDING</Eyebrow></div>
          }
        </Mod>
      </div>

      {/* ── ACTION BAR ───────────────────────────────────── */}
      <div style={{display:"grid",gridTemplateColumns:"1fr auto",gap:12,alignItems:"center"}}>
        <div style={{display:"flex",alignItems:"center",gap:12,padding:"10px 14px",background:"linear-gradient(180deg,#0f171c,#0c1216)",border:`1px solid ${T.bd}`,borderRadius:9}}>
          <div style={{flex:1}}>
            <Ttl>BATTER RESEARCH · {batterName.toUpperCase()}</Ttl>
            <Eyebrow style={{color:T.fg3,marginTop:3}}>TONIGHT vs {pitcherName.toUpperCase()} · {pitcherHand}HP · LEAN {verdictLabel}</Eyebrow>
          </div>
          {onPitch && (
            <button onClick={onPitch} style={{fontFamily:"'Barlow Condensed'",fontWeight:800,fontSize:13,letterSpacing:".06em",textTransform:"uppercase",padding:"12px 22px",borderRadius:8,border:`1.5px solid rgba(0,217,255,.5)`,color:T.cyan,background:"rgba(0,217,255,.08)",cursor:"pointer",whiteSpace:"nowrap"}}>
              ⚙ PITCH MIX ANALYSIS →
            </button>
          )}
        </div>
        <div style={{display:"flex",gap:8,padding:"10px 14px",background:"linear-gradient(180deg,#0f171c,#0c1216)",border:`1px solid ${T.bd}`,borderRadius:9}}>
          {[["◁ BACK", false, onClose], ["◷ LIVE GAME", true, null], ["◈ PITCHER CARD", true, null]].map(([lbl,soon,fn],i) => (
            <button key={i} onClick={fn||undefined} style={{fontFamily:"'Barlow Condensed'",fontWeight:800,fontSize:11,letterSpacing:".05em",textTransform:"uppercase",padding:"10px 14px",borderRadius:7,border:`1px solid ${T.bd2}`,color:soon?T.fg3:T.fg2,background:T.void,cursor:soon?"default":"pointer",display:"flex",alignItems:"center",gap:6}}>
              {lbl}{soon && <span style={{fontSize:8,letterSpacing:".12em",color:T.amber,border:"1px solid rgba(255,176,32,.45)",borderRadius:3,padding:"2px 4px"}}>SOON</span>}
            </button>
          ))}
        </div>
      </div>

      {/* ── FOOTER ───────────────────────────────────────── */}
      <div style={{display:"flex",flexWrap:"wrap",gap:"6px 14px",padding:"8px 13px",borderTop:`1px solid ${T.bd}`,fontFamily:"'Barlow Condensed'",fontWeight:600,fontSize:10.5,letterSpacing:".06em",textTransform:"uppercase",color:T.fg2,alignItems:"center"}}>
        <span><span style={{width:7,height:7,borderRadius:"50%",display:"inline-block",marginRight:5,background:T.green,boxShadow:`0 0 8px ${T.gg}`}}/>DISPLAY ONLY · NO SCORING IMPACT</span>
        <span style={{color:T.fg3,opacity:.5}}>|</span>
        <span>DATA · <b style={{color:metaBlock.freshness==="Live"?T.green:T.amber}}>{metaBlock.freshness||"—"}</b></span>
        <span style={{color:T.fg3,opacity:.5}}>|</span>
        <span>SLATE · <b style={{color:T.fg1}}>{metaBlock.slate_date||"—"}</b></span>
        <span style={{color:T.fg3,opacity:.5}}>|</span>
        <span>ID · <b style={{fontFamily:"'JetBrains Mono'",fontSize:9,color:T.fg3}}>{batterId}</b></span>
        <span style={{color:T.fg3,opacity:.5}}>|</span>
        <span style={{color:T.fg3}}>{metaBlock.generated_at?metaBlock.generated_at.slice(0,16).replace("T"," ")+" UTC":""}</span>
      </div>

    </div>
  );
}

// Expose to window for cross-file access from full-slate-matrix.js
window.BatterDetailCard = BatterDetailCard;
