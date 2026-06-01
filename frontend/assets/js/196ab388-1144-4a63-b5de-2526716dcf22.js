/* HR Engine — Tactical Command Center (the filters screen). */

const FilterPanel = ({ num, title, children, cols = 3, className = "" }) => (
  <section className={`hr-panel-cc ${className}`}>
    <div className="hr-panel-cc__title">
      <span className="hr-panel-cc__num">{num}.</span> {title}
    </div>
    <div className="hr-panel-cc__grid" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
      {children}
    </div>
  </section>
);

const CommandHeader = ({ onClose }) => (
  <header className="hr-cc__header">
    <div className="hr-cc__brand">
      <svg className="hr-cc__logo" viewBox="0 0 40 40" width="38" height="38">
        <circle cx="20" cy="20" r="18" fill="#0e1519" stroke="#ff3344" strokeWidth="1.5" />
        <path d="M9 11 Q20 18 31 11 M9 29 Q20 22 31 29" fill="none" stroke="#ff3344" strokeWidth="1.5" strokeLinecap="round" opacity="0.8" />
        <circle cx="20" cy="20" r="4" fill="#ff3344" opacity="0.9" />
      </svg>
      <h1 className="hr-cc__title">MLB HR ENGINE <span className="hr-cc__dash">—</span> TACTICAL COMMAND CENTER</h1>
    </div>

    <div className="hr-cc__statusbar">
      <span className="hr-cc__live"><LiveDot size={7} /> LIVE STATUS</span>
      <span className="hr-cc__stat"><span className="hr-cc__k">ACTIVE SLATE:</span> 8 GAMES</span>
      <span className="hr-cc__stat"><span className="hr-cc__k">SYSTEM LOAD:</span> 14%</span>
      <span className="hr-cc__stat"><span className="hr-cc__k">CURRENT PRESET:</span> DEFAULT TACTICAL</span>
    </div>

    <div className="hr-cc__filters-line">
      <Icon name="filter" size={12} color="#1aff66" /> <span style={{ color: "#1aff66" }}>Active Filters: 12</span>
    </div>

    <div className="hr-cc__actions">
      <button className="hr-btn hr-btn--ghost">SAVE PRESET</button>
      <button className="hr-btn hr-btn--ghost">LOAD PRESET</button>
      <button className="hr-btn hr-btn--danger-ghost" onClick={onClose}>RESET ALL FILTERS</button>
    </div>
  </header>
);

const VisibilityPanel = () => (
  <section className="hr-panel-cc hr-panel-cc--vis">
    <div className="hr-panel-cc__title hr-panel-cc__title--vis">
      COMMAND CENTER VISIBILITY
      <Icon name="chevron" size={14} color="var(--fg-3)" />
    </div>
    <div className="hr-vis__grid">
      <div className="hr-vis__toggle"><span>HIDE SECTIONS</span><Toggle label="" on={false} /></div>
      <div className="hr-vis__toggle"><span>LYAR TREKRM MODE</span><Toggle label="" on={true} /></div>
      <button className="hr-vis__btn">COMPACT MODE</button>
      <button className="hr-vis__btn">SAVE LAYOUT DENSITY</button>
      <button className="hr-vis__btn">EXPANDED MODE</button>
      <button className="hr-vis__btn">TACTICAL PRESETS</button>
    </div>
  </section>
);

