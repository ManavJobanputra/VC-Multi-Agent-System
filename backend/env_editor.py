import os
from typing import Dict

ROOT_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')

SECRET_KEY_MARKERS = ("KEY", "PASSWORD", "SECRET", "TOKEN")


def _is_secret(key: str) -> bool:
    return any(marker in key.upper() for marker in SECRET_KEY_MARKERS)


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}{'*' * 6}{value[-4:]}"


def read_env() -> Dict[str, str]:
    """Parse the root .env file into a plain key/value dict."""
    values = {}
    if not os.path.exists(ROOT_ENV_PATH):
        return values
    with open(ROOT_ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def read_env_masked() -> Dict[str, dict]:
    """Same as read_env, but secret-looking values are masked - safe to
    send to the admin UI. is_set tells the UI whether a value exists at
    all, since the masked string alone can't distinguish empty from set."""
    raw = read_env()
    result = {}
    for key, value in raw.items():
        is_secret = _is_secret(key)
        result[key] = {
            "value": _mask(value) if is_secret else value,
            "is_secret": is_secret,
            "is_set": bool(value),
        }
    return result


def update_env(updates: Dict[str, str]) -> None:
    """Update the given keys in the .env file, preserving every other
    line as-is. Keys with an empty/None value are skipped entirely - this
    is what lets the admin UI submit masked, untouched secret fields as
    blank and mean 'leave unchanged' rather than 'clear this value'."""
    updates = {k: v for k, v in updates.items() if v not in (None, "")}
    if not updates:
        return

    existing_lines = []
    if os.path.exists(ROOT_ENV_PATH):
        with open(ROOT_ENV_PATH, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()

    seen_keys = set()
    new_lines = []
    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            new_lines.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in updates:
            new_lines.append(f"{key}={updates[key]}\n")
            seen_keys.add(key)
        else:
            new_lines.append(line)

    for key, value in updates.items():
        if key not in seen_keys:
            new_lines.append(f"{key}={value}\n")

    with open(ROOT_ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
