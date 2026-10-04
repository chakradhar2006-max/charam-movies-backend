from datetime import datetime
from database.db import db


class FeaturedMovie(db.Model):
    __tablename__ = "featured_movies"

    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(
        db.Integer, db.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    display_order = db.Column(db.Integer, nullable=False, default=0)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    movie = db.relationship("Movie", lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "display_order": self.display_order,
            "active": self.active,
            "movie": self.movie.to_dict(detailed=True) if self.movie else None,
        }
