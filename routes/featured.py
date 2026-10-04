from flask import Blueprint
from models.featured import FeaturedMovie
from utils.responses import ok

featured_bp = Blueprint("featured", __name__, url_prefix="/api/featured")


@featured_bp.get("")
def get_featured():
    items = (
        FeaturedMovie.query.filter_by(active=True)
        .order_by(FeaturedMovie.display_order.asc())
        .all()
    )
    return ok({"featured": [i.to_dict() for i in items]}, "Featured movies retrieved successfully")
