import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from db import get_conn
from email_sender import send_magic_link
from config import FRONTEND_URL

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAGIC_LINK_TTL_MINUTES = 15
SESSION_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days

# In-memory session tokens, same lightweight pattern as admin_auth.py.
# Lost on restart (users just sign in again) - the durable state that
# actually matters (email, free_session_used, credits) lives in the DB.
_sessions: Dict[str, dict] = {}  # token -> {"email": ..., "expires_at": ...}


def is_valid_email(email: str) -> bool:
    return bool(email and EMAIL_RE.match(email.strip()))


def request_magic_link(email: str) -> None:
    email = email.strip().lower()
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=MAGIC_LINK_TTL_MINUTES)).isoformat()

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO magic_link_tokens (token, email, expires_at) VALUES (?, ?, ?)",
            (token, email, expires_at),
        )
        conn.execute(
            "INSERT INTO users (email) VALUES (?) ON CONFLICT(email) DO NOTHING",
            (email,),
        )

    link = f"{FRONTEND_URL}/auth/callback?token={token}"
    send_magic_link(email, link)


def verify_magic_link(token: str) -> Optional[str]:
    """Consumes the token if valid, returns the associated email or None."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT email, expires_at, used FROM magic_link_tokens WHERE token = ?",
            (token,),
        ).fetchone()

        if row is None or row["used"]:
            return None

        expires_at = datetime.fromisoformat(row["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            return None

        conn.execute("UPDATE magic_link_tokens SET used = 1 WHERE token = ?", (token,))
        return row["email"]


def create_session(email: str) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = {"email": email, "expires_at": time.time() + SESSION_TTL_SECONDS}
    return token


def get_session_email(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    session = _sessions.get(token)
    if session is None:
        return None
    if time.time() > session["expires_at"]:
        _sessions.pop(token, None)
        return None
    return session["email"]


def get_user(email: str) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT email, free_session_used, credits FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if row is None:
            conn.execute("INSERT INTO users (email) VALUES (?)", (email,))
            return {"email": email, "free_session_used": False, "credits": 0}
        return {
            "email": row["email"],
            "free_session_used": bool(row["free_session_used"]),
            "credits": row["credits"],
        }


def can_start_session(email: str) -> bool:
    user = get_user(email)
    return not user["free_session_used"] or user["credits"] > 0


def consume_session_entitlement(email: str) -> None:
    """Called right before starting a new evaluation. Spends the free
    session if unused, otherwise spends one credit. Caller must have
    already checked can_start_session() - this doesn't re-check, so it
    will drive credits negative if called without that guard."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT free_session_used, credits FROM users WHERE email = ?", (email,)
        ).fetchone()
        if row is not None and not row["free_session_used"]:
            conn.execute(
                "UPDATE users SET free_session_used = 1 WHERE email = ?", (email,)
            )
        else:
            conn.execute(
                "UPDATE users SET credits = credits - 1 WHERE email = ?", (email,)
            )


def grant_credits(email: str, amount: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO users (email, credits) VALUES (?, ?) "
            "ON CONFLICT(email) DO UPDATE SET credits = credits + excluded.credits",
            (email, amount),
        )
