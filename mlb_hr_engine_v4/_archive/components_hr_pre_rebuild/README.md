# Archive — components/hr/ pre-rebuild artifact

**Archived:** 2026-05-25
**Reason:** Superseded by `frontend/components/hr/` during the May 24 "MAIN HR-threat-first rebuild" commit (4601700d).
**Authorization:** Operator decision in [R11] Strategic Comms Hub, X-001 audit follow-up (X-002).

## Origin
These files originated in the May 23 commit "Add tactical HR threat card system" at:
`mlb_hr_engine_v4/components/hr/`

## Why archived
- Zero importers in the v4 tree at time of archival
- `frontend/app/page.tsx` is the sole consumer of HR threat card components; it resolves to `frontend/components/hr/` (canonical, doctrine-aligned, more refined)
- Streamlit runtime (`app.py`) does not consume `.tsx`
- Versions here are pre-refinement; missing corner brackets, pulse animations, semantic green barrel palette, and other doctrine-aligned refinements present in the canonical `frontend/` versions

## Restoration
If ever needed:
    git mv _archive/components_hr_pre_rebuild/hr components/hr

## Related audit trail
- C-001 doctrine audit (Steps 1–6) — May 25 2026
- X-001 frontend surface investigation — May 25 2026
- X-002 this archival — May 25 2026
