import hmac
import secrets
import time
from typing import Dict, Optional

from config import ADMIN_PASSWORD

_SESSION_TTL_SECONDS = 12 * 60 * 60  # 12 hours
_sessions: Dict[str, float] = {}  # token -> expiry unix timestamp


def verify_password(password: str) -> bool:
    if not ADMIN_PASSWORD:
        return False
    return hmac.compare_digest(password, ADMIN_PASSWORD)


def create_session() -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = time.time() + _SESSION_TTL_SECONDS
    return token


def verify_session(token: Optional[str]) -> bool:
    if not token:
        return False
    expiry = _sessions.get(token)
    if expiry is None:
        return False
    if time.time() > expiry:
        _sessions.pop(token, None)
        return False
    return True


def revoke_session(token: str):
    _sessions.pop(token, None)
