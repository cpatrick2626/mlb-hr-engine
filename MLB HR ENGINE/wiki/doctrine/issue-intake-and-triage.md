# Issue Intake & Triage

Operator bugs, concerns, screenshots, confusing UI, missing data, suspected issues.

---

## Triage: No documented manual pipeline trigger procedure

Logged: 2026-06-14
Severity: LOW (scheduled run unaffected)
Surface: Backend / Ops

Observation:
- POST https://mlb-hr-api.fly.dev/api/pipeline/run returns {"detail":"Unauthorized"}.
- Endpoint is auth-protected (good); no operator-facing procedure documents
  the required credential, header name, or how to invoke a manual run.

Impact:
- Operator cannot force a manual pipeline run on demand (e.g., to recover from a
  missed scheduled run) without the credential and invocation details.

Open questions:
- Header/auth scheme expected (Authorization: Bearer? X-API-Key?).
- Where the credential lives (Fly secret name / .env key) — DO NOT store the value
  in vault or triage notes.
- How the scheduled run authenticates (it already holds a working credential).

Recommended next step:
- Document the manual trigger procedure (header + secret name only, never the value)
  in OPS_DAILY_SETUP.md once confirmed.
- No code change required; documentation/ops only.
