"""
Push notifications via ntfy.sh

Setup (one-time):
  1. Install the ntfy app on your phone (iOS or Android — free).
  2. Pick a private topic name, e.g. "mlb-hr-engine-chris-abc123"
     (treat it like a password — anyone who knows it can subscribe).
  3. In the app, subscribe to that topic.
  4. Add NTFY_TOPIC=your-topic-name to mlb_hr_engine_v4/.env

That's it. No account, no API key, no cost.
"""

import os
import requests
from pathlib import Path

# Load from .env if python-dotenv is available; otherwise falls back to env vars.
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

NTFY_BASE = "https://ntfy.sh"


def _topic() -> str:
    return os.getenv("NTFY_TOPIC", "").strip()


def enabled() -> bool:
    return bool(_topic())


def send_hr_hit(player_name: str, team: str, odds: str, profit: float, date_str: str) -> bool:
    """
    Send a push notification for a confirmed HR.
    Returns True if the request succeeded (2xx).
    """
    topic = _topic()
    if not topic:
        return False

    sign   = "+" if profit >= 0 else ""
    title  = f"💥 HR — {player_name}"
    body   = (
        f"{team}  ·  {date_str}\n"
        f"Odds: {odds}  ·  P&L: {sign}${profit:.2f}"
    )

    try:
        resp = requests.post(
            f"{NTFY_BASE}/{topic}",
            data=body.encode("utf-8"),
            headers={
                "Title":    title,
                "Priority": "high",
                "Tags":     "baseball,moneybag",
            },
            timeout=8,
        )
        return resp.ok
    except Exception:
        return False


def send_settlement_summary(date_str: str, hits: int, misses: int, net_pl: float) -> bool:
    """
    Send a daily settlement summary (called after a full settle pass).
    Only fires if there was at least one settled pick.
    """
    topic = _topic()
    if not topic or (hits + misses) == 0:
        return False

    sign  = "+" if net_pl >= 0 else ""
    emoji = "✅" if net_pl >= 0 else "📉"
    title = f"{emoji} Settlement — {date_str}"
    body  = (
        f"{hits} HR / {misses} miss  ·  "
        f"Net: {sign}${net_pl:.2f}"
    )

    try:
        resp = requests.post(
            f"{NTFY_BASE}/{topic}",
            data=body.encode("utf-8"),
            headers={
                "Title":    title,
                "Priority": "default",
                "Tags":     "baseball",
            },
            timeout=8,
        )
        return resp.ok
    except Exception:
        return False
