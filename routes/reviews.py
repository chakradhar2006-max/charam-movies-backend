from flask import Blueprint, request
from database.db import db
from models.review import Review
from models.movie import Movie
from utils.responses import ok, err
from utils.validators import to_int, sanitize_str
from middleware.auth import token_required

reviews_bp = Blueprint("reviews", __name__, url_prefix="/api/reviews")


@reviews_bp.get("/movie/<int:movie_id>")
def get_reviews(movie_id):
    movie = Movie.query.get(movie_id)
    if not movie:
        return err("Movie not found", 404)
    reviews = Review.query.filter_by(movie_id=movie_id).order_by(Review.created_at.desc()).all()
    return ok(
        {
            "reviews": [r.to_dict() for r in reviews],
            "average_rating": movie.average_rating(),
            "review_count": len(reviews),
        },
        "Reviews retrieved successfully",
    )


@reviews_bp.post("")
@token_required
def add_review(current_user):
    data = request.get_json(silent=True) or {}
    movie_id = data.get("movie_id")
    rating = to_int(data.get("rating"))
    if not movie_id or not Movie.query.get(movie_id):
        return err("A valid movie_id is required", 422)
    if rating is None or rating < 1 or rating > 5:
        return err("rating must be an integer from 1 to 5", 422)

    existing = Review.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if existing:
        return err("You have already reviewed this movie. Use update instead.", 409)

    review = Review(
        user_id=current_user.id,
        movie_id=movie_id,
        rating=rating,
        review_text=sanitize_str(data.get("review_text"), 4000),
    )
    db.session.add(review)
    db.session.commit()
    return ok({"review": review.to_dict()}, "Review added successfully", 201)


@reviews_bp.put("/<int:review_id>")
@token_required
def update_review(current_user, review_id):
    review = Review.query.get(review_id)
    if not review:
        return err("Review not found", 404)
    if review.user_id != current_user.id and current_user.role != "admin":
        return err("You can only edit your own review", 403)

    data = request.get_json(silent=True) or {}
    if "rating" in data:
        rating = to_int(data["rating"])
        if rating is None or rating < 1 or rating > 5:
            return err("rating must be an integer from 1 to 5", 422)
        review.rating = rating
    if "review_text" in data:
        review.review_text = sanitize_str(data["review_text"], 4000)
    db.session.commit()
    return ok({"review": review.to_dict()}, "Review updated successfully")


@reviews_bp.delete("/<int:review_id>")
@token_required
def delete_review(current_user, review_id):
    review = Review.query.get(review_id)
    if not review:
        return err("Review not found", 404)
    if review.user_id != current_user.id and current_user.role != "admin":
        return err("You can only delete your own review", 403)
    db.session.delete(review)
    db.session.commit()
    return ok(message="Review deleted successfully")
