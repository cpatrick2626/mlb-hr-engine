"""
JWT verification and beta-access gating.

Supabase issues ES256 JWTs signed with a per-project EC private key.
FastAPI routes declare `user=Depends(require_beta)` to gate on beta access,
or `user=Depends(require_auth)` to require login only (e.g. invite redemption).
"""

import os
import requests as _requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, jwk, JWTError

SUPABASE_URL         = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
JWT_SECRET           = os.environ.get("SUPABASE_JWT_SECRET")  # retained; no longer used for decode

_JWKS_URL = f"{SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"

_bearer = HTTPBearer()

# Lazy Supabase client — created once on first use
_supa = None
# JWKS cache: { kid: jwk_dict }
_jwks_cache: dict = {}


def _client():
    global _supa
    if _supa is None:
        from supabase import create_client
        _supa = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _supa


def _get_jwks(force_refresh: bool = False) -> dict:
    """Fetch JWKS from Supabase and return {kid: jwk_dict}. Raises 401 on network failure."""
    global _jwks_cache
    if _jwks_cache and not force_refresh:
        return _jwks_cache
    try:
        resp = _requests.get(_JWKS_URL, timeout=5)
        resp.raise_for_status()
        keys = resp.json().get("keys", [])
        _jwks_cache = {k["kid"]: k for k in keys if "kid" in k}
        return _jwks_cache
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to fetch JWKS: {exc}",
        )


def _decode(token: str) -> dict:
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    alg = header.get("alg")
    kid = header.get("kid")

    if alg != "ES256":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unsupported algorithm: {alg}. Only ES256 is accepted.",
        )

    # Look up the signing key; retry once on cache miss (key rotation)
    cache = _get_jwks()
    if kid not in cache:
        cache = _get_jwks(force_refresh=True)
    if kid not in cache:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unknown kid: {kid}",
        )

    try:
        public_key = jwk.construct(cache[kid], algorithm="ES256")
        return jwt.decode(token, public_key, algorithms=["ES256"], audience="authenticated")
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
