from datetime import datetime
from database.db import db


class Watchlist(db.Model):
    __tablename__ = "watchlist"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    movie_id = db.Column(
        db.Integer, db.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    movie = db.relationship("Movie", lazy="joined")

    __table_args__ = (
        db.UniqueConstraint("user_id", "movie_id", name="uq_user_movie_watchlist"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "movie": self.movie.to_dict() if self.movie else None,
            "added_at": self.created_at.isoformat() if self.created_at else None,
        }
