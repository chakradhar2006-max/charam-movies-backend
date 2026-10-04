from datetime import datetime, timedelta
from flask import Blueprint, request
from sqlalchemy import func
from database.db import db
from models.user import User
from models.movie import Movie, MovieGenre
from models.genre import Genre
from models.featured import FeaturedMovie
from models.subscription import Subscription
from models.stream_event import StreamEvent
from models.history import WatchHistory
from utils.responses import ok, err
from utils.validators import sanitize_str, to_int, to_float
from middleware.admin import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# ---------------------------------------------------------------- dashboard
@admin_bp.get("/dashboard")
@admin_required
def dashboard(current_user):
    total_users = User.query.filter_by(role="user").count()
    total_movies = Movie.query.count()
    total_streams = StreamEvent.query.count()
    premium_users = User.query.filter_by(subscription_type="premium").count()

    # Mock revenue: premium users * mock premium price
    from models.subscription import PLAN_PRICES
    revenue = premium_users * PLAN_PRICES["premium"]

    today = datetime.utcnow().date()
    streams_today = StreamEvent.query.filter(
        func.date(StreamEvent.started_at) == today
    ).count()

    return ok(
        {
            "total_users": total_users,
            "total_movies": total_movies,
            "total_streams": total_streams,
            "streams_today": streams_today,
            "premium_users": premium_users,
            "revenue_mock": revenue,
        },
        "Dashboard data retrieved successfully",
    )


# ------------------------------------------------------------------- users
@admin_bp.get("/users")
@admin_required
def list_users(current_user):
    page = to_int(request.args.get("page"), 1) or 1
    per_page = min(to_int(request.args.get("per_page"), 20) or 20, 100)
    query = User.query.order_by(User.created_at.desc())
    total = query.count()
    users = query.offset((page - 1) * per_page).limit(per_page).all()
    return ok(
        {
            "users": [u.to_dict() for u in users],
            "pagination": {"page": page, "per_page": per_page, "total": total},
        },
        "Users retrieved successfully",
    )


@admin_bp.put("/users/<int:user_id>")
@admin_required
def update_user(current_user, user_id):
    user = User.query.get(user_id)
    if not user:
        return err("User not found", 404)
    data = request.get_json(silent=True) or {}
    if "role" in data and data["role"] in ("user", "admin"):
        user.role = data["role"]
    if "is_active" in data:
        user.is_active = bool(data["is_active"])
    if "subscription_type" in data and data["subscription_type"] in ("free", "premium"):
        user.subscription_type = data["subscription_type"]
    db.session.commit()
    return ok({"user": user.to_dict()}, "User updated successfully")


@admin_bp.delete("/users/<int:user_id>")
@admin_required
def delete_user(current_user, user_id):
    user = User.query.get(user_id)
    if not user:
        return err("User not found", 404)
    if user.id == current_user.id:
        return err("You cannot delete your own admin account", 400)
    db.session.delete(user)
    db.session.commit()
    return ok(message="User deleted successfully")


# ------------------------------------------------------------------ movies
# Full CRUD also exists at /api/movies (admin-protected for writes). These
# /api/admin/movies aliases share the same core logic and are provided to
# match the spec's admin surface.
@admin_bp.post("/movies")
@admin_required
def admin_add_movie(current_user):
    from routes.movies import create_movie_from_data

    data = request.get_json(silent=True) or {}
    try:
        movie = create_movie_from_data(data)
    except ValueError as e:
        return err(str(e), 422)
    return ok({"movie": movie.to_dict(detailed=True)}, "Movie added successfully", 201)


@admin_bp.put("/movies/<int:movie_id>")
@admin_required
def admin_update_movie(current_user, movie_id):
    from routes.movies import update_movie_from_data

    movie = Movie.query.get(movie_id)
    if not movie:
        return err("Movie not found", 404)
    data = request.get_json(silent=True) or {}
    movie = update_movie_from_data(movie, data)
    return ok({"movie": movie.to_dict(detailed=True)}, "Movie updated successfully")


