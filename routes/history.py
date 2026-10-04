from datetime import datetime
from flask import Blueprint, request
from database.db import db
from models.history import WatchHistory
from models.movie import Movie
from utils.responses import ok, err
from utils.validators import to_int
from middleware.auth import token_required

history_bp = Blueprint("history", __name__, url_prefix="/api/history")


@history_bp.post("")
@token_required
def add_history(current_user):
    data = request.get_json(silent=True) or {}
    movie_id = data.get("movie_id")
    if not movie_id or not Movie.query.get(movie_id):
        return err("A valid movie_id is required", 422)

    record = WatchHistory.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    position = to_int(data.get("watch_position"), 0) or 0
    if record:
        record.watch_position = position
        record.watched_at = datetime.utcnow()
        record.completed = bool(data.get("completed", record.completed))
    else:
        record = WatchHistory(
            user_id=current_user.id,
            movie_id=movie_id,
            watch_position=position,
            completed=bool(data.get("completed", False)),
        )
        db.session.add(record)
    db.session.commit()
    return ok({"history": record.to_dict()}, "Watch history recorded", 201)


@history_bp.put("/<int:movie_id>/position")
@token_required
def update_position(current_user, movie_id):
    data = request.get_json(silent=True) or {}
    record = WatchHistory.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if not record:
        return err("No history found for this movie", 404)
    record.watch_position = to_int(data.get("watch_position"), record.watch_position)
    if "completed" in data:
        record.completed = bool(data["completed"])
    record.watched_at = datetime.utcnow()
    db.session.commit()
    return ok({"history": record.to_dict()}, "Watch position updated")


@history_bp.get("/continue-watching")
@token_required
def continue_watching(current_user):
    items = (
        WatchHistory.query.filter_by(user_id=current_user.id, completed=False)
        .order_by(WatchHistory.watched_at.desc())
        .limit(20)
        .all()
    )
    return ok({"continue_watching": [i.to_dict() for i in items]})


@history_bp.get("")
@token_required
def full_history(current_user):
    items = (
        WatchHistory.query.filter_by(user_id=current_user.id)
        .order_by(WatchHistory.watched_at.desc())
        .all()
    )
    return ok({"history": [i.to_dict() for i in items]}, "Watch history retrieved successfully")


@history_bp.delete("/<int:movie_id>")
@token_required
def remove_history(current_user, movie_id):
    record = WatchHistory.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if not record:
        return err("No history found for this movie", 404)
    db.session.delete(record)
    db.session.commit()
    return ok(message="Removed from watch history")
