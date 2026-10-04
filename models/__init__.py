"""
Models package. Importing this module registers every table with SQLAlchemy's
metadata, which is required before db.create_all() / Flask-Migrate can see them.
"""
from .user import User
from .genre import Genre
from .movie import Movie, MovieGenre
from .watchlist import Watchlist
from .history import WatchHistory
from .review import Review
from .subscription import Subscription
from .featured import FeaturedMovie
from .stream_event import StreamEvent

__all__ = [
    "User",
    "Genre",
    "Movie",
    "MovieGenre",
    "Watchlist",
    "WatchHistory",
    "Review",
    "Subscription",
    "FeaturedMovie",
    "StreamEvent",
]
