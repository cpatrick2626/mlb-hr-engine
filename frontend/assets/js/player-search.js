/* HR Engine — Player Search
   Accent-tolerant, case-insensitive, substring player/pitcher locator.
   Operates on already-rendered DOM — does NOT re-rank or re-filter board data.
   Matches batter rows in FSM matrix (.fsm-player__name always full name),
   HR Threat Zone cards, and Pitcher Vulnerability cards (data-fullname attr). */

function _psNorm(s) {
  /* NFD decompose then drop all combining marks — handles Álvarez, Chaparro, etc. */
  return String(s || '').normalize('NFD').replace(/\p{M}/gu, '').toLowerCase();
}

function PlayerSearch() {
  var useState  = React.useState;
  var useEffect = React.useEffect;
  var useRef    = React.useRef;

  var queryState      = useState('');
  var query           = queryState[0];
  var setQuery        = queryState[1];

  var matchCountState = useState(null);
  var matchCount      = matchCountState[0];
  var setMatchCount   = matchCountState[1];

  var inputRef = useRef(null);

  function clearHighlights() {
    document.querySelectorAll('.is-search-hit').forEach(function(el) {
      el.classList.remove('is-search-hit');
    });
  }

  function runSearch(q) {
    clearHighlights();
    var trimmed = (q || '').trim();
    if (!trimmed) { setMatchCount(null); return; }

    var norm = _psNorm(trimmed);
    var hits = [];
    var seen = new Set();

    function addHit(el) {
      if (el && !seen.has(el)) { seen.add(el); hits.push(el); }
    }

    /* 1 — FSM matrix batter rows: .fsm-player__name always renders full name */
    try {
      document.querySelectorAll('.fsm-player__name').forEach(function(el) {
        if (_psNorm(el.textContent).indexOf(norm) !== -1) {
          var row = el.closest('tr');
          if (row) addHit(row);
        }
      });
    } catch (e) {}

    /* 2 — HR Threat Zone cards + Pitcher Vulnerability cards via data-fullname */
    try {
      document.querySelectorAll('[data-fullname]').forEach(function(el) {
        if (_psNorm(el.getAttribute('data-fullname') || '').indexOf(norm) !== -1) {
          addHit(el);
        }
      });
    } catch (e) {}

    setMatchCount(hits.length);
    hits.forEach(function(el) { el.classList.add('is-search-hit'); });
    if (hits[0]) {
      try { hits[0].scrollIntoView({ behavior: 'smooth', block: 'center' }); } catch (e) {}
    }
  }

  useEffect(function() {
    var timer = setTimeout(function() { runSearch(query); }, 200);
    return function() { clearTimeout(timer); };
  }, [query]);

  function onKeyDown(e) {
    if (e.key === 'Escape') {
      setQuery('');
      if (inputRef.current) inputRef.current.blur();
    }
  }

  var hasQuery  = query.length > 0;
  var showCount = hasQuery && matchCount !== null;

  return (
    <div className="ps-wrap">
      <div className={`ps-field${hasQuery ? ' ps-field--active' : ''}`}>
        <span className="ps-icon" aria-hidden="true">&#x2315;</span>
        <input
          ref={inputRef}
          className="ps-input"
          type="text"
          value={query}
          onChange={function(e) { setQuery(e.target.value); }}
          onKeyDown={onKeyDown}
          placeholder="FIND PLAYER"
          aria-label="Find player"
          autoComplete="off"
          spellCheck="false"
        />
        {hasQuery && (
          <button
            className="ps-clear"
            onClick={function() { setQuery(''); }}
            aria-label="Clear search"
          >&#xd7;</button>
        )}
      </div>
      {showCount && (
        <span className="ps-count">
          {matchCount === 0 ? 'NO MATCH' : matchCount + ' FOUND'}
        </span>
      )}
    </div>
  );
}
