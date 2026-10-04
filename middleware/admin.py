"""
@admin_required: combines with token_required to additionally check
current_user.role == 'admin'. Use order: @token_required then @admin_required,
or just @admin_required which already wraps token_required.
"""
from functools import wraps
from flask import jsonify
from middleware.auth import token_required


def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(current_user, *args, **kwargs):
        if current_user.role != "admin":
            return jsonify({"success": False, "message": "Admin privileges required"}), 403
        return f(current_user, *args, **kwargs)

    return decorated
