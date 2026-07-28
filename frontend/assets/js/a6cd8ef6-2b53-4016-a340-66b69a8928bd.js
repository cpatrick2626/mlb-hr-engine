function StaleBanner() {
  const [info, setInfo] = React.useState(() => ({
    stale: window.SLATE_STALE === true,
    generatedAt: window.SLATE_GENERATED_AT || null,
  }));

  React.useEffect(() => {
    const handler = (e) => {
      setInfo({
        stale: e.detail && e.detail.stale === true,
        generatedAt: (e.detail && e.detail.generated_at) || null,
      });
    };
    window.addEventListener("hrEngineDataLoaded", handler);
    return () => window.removeEventListener("hrEngineDataLoaded", handler);
  }, []);

  if (!info.stale) return null;

  const dateStr = (() => {
    if (!info.generatedAt) return null;
    try {
      return new Date(info.generatedAt)
        .toLocaleDateString("en-US", { month: "short", day: "numeric" })
        .toUpperCase();
    } catch (_) { return null; }
  })();

  return (
    <div className="stale-banner">
      <span className="stale-banner__dot" />
      <span className="stale-banner__text">
        SHOWING LAST-GOOD SLATE
        {dateStr && <span className="stale-banner__date"> · {dateStr}</span>}
        <span className="stale-banner__note"> — TODAY'S SLATE UPDATES ~10 AM ET</span>
      </span>
    </div>
  );
}

/* HR Engine — Master Dashboard. Persistent app shell:
   top bar (room/lens breadcrumb + command center), live-targets banner,
   stage (rooms render here), right rail (navigation + rotating quick picks). */

function useMobileLayout() {
  const query = "(max-width: 768px)";
  const [isMobile, setIsMobile] = React.useState(() => window.matchMedia(query).matches);

  React.useEffect(() => {
    const media = window.matchMedia(query);
    const sync = (event) => setIsMobile(event.matches);
    sync(media);
    if (media.addEventListener) media.addEventListener("change", sync);
    else media.addListener(sync);
    return () => {
      if (media.removeEventListener) media.removeEventListener("change", sync);
      else media.removeListener(sync);
    };
  }, []);

  return isMobile;
}

