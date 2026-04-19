"""
Google Sheets persistence for pick logs and P&L.
Falls back silently if credentials are not configured.

One-time setup:
  1. console.cloud.google.com → New Project
  2. Enable "Google Sheets API" and "Google Drive API"
  3. IAM & Admin → Service Accounts → Create → download JSON key
  4. Create a Google Sheet; share it (Editor) with the service account email
  5. In Streamlit Cloud → App Settings → Secrets, add:
       GOOGLE_CREDENTIALS = '<paste entire contents of JSON key file>'
       GOOGLE_SHEET_ID    = '<ID from the sheet URL between /d/ and /edit>'
"""

import json
import os

_client_cache = None
_client_checked = False


def _creds_json() -> str:
    try:
        import streamlit as st
        val = st.secrets.get("GOOGLE_CREDENTIALS", "")
        if val:
            return val
    except Exception:
        pass
    return os.getenv("GOOGLE_CREDENTIALS", "")


def _sheet_id() -> str:
    try:
        import streamlit as st
        val = st.secrets.get("GOOGLE_SHEET_ID", "")
        if val:
            return val
    except Exception:
        pass
    return os.getenv("GOOGLE_SHEET_ID", "")


def _client():
    global _client_cache, _client_checked
    if _client_checked:
        return _client_cache
    _client_checked = True
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        raw = _creds_json()
        if not raw:
            return None
        info = json.loads(raw)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
        ]
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        _client_cache = gspread.authorize(creds)
    except Exception:
        _client_cache = None
    return _client_cache


def available() -> bool:
    """True when Google Sheets credentials and sheet ID are both configured."""
    return _client() is not None and bool(_sheet_id())


def _spreadsheet():
    c = _client()
    sid = _sheet_id()
    if not c or not sid:
        return None
    try:
        return c.open_by_key(sid)
    except Exception:
        return None


def _worksheet(tab_name: str):
    ss = _spreadsheet()
    if ss is None:
        return None
    try:
        return ss.worksheet(tab_name)
    except Exception:
        try:
            return ss.add_worksheet(title=tab_name, rows=5000, cols=30)
        except Exception:
            return None


def read_rows(tab_name: str) -> list[dict]:
    ws = _worksheet(tab_name)
    if ws is None:
        return []
    try:
        return ws.get_all_records()
    except Exception:
        return []


def existing_dates(tab_name: str) -> set[str]:
    rows = read_rows(tab_name)
    return {str(r.get("date", "")) for r in rows if r.get("date")}


def append_rows(tab_name: str, fields: list[str], rows: list[dict]) -> bool:
    ws = _worksheet(tab_name)
    if ws is None:
        return False
    try:
        if not ws.get_all_values():
            ws.append_row(fields)
        for row in rows:
            ws.append_row([str(row.get(h, "")) for h in fields])
        return True
    except Exception:
        return False


def append_results(fields: list[str], rows: list[dict]) -> bool:
    """Append settled results to the 'results' tab."""
    return append_rows("results", fields, rows)
