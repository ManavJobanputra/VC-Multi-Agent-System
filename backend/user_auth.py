import hashlib
import hmac
import re
import secrets
import time
from typing import Dict, Optional

from db import get_conn

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SESSION_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days
MIN_PASSWORD_LENGTH = 8
PBKDF2_ITERATIONS = 260_000

# In-memory session tokens, same lightweight pattern as admin_auth.py.
# Lost on restart (users just log in again) - the durable state that
# actually matters (email, password hash, free_session_used, credits)
# lives in the DB.
_sessions: Dict[str, dict] = {}  # token -> {"email": ..., "expires_at": ...}


def is_valid_email(email: str) -> bool:
    return bool(email and EMAIL_RE.match(email.strip()))


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return f"{salt}${digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, hex_digest = stored_hash.split("$", 1)
    except (ValueError, AttributeError):
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return hmac.compare_digest(digest.hex(), hex_digest)


def sign_up(email: str, password: str) -> str:
    """Creates a new account and returns a session token. Raises ValueError
    on bad input or an already-registered email."""
    email = email.strip().lower()
    if not is_valid_email(email):
        raise ValueError("Enter a valid email address")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")

    with get_conn() as conn:
        existing = conn.execute("SELECT email FROM users WHERE email = ?", (email,)).fetchone()
        if existing is not None:
            raise ValueError("An account with this email already exists. Log in instead.")
        conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, _hash_password(password)),
        )

    return create_session(email)


def log_in(email: str, password: str) -> str:
    """Verifies credentials and returns a session token. Raises ValueError
    on missing account or wrong password."""
    email = email.strip().lower()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()

    if row is None or not row["password_hash"] or not _verify_password(password, row["password_hash"]):
        raise ValueError("Incorrect email or password")

    return create_session(email)


def create_session(email: str) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = {"email": email, "expires_at": time.time() + SESSION_TTL_SECONDS}
    return token


def revoke_session(token: Optional[str]) -> None:
    if token:
        _sessions.pop(token, None)


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
