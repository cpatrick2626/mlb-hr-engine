# Cache Ownership Map

## Summary

Cache surfaces in the MLB HR Engine are closed and owned by specific system components. The Streamlit dashboard (`app.py`) and FastAPI service (`api/main.py`) have independent cache surfaces — they do not share cache state. Modifying cache ownership or cache key naming requires explicit operator authorization.

## Key Points

### Cache Surface Separation
- **Streamlit (`app.py`):** Owns its own cache layer. Uses Streamlit's `@st.cache_data` / `@st.cache_resource` decorators. Cache is scoped to the Streamlit process.
- **FastAPI (`api/main.py`, `api/cache.py`):** Owns its own cache layer. Independent of Streamlit. Cache is scoped to the uvicorn process.
- **pipeline.py:** Shared between both surfaces but does not own cache directly — callers manage caching of pipeline results.

### Known Cache Boundaries
| Cache Surface | Owner | Notes |
|---------------|-------|-------|
| Statcast/Savant data | pipeline.py callers | Freshness determined by caller |
| Market odds | pipeline.py callers | Time-sensitive; TTL matters |
| Lineup data | pipeline.py callers | Refreshed pre-game |
| FastAPI route cache | api/cache.py | Independent of Streamlit |
| Streamlit component cache | app.py | @st.cache_data scoped |

**Note:** Full cache key inventory requires Claude Code audit of `app.py`, `api/cache.py`, and `pipeline.py`. This stub reflects known architectural boundaries from doctrine.

## Cross-References

- [Session State Map](session-state-map.md)
- [Pipeline Data Flow](pipeline-data-flow.md)
- [Supabase Schema](supabase-schema.md)
