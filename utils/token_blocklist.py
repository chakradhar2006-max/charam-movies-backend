"""
Minimal in-memory revoked-token set used to support /api/auth/logout.
This resets on server restart and does not scale across multiple processes —
for production, replace with a Redis SET keyed by token (or jti) with a TTL
matching JWT_ACCESS_TOKEN_EXPIRES.
"""
_revoked = set()


def revoke(token: str) -> None:
    if token:
        _revoked.add(token)


def is_revoked(token: str) -> bool:
    return token in _revoked
