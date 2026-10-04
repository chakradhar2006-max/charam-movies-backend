from datetime import datetime
from database.db import db


class StreamEvent(db.Model):
    """One row per playback start — used to build analytics (daily streams,
    most-watched titles, watch time, etc.) without re-scanning watch_history."""
    __tablename__ = "stream_events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    movie_id = db.Column(
        db.Integer, db.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    duration_watched = db.Column(db.Integer, nullable=False, default=0)  # seconds, updated later

    movie = db.relationship("Movie", lazy="joined")
