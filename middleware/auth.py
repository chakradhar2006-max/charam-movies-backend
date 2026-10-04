"""
@token_required: validates the 'Authorization: Bearer <token>' header,
loads the user from the database, and passes it into the view as
current_user. Returns a consistent JSON error envelope on failure.
"""
from functools import wraps
from flask import request, jsonify, g
from utils.jwt_utils import decode_token, TokenError
from utils.token_blocklist import is_revoked
from models.user import User


def _extract_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return None


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"success": False, "message": "Authentication token is missing"}), 401
        if is_revoked(token):
            return jsonify({"success": False, "message": "Token has been revoked, please log in again"}), 401
        try:
            payload = decode_token(token)
        except TokenError as e:
            return jsonify({"success": False, "message": str(e)}), 401

        if payload.get("type") != "access":
            return jsonify({"success": False, "message": "Invalid token type"}), 401

        user = User.query.get(int(payload["sub"]))
        if not user or not user.is_active:
            return jsonify({"success": False, "message": "User not found or inactive"}), 401

        g.current_user = user
        return f(user, *args, **kwargs)

    return decorated


def optional_token(f):
    """Like token_required but does not fail when no/invalid token is present;
    current_user will be None in that case. Useful for public endpoints that
    personalize output when a user happens to be logged in."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = None
        token = _extract_token()
        if token:
            try:
                payload = decode_token(token)
                if payload.get("type") == "access":
                    user = User.query.get(int(payload["sub"]))
            except TokenError:
                user = None
        g.current_user = user
        return f(user, *args, **kwargs)

    return decorated
