import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from db import get_conn

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SESSION_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days
MIN_PASSWORD_LENGTH = 8
PBKDF2_ITERATIONS = 260_000


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
    """Persists the session token in Postgres (not in-memory) so logins
    survive a redeploy/restart instead of silently signing everyone out,
    and so this works if the backend ever runs more than one instance."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=SESSION_TTL_SECONDS)
    with get_conn() as conn:
        # Opportunistic cleanup, piggybacking on a write we're already doing,
        # so the table doesn't grow unbounded without needing a cron job.
        conn.execute("DELETE FROM user_sessions WHERE expires_at <= CURRENT_TIMESTAMP")
        conn.execute(
            "INSERT INTO user_sessions (token, email, expires_at) VALUES (?, ?, ?)",
            (token, email, expires_at),
        )
    return token


def revoke_session(token: Optional[str]) -> None:
    if not token:
        return
    with get_conn() as conn:
        conn.execute("DELETE FROM user_sessions WHERE token = ?", (token,))


def get_session_email(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    with get_conn() as conn:
        row = conn.execute(
            "SELECT email FROM user_sessions WHERE token = ? AND expires_at > CURRENT_TIMESTAMP",
            (token,),
        ).fetchone()
        return row["email"] if row is not None else None


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


def consume_session_entitlement(email: str) -> bool:
    """Atomically spends the free session if unused, otherwise spends one
    credit. Returns True if an entitlement was actually spent, False if the
    user has neither a free session nor credits left. Each UPDATE is
    conditioned on the row still being in the spendable state, so two
    concurrent calls for the same user can't both succeed against the same
    entitlement (no separate check-then-write race)."""
    with get_conn() as conn:
        free_row = conn.execute(
            "UPDATE users SET free_session_used = 1 "
            "WHERE email = ? AND free_session_used = 0 "
            "RETURNING email",
            (email,),
        ).fetchone()
        if free_row is not None:
            return True

        credit_row = conn.execute(
            "UPDATE users SET credits = credits - 1 "
            "WHERE email = ? AND credits > 0 "
            "RETURNING credits",
            (email,),
        ).fetchone()
        return credit_row is not None


def grant_credits(email: str, amount: int, conn=None) -> None:
    """Grants credits. Pass an existing conn (from a `with get_conn()` block)
    to run this as part of a caller's transaction - e.g. billing.py grants
    credits atomically with the payment-status flip, so a failure here rolls
    back the status change too instead of leaving a 'captured' payment that
    never actually paid out."""
    if conn is not None:
        _grant_credits(conn, email, amount)
        return
    with get_conn() as conn:
        _grant_credits(conn, email, amount)


def _grant_credits(conn, email: str, amount: int) -> None:
    conn.execute(
        "INSERT INTO users (email, credits) VALUES (?, ?) "
        "ON CONFLICT(email) DO UPDATE SET credits = users.credits + excluded.credits",
        (email, amount),
    )