function CommandCenter({ onClose }) {
  return (
    <div className="hr-cc">
      <CommandHeader onClose={onClose} />

      <div className="hr-cc__body">
        {/* Row 1 */}
        <div className="hr-cc__row" style={{ gridTemplateColumns: "1fr 1fr" }}>
          <FilterPanel num="1" title="BATTER POWER & CONTACT">
            <Stepper label="ISO" value={0} step={0.005} decimals={3} max={1} />
            <Stepper label="xSLG" value={0} step={0.005} decimals={3} max={1} />
            <Stepper label="Barrel %" value={0} step={0.5} decimals={1} max={100} />
            <Stepper label="Hard Hit %" value={0} step={0.5} decimals={1} max={100} />
            <Stepper label="Avg Exit Velocity" unit="(MPH)" value={0} step={0.5} decimals={1} max={120} />
            <Stepper label="HR/FB %" value={0} step={0.5} decimals={1} max={100} />
          </FilterPanel>

          <FilterPanel num="2" title="LAUNCH & CONTACT SHAPE">
            <Stepper label="Pull Air %" value={0} step={0.5} decimals={1} max={100} />
            <Stepper label="Launch Angle" unit="(°)" value={0} step={0.5} decimals={1} min={-20} max={60} />
            <Stepper label="HR Window %" value={0} step={0.5} decimals={1} max={100} />
            <Stepper label="Sweet Spot %" value={0} step={0.5} decimals={1} max={100} />
            <Stepper label="Fly Ball %" value={0} step={0.5} decimals={1} max={100} />
            <span />
          </FilterPanel>
        </div>

        {/* Row 2 */}
        <div className="hr-cc__row" style={{ gridTemplateColumns: "1fr 1fr 1fr" }}>
          <FilterPanel num="3" title="MATCHUP & SPLITS">
            <Stepper label="vs RHP ISO" value={0} step={0.005} decimals={3} max={1} />
            <Stepper label="vs LHP ISO" value={0} step={0.005} decimals={3} max={1} />
            <Stepper label="Pitch Type Damage %" value={0} step={0.5} decimals={1} max={100} />
            <Stepper label="Min Matchup Modifier %" value={75} step={1} decimals={0} max={100} />
            <Stepper label="Min HVY Score" value={0} step={1} decimals={0} max={100} />
            <span />
          </FilterPanel>

          <FilterPanel num="4" title="PITCHER VULNERABILITY">
            <Stepper label="Total HR Allowed" value={0} step={1} decimals={0} max={100} />
            <Stepper label="HR/9" value={0} step={0.01} decimals={2} max={10} />
            <Stepper label="Barrel % Allowed" value={0} step={0.5} decimals={1} max={100} />
            <Stepper label="Hard Hit % Allowed" value={0} step={0.5} decimals={1} max={100} />
            <Stepper label="Fly Ball % Allowed" value={0} step={0.5} decimals={1} max={100} />
            <Stepper label="Pull Damage Allowed %" value={0} step={0.5} decimals={1} max={100} />
          </FilterPanel>

          <FilterPanel num="5" title="ENVIRONMENT">
            <Stepper label="Park HR Factor" value={0} step={0.5} decimals={1} max={200} />
            <Stepper label="Wind" unit="(MPH)" value={0} step={0.5} decimals={1} max={60} />
            <Dropdown label="Wind Direction" options={["Any", "Out to LF", "Out to CF", "Out to RF", "In from LF", "In from RF"]} />
            <Stepper label="Temperature" unit="(°F)" value={0} step={1} decimals={1} min={0} max={120} />
            <Stepper label="Humidity" unit="(°F)" value={0} step={1} decimals={1} max={100} />
            <Dropdown label="Air Density" options={["Any", "Low", "Average", "High"]} />
          </FilterPanel>
        </div>

        {/* Row 3 */}
        <div className="hr-cc__row" style={{ gridTemplateColumns: "1fr 1fr 1fr" }}>
          <FilterPanel num="6" title="ADVANCED HR SIGNALS">
            <Stepper label="Contact Shape Score" value={0} step={1} decimals={0} max={100} />
            <Stepper label="Arsenal Matchup Score" value={0} step={1} decimals={0} max={100} />
            <Stepper label="Opposite Field Weakness %" value={0} step={0.5} decimals={1} max={100} />
            <Stepper label="Lifted Hard Hit %" value={0} step={0.5} decimals={1} max={100} />
            <Stepper label="EV Trend" unit="(7G)" value={0} step={0.5} decimals={1} min={-50} max={50} />
            <span />
          </FilterPanel>

          <FilterPanel num="7" title="MOMENTUM & RECENCY">
            <Stepper label="Recent HRs" unit="(7G)" value={0} step={1} decimals={0} max={50} />
            <Stepper label="Recent Hard Hit %" unit="(7G)" value={0} step={0.5} decimals={1} max={100} />
            <Stepper label="Recent Barrel %" unit="(%)" value={0} step={0.5} decimals={1} max={100} />
            <Stepper label="Hot Streak Indicator" value={0} step={1} decimals={0} max={100} />
            <Stepper label="Recent EV Trend" unit="(7G)" value={0} step={0.5} decimals={1} min={-50} max={50} />
            <Stepper label="Launch Angle Trend" value={0} step={0.5} decimals={1} min={-50} max={50} />
          </FilterPanel>

          <FilterPanel num="8" title="GAME CONTEXT" className="hr-panel-cc--toggles">
            <Toggle label="Exclude Started Games" on={false} />
            <Toggle label="Include Live Games" on={true} />
            <Toggle label="No Time Gate" on={false} />
            <Toggle label="No Time Gate" on={false} />
            <Toggle label="Confirmed Lineups Only" on={false} />
            <Toggle label="Pre-Lineup Pool Toggle" on={true} />
          </FilterPanel>
        </div>

        {/* Row 4 */}
        <div className="hr-cc__row" style={{ gridTemplateColumns: "1.5fr 1fr" }}>
          <FilterPanel num="9" title="OUTPUT CONTROL" cols={5}>
            <Stepper label="Min Projected HR %" value={0} step={0.5} decimals={1} max={100} />
            <Stepper label="Min Confidence %" value={0} step={0.5} decimals={1} max={100} />
            <Stepper label="Max Players" value={75} step={1} decimals={0} max={500} />
            <Dropdown label="Sort By" options={["Projected HR %", "Confidence %", "EV", "Barrel %", "xSLG"]} />
            <Dropdown label="Sort Direction" options={["Descending", "Ascending"]} />
          </FilterPanel>

          <VisibilityPanel />
        </div>
      </div>

      <footer className="hr-cc__footer">
        <span className="hr-cc__footer-brand">
          <svg viewBox="0 0 24 24" width="16" height="16"><circle cx="12" cy="12" r="10" fill="none" stroke="#1aff66" strokeWidth="1.5"/><path d="M5 7 Q12 11 19 7 M5 17 Q12 13 19 17" fill="none" stroke="#1aff66" strokeWidth="1.2"/></svg>
          » MB ENGINE COMMAND SYSTEM
        </span>
        <span className="hr-cc__footer-stat"><span className="hr-cc__k">DATA STATUS:</span> <span style={{ color: "#1aff66" }}>LIVE</span></span>
        <span className="hr-cc__footer-stat"><span className="hr-cc__k">UPDATE TIMER:</span> 28s</span>
        <span className="hr-cc__footer-stat"><span className="hr-cc__k">STATUS:</span> <span style={{ color: "#1aff66" }}>OPERATIONAL</span></span>
        <span className="hr-cc__footer-stat"><span className="hr-cc__k">ACTIVE FILTERS:</span> 12</span>
        <span className="hr-cc__footer-stat"><span className="hr-cc__k">TACTICAL MODE:</span> <span style={{ color: "#1aff66" }}>ENGAGED</span></span>
        <span style={{ flex: 1 }} />
        <span className="hr-cc__footer-stat"><span className="hr-cc__k">SOURCE:</span> MLB STATS API</span>
      </footer>
    </div>
  );
}

Object.assign(window, { CommandCenter, FilterPanel, VisibilityPanel });