@admin_bp.delete("/movies/<int:movie_id>")
@admin_required
def admin_delete_movie(current_user, movie_id):
    movie = Movie.query.get(movie_id)
    if not movie:
        return err("Movie not found", 404)
    db.session.delete(movie)
    db.session.commit()
    return ok(message="Movie deleted successfully")


# ---------------------------------------------------------------- featured
@admin_bp.get("/featured")
@admin_required
def admin_list_featured(current_user):
    items = FeaturedMovie.query.order_by(FeaturedMovie.display_order.asc()).all()
    return ok({"featured": [i.to_dict() for i in items]})


@admin_bp.post("/featured")
@admin_required
def admin_add_featured(current_user):
    data = request.get_json(silent=True) or {}
    movie_id = data.get("movie_id")
    if not movie_id or not Movie.query.get(movie_id):
        return err("A valid movie_id is required", 422)
    item = FeaturedMovie(
        movie_id=movie_id,
        display_order=to_int(data.get("display_order"), 0) or 0,
        active=bool(data.get("active", True)),
    )
    db.session.add(item)
    db.session.commit()
    return ok({"featured": item.to_dict()}, "Featured movie added", 201)


@admin_bp.put("/featured/<int:featured_id>")
@admin_required
def admin_update_featured(current_user, featured_id):
    item = FeaturedMovie.query.get(featured_id)
    if not item:
        return err("Featured entry not found", 404)
    data = request.get_json(silent=True) or {}
    if "display_order" in data:
        item.display_order = to_int(data["display_order"], item.display_order)
    if "active" in data:
        item.active = bool(data["active"])
    db.session.commit()
    return ok({"featured": item.to_dict()}, "Featured movie updated")


@admin_bp.delete("/featured/<int:featured_id>")
@admin_required
def admin_remove_featured(current_user, featured_id):
    item = FeaturedMovie.query.get(featured_id)
    if not item:
        return err("Featured entry not found", 404)
    db.session.delete(item)
    db.session.commit()
    return ok(message="Removed from featured")


# -------------------------------------------------------------- analytics
@admin_bp.get("/analytics")
@admin_required
def analytics(current_user):
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    daily_streams = (
        db.session.query(func.date(StreamEvent.started_at).label("day"), func.count(StreamEvent.id))
        .filter(StreamEvent.started_at >= week_ago)
        .group_by("day")
        .order_by("day")
        .all()
    )

    most_watched = (
        db.session.query(Movie.id, Movie.title, func.count(StreamEvent.id).label("plays"))
        .join(StreamEvent, StreamEvent.movie_id == Movie.id)
        .group_by(Movie.id)
        .order_by(func.count(StreamEvent.id).desc())
        .limit(10)
        .all()
    )

    new_registrations = (
        db.session.query(func.date(User.created_at).label("day"), func.count(User.id))
        .filter(User.created_at >= week_ago)
        .group_by("day")
        .order_by("day")
        .all()
    )

    active_users = (
        db.session.query(func.count(func.distinct(StreamEvent.user_id)))
        .filter(StreamEvent.started_at >= week_ago)
        .scalar()
    ) or 0

    total_watch_time_seconds = db.session.query(func.coalesce(func.sum(WatchHistory.watch_position), 0)).scalar() or 0

    subscription_counts = (
        db.session.query(Subscription.plan, func.count(Subscription.id))
        .group_by(Subscription.plan)
        .all()
    )

    return ok(
        {
            "daily_streams": [{"date": str(d), "count": c} for d, c in daily_streams],
            "most_watched_movies": [
                {"movie_id": mid, "title": title, "plays": plays} for mid, title, plays in most_watched
            ],
            "new_registrations": [{"date": str(d), "count": c} for d, c in new_registrations],
            "active_users_7d": active_users,
            "total_watch_time_seconds": int(total_watch_time_seconds),
            "subscription_counts": {plan: count for plan, count in subscription_counts},
            "total_streams": StreamEvent.query.count(),
        },
        "Analytics retrieved successfully",
    )