function MasterDashboard() {
  const [active, setActive] = React.useState({ engineId: "main", lensId: "fullSlate" });
  const [ccOpen, setCcOpen] = React.useState(false); // Tactical Command Center, scoped to current room
  const isMobileLayout = useMobileLayout();
  const appRef = React.useRef(null);
  const stickyHeadRef = React.useRef(null);

  React.useLayoutEffect(() => {
    const app = appRef.current;
    const head = stickyHeadRef.current;
    if (!app || !head || !isMobileLayout) return undefined;
    const syncStickyHeight = () => {
      app.style.setProperty("--md-sticky-head-height", `${Math.ceil(head.getBoundingClientRect().height)}px`);
    };
    syncStickyHeight();
    const observer = typeof ResizeObserver === "function" ? new ResizeObserver(syncStickyHeight) : null;
    observer?.observe(head);
    window.addEventListener("resize", syncStickyHeight);
    return () => {
      observer?.disconnect();
      window.removeEventListener("resize", syncStickyHeight);
      app.style.removeProperty("--md-sticky-head-height");
    };
  }, [isMobileLayout]);

  // Per-room saved filters (persist across navigation + reloads).
  const [roomFilters, setRoomFilters] = React.useState(() => {
    try { return JSON.parse(localStorage.getItem("md_roomFilters")) || {}; } catch (e) { return {}; }
  });
  React.useEffect(() => {
    try { localStorage.setItem("md_roomFilters", JSON.stringify(roomFilters)); } catch (e) {}
  }, [roomFilters]);

  const engine = ENGINES.find((e) => e.id === active.engineId);
  const lens = engine.subs ? engine.subs.find((s) => s.id === active.lensId) : null;
  const roomKey = active.engineId;
  const currentFilters = roomFilters[roomKey] || null;

  // Save TCC filters to the active room, or an explicitly targeted room when
  // restoring a named MAIN/JIG build.
  const onApplyFilters = (filters, targetRoomKey = roomKey) => {
    setRoomFilters((prev) => ({ ...prev, [targetRoomKey]: filters }));
  };
  const onClearFilters = () => {
    setRoomFilters((prev) => { const n = { ...prev }; delete n[roomKey]; return n; });
  };

  // Command Center panel is scoped to the room you're in — changing room/lens closes it
  // (saved filters for each room persist and re-apply when you return).
  React.useEffect(() => { setCcOpen(false); }, [active.engineId, active.lensId]);

  // Fetch live slate data after React mounts so hrEngineDataLoaded fires after listeners attach.
  // Retries up to 4 times with backoff to tolerate Fly.io cold-start latency (~4-12s).
  React.useEffect(() => {
    const ATTEMPTS = 4, BASE_DELAY_MS = 1500, TIMEOUT_MS = 15000;
    async function fetchSlate() {
      let lastErr;
      for (let i = 0; i < ATTEMPTS; i++) {
        const ctrl = new AbortController();
        const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
        try {
          const res = await fetch("https://mlb-hr-api.fly.dev/api/slate?t=" + Date.now(), { signal: ctrl.signal });
          clearTimeout(timer);
          if (res.ok) {
            const data = await res.json();
            if (data.leaderboard_rows?.length) window.LEADERBOARD_ROWS = data.leaderboard_rows;
            if (data.leaderboard_rows_jig?.length) window.LEADERBOARD_ROWS_JIG = data.leaderboard_rows_jig;
            if (data.slate_games?.length) window.SLATE_GAMES = data.slate_games;
            if (data.generated_at) window.SLATE_GENERATED_AT = data.generated_at;
            window.SLATE_STALE = data.stale === true;
            window.dispatchEvent(new CustomEvent("hrEngineDataLoaded", { detail: data }));
            return;
          }
          if (res.status >= 400 && res.status < 500) { lastErr = new Error("Slate " + res.status); break; }
          lastErr = new Error("Slate " + res.status);
        } catch (err) {
          clearTimeout(timer);
          lastErr = err;
        }
        if (i < ATTEMPTS - 1) await new Promise(r => setTimeout(r, BASE_DELAY_MS * Math.pow(2, i)));
      }
      console.warn("HR Engine API unreachable:", lastErr);
      window.dispatchEvent(new CustomEvent("hrEngineDataLoaded", { detail: { _fetchFailed: true } }));
    }
    fetchSlate();
  }, []);

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

  const bottomNav = [
    { type: "engine", id: "main" },
    { type: "engine", id: "jig" },
    { type: "tcc" },
    { type: "engine", id: "strategy" },
    { type: "engine", id: "performance" },
  ];

  const topBar = (
    <div className="md-topbar" data-comment-anchor="18cc4e4515-div-53-7">
      <span className="md-mobile-brand">HR ENGINE</span>
      <div className="md-crumb">
        <span className="md-crumb__chip" style={chipStyle}>
          {engine.name}
          {engine.suffix && <span className="md-chip-sfx"> {engine.suffix}</span>}
        </span>
        {!engine.expandable && engine.suffix && <span className="md-crumb__lens-sub">{engine.suffix}</span>}
      </div>
      {engine.expandable && (
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
      )}
      <div className="md-topbar-right">
        <div id="slip-btn-root" />
        <div id="auth-root" />
        <button
          className={`md-cc-btn ${ccOpen ? "is-open" : ""}`}
          onClick={() => setCcOpen((o) => !o)}
        >
          <span className="md-cc-btn__chev"><Icon name={ccOpen ? "chevron" : "chevronR"} size={16} color="currentColor" /></span>
          <span className="md-cc-btn__gear"><Icon name="gear" size={16} color="currentColor" /></span>
          <span className="md-cc-btn__label">Tactical Command Center</span>
        </button>
      </div>
    </div>
  );

  return (
    <div className="md-app" ref={appRef}>
      {/* 1 — TOP BAR : room + sub-lens selector */}
      <div className="md-sticky-head" ref={stickyHeadRef}>
        {topBar}
        <SlateCommandStrip />
        <StaleBanner />
        {isMobileLayout && <LiveTargets targets={LIVE_TARGETS} onPick={() => {}} />}
      </div>

      {/* 2 — SPLIT */}
      <div className="md-split">
        <div className="md-left">
          {!isMobileLayout && <LiveTargets targets={LIVE_TARGETS} onPick={() => {}} />}
          <Stage
            engine={engine}
            lens={lens}
            ccOpen={ccOpen}
            onCloseCC={() => setCcOpen(false)}
            appliedFilters={currentFilters}
            roomFilters={roomFilters}
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

      {/* MOBILE BOTTOM NAV */}
      <nav className="md-bottom-nav">
        {bottomNav.map((item, i) => {
          if (item.type === "tcc") {
            return (
              <button key="tcc" className={`md-bottom-nav__item${ccOpen ? " is-on" : ""}`}
                style={{ "--eng-color": "var(--green-500)" }}
                onClick={() => setCcOpen((o) => !o)}>
                <span className="md-bottom-nav__ic"><Icon name="gear" size={20} color="currentColor" /></span>
                <span className="md-bottom-nav__label">TCC</span>
              </button>
            );
          }
          const eng = ENGINES.find((e) => e.id === item.id);
          if (!eng) return null;
          return (
            <button key={eng.id} className={`md-bottom-nav__item${active.engineId === eng.id ? " is-on" : ""}`}
              style={{ "--eng-color": eng.color }}
              onClick={() => onSelectEngine(eng)}>
              <span className="md-bottom-nav__ic"><Icon name={eng.icon} size={20} color="currentColor" /></span>
              <span className="md-bottom-nav__label">{eng.name}</span>
            </button>
          );
        })}
      </nav>
    </div>);

}

ReactDOM.createRoot(document.getElementById("root")).render(<MasterDashboard />);
