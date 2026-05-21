"""Shared requests-session guards for live data clients."""

from __future__ import annotations

import os
from urllib.parse import urlparse

import requests

_PROXY_ENV_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)
_LOOPBACK_PROXY_HOSTS = {"127.0.0.1", "localhost", "::1"}
_BLACKHOLE_PROXY_PORT = 9


def _is_loopback_blackhole_proxy(value: str) -> bool:
    raw = (value or "").strip()
    if not raw:
        return False
    parsed = urlparse(raw if "://" in raw else f"http://{raw}")
    host = (parsed.hostname or "").strip().lower()
    return host in _LOOPBACK_PROXY_HOSTS and parsed.port == _BLACKHOLE_PROXY_PORT


def configure_session(session: requests.Session) -> requests.Session:
    """
    Ignore broken loopback proxy sentinels that would otherwise zero out hydration.

    This keeps legitimate proxy setups intact and only disables env-derived proxies
    when they point at the local port-9 sinkhole seen on this workstation.
    """
    if any(_is_loopback_blackhole_proxy(os.getenv(key, "")) for key in _PROXY_ENV_KEYS):
        session.trust_env = False
        session.proxies = {}
    return session
