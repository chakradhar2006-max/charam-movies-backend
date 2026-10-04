from datetime import datetime
from flask import Blueprint, request
from database.db import db
from models.movie import Movie
from models.history import WatchHistory
from models.stream_event import StreamEvent
from utils.responses import ok, err
from utils.validators import to_int
from middleware.auth import token_required

streaming_bp = Blueprint("streaming", __name__, url_prefix="/api/movies")


@streaming_bp.get("/<int:movie_id>/stream")
@token_required
def stream_movie(current_user, movie_id):
    movie = Movie.query.get(movie_id)
    if not movie or not movie.is_active:
        return err("Movie not available", 404)
    if not movie.video_url:
        return err("This title has no licensed stream configured yet", 409)

    # Premium gate: keep 4K behind a premium subscription as an example rule.
    if movie.quality == "4K" and current_user.subscription_type != "premium":
        return err("Upgrade to Premium to stream 4K titles", 402)

    # Record / refresh continue-watching position
    record = WatchHistory.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if record:
        record.watched_at = datetime.utcnow()
    else:
        record = WatchHistory(user_id=current_user.id, movie_id=movie_id, watch_position=0)
        db.session.add(record)

    db.session.add(StreamEvent(user_id=current_user.id, movie_id=movie_id))
    db.session.commit()

    return ok(
        {
            "movie_id": movie.id,
            "title": movie.title,
            "video_url": movie.video_url,  # licensed storage reference, never a raw file in the DB
            "quality": movie.quality,
            "resume_position": record.watch_position,
        },
        "Stream authorized",
    )


@streaming_bp.put("/<int:movie_id>/stream/progress")
@token_required
def update_stream_progress(current_user, movie_id):
    data = request.get_json(silent=True) or {}
    record = WatchHistory.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if not record:
        return err("No active stream session for this movie", 404)
    record.watch_position = to_int(data.get("watch_position"), record.watch_position)
    if "completed" in data:
        record.completed = bool(data["completed"])
    record.watched_at = datetime.utcnow()
    db.session.commit()
    return ok({"history": record.to_dict()}, "Progress saved")
