import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(email) and bool(EMAIL_RE.match(email.strip()))


def is_strong_password(password: str) -> bool:
    """At least 6 characters. Kept simple on purpose for a demo app;
    tighten this for production use."""
    return bool(password) and len(password) >= 6


def sanitize_str(value, max_len=255):
    if value is None:
        return None
    value = str(value).strip()
    return value[:max_len]


def to_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def to_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
