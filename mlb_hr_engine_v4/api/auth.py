"""
JWT verification and beta-access gating.

Supabase issues HS256 JWTs signed with your project's JWT secret.
FastAPI routes declare `user=Depends(require_beta)` to gate on beta access,
or `user=Depends(require_auth)` to require login only (e.g. invite redemption).
"""

import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

SUPABASE_URL      = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
JWT_SECRET        = os.environ["SUPABASE_JWT_SECRET"]

_bearer = HTTPBearer()

# Lazy Supabase client — created once on first use
_supa = None


def _client():
    global _supa
    if _supa is None:
        from supabase import create_client
        _supa = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _supa


def _decode(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"], audience="authenticated")
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


def require_auth(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    """Verify JWT. Returns decoded payload. Does NOT check beta status."""
    return _decode(creds.credentials)


def require_beta(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    """Verify JWT and confirm user is in beta_users table."""
    payload = _decode(creds.credentials)
    user_id = payload.get("sub")
    result = _client().table("beta_users").select("user_id").eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Beta access required. Redeem an invite code first.",
        )
    return payload
