"""
Non-admin, non-auth user endpoints. Profile get/update/change-password live in
routes/auth.py (/api/auth/me, /api/auth/change-password) since they operate on
the authenticated user's own account; admin-side user management lives in
routes/admin.py. This module is kept so the project structure matches the
spec and is the natural place to add things like public user stats later.
"""
from flask import Blueprint
from utils.responses import ok
from middleware.auth import token_required

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


@users_bp.get("/me/summary")
@token_required
def my_summary(current_user):
    """Small convenience endpoint: counts used by the frontend's profile menu."""
    from models.watchlist import Watchlist
    from models.history import WatchHistory
    from models.review import Review

    return ok(
        {
            "watchlist_count": Watchlist.query.filter_by(user_id=current_user.id).count(),
            "history_count": WatchHistory.query.filter_by(user_id=current_user.id).count(),
            "review_count": Review.query.filter_by(user_id=current_user.id).count(),
        }
    )
