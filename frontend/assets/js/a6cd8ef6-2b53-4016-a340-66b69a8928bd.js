/* HR Engine — Master Dashboard. Persistent app shell:
   top bar (room/lens breadcrumb + command center), live-targets banner,
   stage (rooms render here), right rail (navigation + rotating quick picks). */

function MasterDashboard() {
  const [active, setActive] = React.useState({ engineId: "main", lensId: "fullSlate" });
  const [ccOpen, setCcOpen] = React.useState(false); // Tactical Command Center, scoped to current room

  // Per-room saved filters (persist across navigation + reloads).
  const [roomFilters, setRoomFilters] = React.useState(() => {
    try { return JSON.parse(localStorage.getItem("md_roomFilters")) || {}; } catch (e) { return {}; }
  });
  React.useEffect(() => {
    try { localStorage.setItem("md_roomFilters", JSON.stringify(roomFilters)); } catch (e) {}
  }, [roomFilters]);

  const engine = ENGINES.find((e) => e.id === active.engineId);
  const lens = engine.subs ? engine.subs.find((s) => s.id === active.lensId) : null;
  const roomKey = `${active.engineId}/${active.lensId || "_"}`;
  const currentFilters = roomFilters[roomKey] || null;

  // Save TCC filters to the room you're in.
  const onApplyFilters = (filters) => {
    setRoomFilters((prev) => ({ ...prev, [roomKey]: filters }));
  };
  const onClearFilters = () => {
    setRoomFilters((prev) => { const n = { ...prev }; delete n[roomKey]; return n; });
  };

  // Command Center panel is scoped to the room you're in — changing room/lens closes it
  // (saved filters for each room persist and re-apply when you return).
  React.useEffect(() => { setCcOpen(false); }, [active.engineId, active.lensId]);

  const defaultLens = (eng) => eng.subs.find((s) => s.tag === "DEFAULT") || eng.subs[0];

  // Select a room (engine) from the nav panel.
  const onSelectEngine = (eng) => {
    if (eng.expandable) {
      setActive({ engineId: eng.id, lensId: defaultLens(eng).id });
    } else {
      setActive({ engineId: eng.id, lensId: null });
    }
  };

  // Select a sub-lens from the top-bar tab strip.
  const onSelectLens = (eng, sub) => {
    setActive({ engineId: eng.id, lensId: sub.id });
  };

  const onViewAll = () => {setActive({ engineId: "strategy", lensId: null });};

  // breadcrumb chip styled with the active engine's accent
  const c = engine.color;
  const chipStyle = {
    color: c,
    background: `${c}0d`,
    boxShadow: `0 0 0 1.5px ${c}8c, 0 0 18px ${c}33`
  };

  return (
    <div className="md-app">
      {/* 1 — TOP BAR : room + sub-lens selector */}
      <div className="md-topbar" data-comment-anchor="18cc4e4515-div-53-7">
        <div className="md-crumb">
          <span className="md-crumb__chip" style={chipStyle}>{engine.name}</span>
          {engine.expandable ? (
            <div className="md-lenstabs">
              {engine.subs.map((s) => (
                <button
                  key={s.id}
                  className={`md-lenstab ${active.lensId === s.id ? "is-on" : ""}`}
                  style={active.lensId === s.id ? { "--eng-color": engine.color } : undefined}
                  onClick={() => onSelectLens(engine, s)}
                >
                  {s.name}
                </button>
              ))}
            </div>
          ) : (
            engine.suffix && <span className="md-crumb__lens-sub">{engine.suffix}</span>
          )}
        </div>
        <button
          className={`md-cc-btn ${ccOpen ? "is-open" : ""}`}
          onClick={() => setCcOpen((o) => !o)}
        >
          <span className="md-cc-btn__chev"><Icon name={ccOpen ? "chevron" : "chevronR"} size={16} color="currentColor" /></span>
          <span className="md-cc-btn__gear"><Icon name="gear" size={16} color="currentColor" /></span>
          Tactical Command Center
        </button>
      </div>

      {/* 2 — SPLIT */}
      <div className="md-split">
        <div className="md-left">
          <LiveTargets targets={LIVE_TARGETS} onPick={() => {}} />
          <Stage
            engine={engine}
            lens={lens}
            ccOpen={ccOpen}
            onCloseCC={() => setCcOpen(false)}
            appliedFilters={currentFilters}
            onApplyFilters={onApplyFilters}
            onClearFilters={onClearFilters}
            onOpenPlayer={() => {}} />
        </div>

        <div className="md-right">
          <NavPanel
            engines={ENGINES}
            active={active}
            onSelect={onSelectEngine} />
          
          <StrategyRail onViewAll={onViewAll} />
        </div>
      </div>
    </div>);

}

ReactDOM.createRoot(document.getElementById("root")).render(<MasterDashboard />);