from flask import Blueprint, request
from database.db import db
from models.genre import Genre
from models.movie import Movie, MovieGenre
from utils.responses import ok, err
from utils.validators import sanitize_str
from middleware.admin import admin_required

genres_bp = Blueprint("genres", __name__, url_prefix="/api/genres")


@genres_bp.get("")
def list_genres():
    genres = Genre.query.order_by(Genre.name.asc()).all()
    return ok({"genres": [g.to_dict() for g in genres]}, "Genres retrieved successfully")


@genres_bp.post("")
@admin_required
def add_genre(current_user):
    data = request.get_json(silent=True) or {}
    name = sanitize_str(data.get("name"), 60)

    if not name:
        return err("name is required", 422)

    if Genre.query.filter_by(name=name).first():
        return err("Genre already exists", 409)

    genre = Genre(name=name)

    db.session.add(genre)
    db.session.commit()

    return ok(
        {"genre": genre.to_dict()},
        "Genre added successfully",
        201
    )


@genres_bp.put("/<int:genre_id>")
@admin_required
def update_genre(current_user, genre_id):
    genre = Genre.query.get(genre_id)

    if not genre:
        return err("Genre not found", 404)

    data = request.get_json(silent=True) or {}
    name = sanitize_str(data.get("name"), 60)

    if name:
        genre.name = name

    db.session.commit()

    return ok(
        {"genre": genre.to_dict()},
        "Genre updated successfully"
    )


@genres_bp.delete("/<int:genre_id>")
@admin_required
def delete_genre(current_user, genre_id):
    genre = Genre.query.get(genre_id)

    if not genre:
        return err("Genre not found", 404)

    db.session.delete(genre)
    db.session.commit()

    return ok(message="Genre deleted successfully")


@genres_bp.get("/<int:genre_id>/movies")
def movies_by_genre(genre_id):
    genre = Genre.query.get(genre_id)

    if not genre:
        return err("Genre not found", 404)

    movies = (
        Movie.query
        .join(MovieGenre, Movie.id == MovieGenre.movie_id)
        .filter(MovieGenre.genre_id == genre_id)
        .filter(Movie.is_active == True)
        .order_by(Movie.title.asc())
        .all()
    )

    return ok(
        {
            "genre": genre.name,
            "movies": [movie.to_dict() for movie in movies]
        },
        "Movies retrieved successfully"
    )