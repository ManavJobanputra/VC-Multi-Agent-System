import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from config import ADMIN_PASSWORD
from db import get_conn

_SESSION_TTL_SECONDS = 12 * 60 * 60  # 12 hours


def verify_password(password: str) -> bool:
    if not ADMIN_PASSWORD:
        return False
    return hmac.compare_digest(password, ADMIN_PASSWORD)


def create_session() -> str:
    """Persisted in Postgres (not in-memory) so an admin session survives a
    redeploy/restart instead of silently logging the admin out."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=_SESSION_TTL_SECONDS)
    with get_conn() as conn:
        conn.execute("DELETE FROM admin_sessions WHERE expires_at <= CURRENT_TIMESTAMP")
        conn.execute(
            "INSERT INTO admin_sessions (token, expires_at) VALUES (?, ?)",
            (token, expires_at),
        )
    return token


def verify_session(token: Optional[str]) -> bool:
    if not token:
        return False
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM admin_sessions WHERE token = ? AND expires_at > CURRENT_TIMESTAMP",
            (token,),
        ).fetchone()
        return row is not None


def revoke_session(token: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM admin_sessions WHERE token = ?", (token,))
