from flask import Blueprint, request
from sqlalchemy import or_
from database.db import db
from models.movie import Movie, MovieGenre
from models.genre import Genre
from utils.responses import ok, err
from utils.validators import sanitize_str, to_int, to_float
from middleware.admin import admin_required

movies_bp = Blueprint("movies", __name__, url_prefix="/api/movies")


def _paginate(query):
    page = to_int(request.args.get("page"), 1) or 1
    per_page = to_int(request.args.get("per_page"), 20) or 20
    per_page = min(max(per_page, 1), 100)
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, {"page": page, "per_page": per_page, "total": total}


def _apply_filters(query):
    """Shared filtering logic used by GET /movies, /search and the genre/
    language/year/rating/country/duration filter endpoints."""
    genre = sanitize_str(request.args.get("genre"))
    language = sanitize_str(request.args.get("language"))
    year = to_int(request.args.get("year"))
    min_rating = to_float(request.args.get("min_rating") or request.args.get("rating"))
    country = sanitize_str(request.args.get("country"))
    max_duration = to_int(request.args.get("max_duration"))
    min_duration = to_int(request.args.get("min_duration"))

    if genre:
        query = query.join(MovieGenre).join(Genre).filter(Genre.name.ilike(genre))
    if language:
        query = query.filter(Movie.language.ilike(language))
    if year:
        query = query.filter(Movie.release_year == year)
    if min_rating is not None:
        query = query.filter(Movie.rating >= min_rating)
    if country:
        query = query.filter(Movie.country.ilike(country))
    if max_duration is not None:
        query = query.filter(Movie.duration <= max_duration)
    if min_duration is not None:
        query = query.filter(Movie.duration >= min_duration)
    return query


@movies_bp.get("")
def list_movies():
    query = Movie.query.filter_by(is_active=True)
    query = _apply_filters(query)
    items, meta = _paginate(query.order_by(Movie.created_at.desc()))
    return ok({"movies": [m.to_dict() for m in items], "pagination": meta}, "Movies retrieved successfully")


@movies_bp.get("/search")
def search_movies():
    q = sanitize_str(request.args.get("q") or request.args.get("query"))
    query = Movie.query.filter_by(is_active=True)

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Movie.title.ilike(like),
                Movie.language.ilike(like),
                Movie.country.ilike(like),
                Movie.director.ilike(like),
                Movie.cast.ilike(like),
            )
        )
    query = _apply_filters(query)
    items, meta = _paginate(query.order_by(Movie.rating.desc()))
    return ok({"movies": [m.to_dict() for m in items], "pagination": meta}, "Search results retrieved")


@movies_bp.get("/filter/genre/<string:genre_name>")
def filter_by_genre(genre_name):
    query = Movie.query.filter_by(is_active=True).join(MovieGenre).join(Genre).filter(
        Genre.name.ilike(genre_name)
    )
    items, meta = _paginate(query)
    return ok({"movies": [m.to_dict() for m in items], "pagination": meta})


@movies_bp.get("/filter/language/<string:language>")
def filter_by_language(language):
    query = Movie.query.filter_by(is_active=True).filter(Movie.language.ilike(language))
    items, meta = _paginate(query)
    return ok({"movies": [m.to_dict() for m in items], "pagination": meta})


@movies_bp.get("/filter/year/<int:year>")
def filter_by_year(year):
    query = Movie.query.filter_by(is_active=True, release_year=year)
    items, meta = _paginate(query)
    return ok({"movies": [m.to_dict() for m in items], "pagination": meta})


@movies_bp.get("/filter/rating/<float:min_rating>")
def filter_by_rating(min_rating):
    query = Movie.query.filter_by(is_active=True).filter(Movie.rating >= min_rating)
    items, meta = _paginate(query)
    return ok({"movies": [m.to_dict() for m in items], "pagination": meta})


@movies_bp.get("/filter/country/<string:country>")
def filter_by_country(country):
    query = Movie.query.filter_by(is_active=True).filter(Movie.country.ilike(country))
    items, meta = _paginate(query)
    return ok({"movies": [m.to_dict() for m in items], "pagination": meta})


@movies_bp.get("/filter/duration")
def filter_by_duration():
    """?min=100&max=130"""
    min_d = to_int(request.args.get("min"))
    max_d = to_int(request.args.get("max"))
    query = Movie.query.filter_by(is_active=True)
    if min_d is not None:
        query = query.filter(Movie.duration >= min_d)
    if max_d is not None:
        query = query.filter(Movie.duration <= max_d)
    items, meta = _paginate(query)
    return ok({"movies": [m.to_dict() for m in items], "pagination": meta})


