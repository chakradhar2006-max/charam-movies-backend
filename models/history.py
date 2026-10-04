from datetime import datetime
from database.db import db


class WatchHistory(db.Model):
    __tablename__ = "watch_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    movie_id = db.Column(
        db.Integer, db.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    watch_position = db.Column(db.Integer, nullable=False, default=0)  # seconds
    completed = db.Column(db.Boolean, nullable=False, default=False)
    watched_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    movie = db.relationship("Movie", lazy="joined")

    __table_args__ = (
        db.UniqueConstraint("user_id", "movie_id", name="uq_user_movie_history"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "movie": self.movie.to_dict() if self.movie else None,
            "watch_position": self.watch_position,
            "completed": self.completed,
            "watched_at": self.watched_at.isoformat() if self.watched_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
