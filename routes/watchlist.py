from flask import Blueprint, request
from database.db import db
from models.watchlist import Watchlist
from models.movie import Movie
from utils.responses import ok, err
from middleware.auth import token_required

watchlist_bp = Blueprint("watchlist", __name__, url_prefix="/api/watchlist")


@watchlist_bp.get("")
@token_required
def get_watchlist(current_user):
    items = (
        Watchlist.query.filter_by(user_id=current_user.id)
        .order_by(Watchlist.created_at.desc())
        .all()
    )
    return ok({"watchlist": [i.to_dict() for i in items]}, "Watchlist retrieved successfully")


@watchlist_bp.post("")
@token_required
def add_to_watchlist(current_user):
    data = request.get_json(silent=True) or {}
    movie_id = data.get("movie_id")
    if not movie_id:
        return err("movie_id is required", 422)

    movie = Movie.query.get(movie_id)
    if not movie:
        return err("Movie not found", 404)

    existing = Watchlist.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if existing:
        return ok({"watchlist_item": existing.to_dict()}, "Movie already in watchlist")

    item = Watchlist(user_id=current_user.id, movie_id=movie_id)
    db.session.add(item)
    db.session.commit()
    return ok({"watchlist_item": item.to_dict()}, "Added to watchlist", 201)


@watchlist_bp.delete("/<int:movie_id>")
@token_required
def remove_from_watchlist(current_user, movie_id):
    item = Watchlist.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if not item:
        return err("Movie not found in watchlist", 404)
    db.session.delete(item)
    db.session.commit()
    return ok(message="Removed from watchlist")


@watchlist_bp.get("/check/<int:movie_id>")
@token_required
def check_watchlist(current_user, movie_id):
    exists = (
        Watchlist.query.filter_by(user_id=current_user.id, movie_id=movie_id).first() is not None
    )
    return ok({"in_watchlist": exists})
