"""
Seeds the database with:
  - an admin account and a demo user account
  - the genre list
  - the same sample movie catalogue used in the frontend demo (so titles,
    years and ratings line up with what the UI already shows)
  - a handful of featured movies for the homepage hero
  - one sample review

Run with:  python -m database.seed
(run from the charam_movies_backend/ directory, after the tables exist)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database.db import db
from models.user import User
from models.genre import Genre
from models.movie import Movie, MovieGenre
from models.subscription import Subscription
from models.featured import FeaturedMovie
from models.review import Review

GENRES = [
    "Action", "Comedy", "Horror", "Romance", "Sci-Fi",
    "Thriller", "Family", "Anime", "Documentary",
]

# title, year, rating, genres, language, minutes, country, quality
MOVIES = [
    ("Midnight Meridian", 2026, 8.6, ["Thriller", "Action"], "English", 132, "USA", "4K"),
    ("Crimson Tide Rising", 2025, 8.1, ["Action"], "Hindi", 148, "India", "HD"),
    ("Neon Requiem", 2026, 8.9, ["Sci-Fi", "Thriller"], "English", 121, "UK", "4K"),
    ("The Last Lantern", 2024, 7.9, ["Family", "Anime"], "Japanese", 104, "Japan", "HD"),
    ("Laugh Track", 2025, 7.2, ["Comedy"], "English", 98, "Canada", "HD"),
    ("Hollow Manor", 2026, 7.5, ["Horror"], "English", 109, "UK", "4K"),
    ("Monsoon Letters", 2025, 8.3, ["Romance"], "Hindi", 137, "India", "HD"),
    ("Orbit Zero", 2026, 8.7, ["Sci-Fi", "Action"], "English", 140, "USA", "4K"),
    ("Silent Protocol", 2023, 8.0, ["Thriller"], "Korean", 117, "South Korea", "HD"),
    ("Paws & Planets", 2024, 7.6, ["Family", "Comedy"], "English", 92, "USA", "HD"),
    ("Kaveri Express", 2026, 8.4, ["Action", "Thriller"], "Tamil", 151, "India", "4K"),
    ("Rajadhani", 2025, 8.8, ["Action"], "Telugu", 165, "India", "4K"),
    ("Skyline Heist", 2024, 7.8, ["Action", "Comedy"], "English", 111, "USA", "HD"),
    ("Spirit Blade", 2026, 9.0, ["Anime", "Action"], "Japanese", 96, "Japan", "4K"),
    ("Wild Earth Diaries", 2025, 8.2, ["Documentary"], "English", 88, "UK", "HD"),
    ("Starlight Diner", 2023, 7.4, ["Romance", "Comedy"], "English", 101, "France", "HD"),
    ("Ghost Signal", 2025, 7.7, ["Horror", "Sci-Fi"], "Hindi", 113, "India", "HD"),
    ("Sakura Drift", 2024, 8.5, ["Anime", "Romance"], "Japanese", 99, "Japan", "4K"),
]

DIRECTORS = ["R. Kapoor", "E. Marlowe", "S. Rajan", "H. Ito", "L. Duval"]
CAST = ["Aria Vance", "Dev Malhotra", "Lena Ortiz", "Kabir Rao", "Mika Tanaka", "Sam Okafor", "Priya Nair", "Jonas Weber"]


def run():
    app = create_app()
    with app.app_context():
        db.create_all()

        # ---- genres ----
        genre_map = {}
        for name in GENRES:
            g = Genre.query.filter_by(name=name).first()
            if not g:
                g = Genre(name=name)
                db.session.add(g)
                db.session.flush()
            genre_map[name] = g

        # ---- users ----
        admin = User.query.filter_by(email="admin@charammovies.com").first()
        if not admin:
            admin = User(full_name="Charam Admin", email="admin@charammovies.com", role="admin", subscription_type="premium")
            admin.set_password("Admin@123")
            db.session.add(admin)
            db.session.flush()
            db.session.add(Subscription(user_id=admin.id, plan="premium", payment_status="paid"))

        demo = User.query.filter_by(email="demo@charammovies.com").first()
        if not demo:
            demo = User(full_name="Demo Viewer", email="demo@charammovies.com", role="user", subscription_type="free")
            demo.set_password("Demo@123")
            db.session.add(demo)
            db.session.flush()
            db.session.add(Subscription(user_id=demo.id, plan="free", payment_status="none"))

        db.session.commit()

        # ---- movies ----
        created = []
        for i, (title, year, rating, genres, lang, mins, country, quality) in enumerate(MOVIES):
            movie = Movie.query.filter_by(title=title).first()
            if movie:
                created.append(movie)
                continue
            movie = Movie(
                title=title,
                release_year=year,
                rating=rating,
                language=lang,
                duration=mins,
                country=country,
                quality=quality,
                description=(
                    "When a routine night turns into a race against time, an unlikely crew must "
                    "uncover a secret that spans cities and decades. (Sample synopsis.)"
                ),
                poster_url=f"https://picsum.photos/seed/charam{i}/400/600",
                trailer_url=None,
                video_url=f"https://cdn.example-licensed-storage.com/charam/{i}/master.m3u8",
                director=DIRECTORS[i % len(DIRECTORS)],
                cast=", ".join(CAST[j % len(CAST)] for j in range(i, i + 4)),
            )
            db.session.add(movie)
            db.session.flush()
            for g in genres:
                db.session.add(MovieGenre(movie_id=movie.id, genre_id=genre_map[g].id))
            created.append(movie)

        db.session.commit()

        # ---- featured (top rated titles) ----
        if FeaturedMovie.query.count() == 0:
            top = sorted(created, key=lambda m: float(m.rating), reverse=True)[:4]
            for order, m in enumerate(top):
                db.session.add(FeaturedMovie(movie_id=m.id, display_order=order, active=True))
            db.session.commit()

        # ---- sample review ----
        if Review.query.count() == 0 and created:
            db.session.add(
                Review(
                    user_id=demo.id,
                    movie_id=created[0].id,
                    rating=5,
                    review_text="Stunning visuals and a killer score.",
                )
            )
            db.session.commit()

        print(f"Seed complete: {len(created)} movies, {len(genre_map)} genres.")
        print("Admin login: admin@charammovies.com / Admin@123")
        print("Demo login:  demo@charammovies.com / Demo@123")


if __name__ == "__main__":
    run()
