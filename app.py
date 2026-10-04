"""
Charam Movies backend — Flask + MySQL (SQLAlchemy) + JWT.

Run locally with:  python app.py
Server listens on: http://127.0.0.1:5000
"""
from flask import Flask, jsonify
from flask_cors import CORS

from config import config
from database.db import db
import models  # noqa: F401  (registers all tables with SQLAlchemy metadata)

from routes.auth import auth_bp
from routes.movies import movies_bp
from routes.genres import genres_bp
from routes.watchlist import watchlist_bp
from routes.history import history_bp
from routes.reviews import reviews_bp
from routes.streaming import streaming_bp
from routes.subscription import subscription_bp
from routes.featured import featured_bp
from routes.users import users_bp
from routes.admin import admin_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)
    CORS(
        app,
        resources={r"/api/*": {"origins": config.CORS_ORIGINS}},
        supports_credentials=True,
    )

    for bp in (
        auth_bp,
        movies_bp,
        genres_bp,
        watchlist_bp,
        history_bp,
        reviews_bp,
        streaming_bp,
        subscription_bp,
        featured_bp,
        users_bp,
        admin_bp,
    ):
        app.register_blueprint(bp)

    @app.get("/")
    def index():
        return jsonify(
            {
                "success": True,
                "message": "Charam Movies API is running",
                "docs": "See README.md for the full endpoint list",
            }
        )

    @app.get("/api/health")
    def health():
        return jsonify({"success": True, "message": "healthy"})

    # ---- consistent error handling for uncaught cases ----
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "message": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "message": "Method not allowed"}), 405

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return jsonify({"success": False, "message": "Internal server error"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=config.DEBUG)
