from datetime import datetime
from database.db import db


class MovieGenre(db.Model):
    """Many-to-many join table between movies and genres."""
    __tablename__ = "movie_genres"

    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(
        db.Integer, db.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    genre_id = db.Column(
        db.Integer, db.ForeignKey("genres.id", ondelete="CASCADE"), nullable=False, index=True
    )

    genre = db.relationship("Genre", lazy="joined")

    __table_args__ = (
        db.UniqueConstraint("movie_id", "genre_id", name="uq_movie_genre"),
    )


class Movie(db.Model):
    __tablename__ = "movies"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    release_year = db.Column(db.Integer, nullable=False, index=True)
    rating = db.Column(db.Numeric(3, 1), nullable=False, default=0)
    language = db.Column(db.String(60), nullable=False, index=True)
    duration = db.Column(db.Integer, nullable=False)  # minutes
    country = db.Column(db.String(80), nullable=False, index=True)
    quality = db.Column(db.Enum("HD", "4K", name="movie_quality"), nullable=False, default="HD")
    description = db.Column(db.Text, nullable=True)
    poster_url = db.Column(db.String(500), nullable=True)
    trailer_url = db.Column(db.String(500), nullable=True)
    video_url = db.Column(db.String(500), nullable=True)  # licensed storage reference
    director = db.Column(db.String(150), nullable=True)
    # column is named cast_list in the DB because CAST is a reserved SQL keyword;
    # the Python attribute stays `cast` to match the spec's field name.
    cast = db.Column("cast_list", db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    genre_links = db.relationship(
        "MovieGenre", backref="movie", lazy=True, cascade="all, delete-orphan"
    )
    reviews = db.relationship(
        "Review", backref="movie", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def genres(self):
        return [link.genre.name for link in self.genre_links]

    def average_rating(self):
        if not self.reviews:
            return float(self.rating) if self.rating else 0.0
        total = sum(r.rating for r in self.reviews)
        return round(total / len(self.reviews), 1)

    def to_dict(self, detailed=False):
        data = {
            "id": self.id,
            "title": self.title,
            "release_year": self.release_year,
            "rating": float(self.rating) if self.rating is not None else 0.0,
            "genres": self.genres,
            "language": self.language,
            "duration": self.duration,
            "country": self.country,
            "quality": self.quality,
            "poster_url": self.poster_url,
        }
        if detailed:
            data.update(
                {
                    "description": self.description,
                    "trailer_url": self.trailer_url,
                    "director": self.director,
                    "cast": [c.strip() for c in (self.cast or "").split(",") if c.strip()],
                    "average_user_rating": self.average_rating(),
                    "review_count": len(self.reviews),
                    "created_at": self.created_at.isoformat() if self.created_at else None,
                }
            )
        return data

    def __repr__(self):
        return f"<Movie {self.id} {self.title}>"
