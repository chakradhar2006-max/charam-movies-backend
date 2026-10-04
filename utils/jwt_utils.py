"""
Thin wrapper around PyJWT for issuing and verifying access/refresh tokens.
"""
from datetime import datetime, timezone
import jwt
from config import config


class TokenError(Exception):
    pass


def _encode(payload: dict, expires_delta) -> str:
    now = datetime.now(timezone.utc)
    to_encode = payload.copy()
    to_encode.update({"iat": now, "exp": now + expires_delta})
    return jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def generate_access_token(user_id: int, role: str) -> str:
    return _encode({"sub": str(user_id), "role": role, "type": "access"}, config.JWT_ACCESS_TOKEN_EXPIRES)


def generate_refresh_token(user_id: int) -> str:
    return _encode({"sub": str(user_id), "type": "refresh"}, config.JWT_REFRESH_TOKEN_EXPIRES)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenError("Token has expired")
    except jwt.InvalidTokenError:
        raise TokenError("Invalid token")