@movies_bp.get("/<int:movie_id>")
def get_movie(movie_id):
    movie = Movie.query.get(movie_id)
    if not movie or not movie.is_active:
        return err("Movie not found", 404)
    return ok({"movie": movie.to_dict(detailed=True)}, "Movie retrieved successfully")


@movies_bp.get("/<int:movie_id>/similar")
def similar_movies(movie_id):
    movie = Movie.query.get(movie_id)
    if not movie:
        return err("Movie not found", 404)
    genre_names = movie.genres
    query = Movie.query.filter(Movie.id != movie_id, Movie.is_active == True)
    if genre_names:
        query = query.join(MovieGenre).join(Genre).filter(Genre.name.in_(genre_names)).distinct()
    results = query.order_by(Movie.rating.desc()).limit(8).all()
    return ok({"movies": [m.to_dict() for m in results]})


def _set_genres(movie: Movie, genre_names):
    MovieGenre.query.filter_by(movie_id=movie.id).delete()
    for name in genre_names:
        name = sanitize_str(name, 60)
        if not name:
            continue
        genre = Genre.query.filter_by(name=name).first()
        if not genre:
            genre = Genre(name=name)
            db.session.add(genre)
            db.session.flush()
        db.session.add(MovieGenre(movie_id=movie.id, genre_id=genre.id))


def create_movie_from_data(data: dict) -> Movie:
    """Core create logic, shared by POST /api/movies and POST /api/admin/movies."""
    title = sanitize_str(data.get("title"), 200)
    if not title:
        raise ValueError("title is required")

    movie = Movie(
        title=title,
        release_year=to_int(data.get("release_year"), 2026),
        rating=to_float(data.get("rating"), 0) or 0,
        language=sanitize_str(data.get("language"), 60) or "English",
        duration=to_int(data.get("duration"), 100) or 100,
        country=sanitize_str(data.get("country"), 80) or "USA",
        quality=data.get("quality") if data.get("quality") in ("HD", "4K") else "HD",
        description=sanitize_str(data.get("description"), 4000),
        poster_url=sanitize_str(data.get("poster_url"), 500),
        trailer_url=sanitize_str(data.get("trailer_url"), 500),
        video_url=sanitize_str(data.get("video_url"), 500),
        director=sanitize_str(data.get("director"), 150),
        cast=", ".join(data.get("cast", [])) if isinstance(data.get("cast"), list) else sanitize_str(data.get("cast"), 1000),
    )
    db.session.add(movie)
    db.session.flush()
    _set_genres(movie, data.get("genres", []))
    db.session.commit()
    return movie


def update_movie_from_data(movie: Movie, data: dict) -> Movie:
    """Core update logic, shared by PUT /api/movies/<id> and PUT /api/admin/movies/<id>."""
    simple_fields = [
        "title", "language", "country", "description", "poster_url",
        "trailer_url", "video_url", "director",
    ]
    for f in simple_fields:
        if f in data:
            setattr(movie, f, sanitize_str(data[f], 4000 if f == "description" else 500))
    if "release_year" in data:
        movie.release_year = to_int(data["release_year"], movie.release_year)
    if "rating" in data:
        movie.rating = to_float(data["rating"], float(movie.rating))
    if "duration" in data:
        movie.duration = to_int(data["duration"], movie.duration)
    if "quality" in data and data["quality"] in ("HD", "4K"):
        movie.quality = data["quality"]
    if "cast" in data:
        movie.cast = ", ".join(data["cast"]) if isinstance(data["cast"], list) else sanitize_str(data["cast"], 1000)
    if "genres" in data:
        _set_genres(movie, data["genres"])
    if "is_active" in data:
        movie.is_active = bool(data["is_active"])
    db.session.commit()
    return movie


@movies_bp.post("")
@admin_required
def add_movie(current_user):
    data = request.get_json(silent=True) or {}
    try:
        movie = create_movie_from_data(data)
    except ValueError as e:
        return err(str(e), 422)
    return ok({"movie": movie.to_dict(detailed=True)}, "Movie added successfully", 201)


@movies_bp.put("/<int:movie_id>")
@admin_required
def update_movie(current_user, movie_id):
    movie = Movie.query.get(movie_id)
    if not movie:
        return err("Movie not found", 404)
    data = request.get_json(silent=True) or {}
    movie = update_movie_from_data(movie, data)
    return ok({"movie": movie.to_dict(detailed=True)}, "Movie updated successfully")


@movies_bp.delete("/<int:movie_id>")
@admin_required
def delete_movie(current_user, movie_id):
    movie = Movie.query.get(movie_id)
    if not movie:
        return err("Movie not found", 404)
    db.session.delete(movie)
    db.session.commit()
    return ok(message="Movie deleted successfully")
