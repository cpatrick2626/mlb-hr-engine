/* HR Engine — Navigation Panel: the MAIN room (engine) names.
   Sub-lenses live in the top bar (above the live banner), not here. */

const EngineRow = ({ eng, active, onSelect }) => {
  const isActive = active.engineId === eng.id;
  const styleVars = { "--eng-color": eng.color, "--eng-glow": eng.glow, "--eng-tint": eng.tint };
  return (
    <div className="md-eng" style={styleVars}>
      <button
        className={`md-eng__btn ${isActive ? "is-active" : ""}`}
        onClick={() => onSelect(eng)}
      >
        <span className="md-eng__ic"><Icon name={eng.icon} size={19} color="currentColor" strokeWidth={1.8} /></span>
        <span className="md-eng__meta">
          <span className="md-eng__name">{eng.name}{eng.suffix ? <span className="soft"> {eng.suffix}</span> : null}</span>
          {eng.desc && <span className="md-eng__desc">{eng.desc}</span>}
        </span>
        <span className="md-eng__chev"><Icon name="chevronR" size={15} color="currentColor" /></span>
      </button>
    </div>
  );
};

const NavPanel = ({ engines, active, onSelect }) => (
  <div className="md-nav">
    <div className="md-nav__title">Navigation Panel</div>
    {engines.map((eng) => (
      <EngineRow key={eng.id} eng={eng} active={active} onSelect={onSelect} />
    ))}
  </div>
);

Object.assign(window, { NavPanel, EngineRow });
