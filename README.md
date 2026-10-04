# Charam Movies — Backend API

Flask + MySQL (SQLAlchemy) + JWT backend for the Charam Movies OTT frontend.

## 1. Requirements

- Python 3.10+
- MySQL 8.x (or MariaDB 10.5+) running locally or reachable over the network
- pip

## 2. Setup

```bash
cd charam_movies_backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit .env with your real DB credentials/secrets
```

Create the database (empty) in MySQL:

```sql
CREATE DATABASE charam_movies CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 3. Create the tables

Two options — pick one:

**Option A — raw SQL script**
```bash
mysql -u root -p charam_movies < database/schema.sql
```

**Option B — let SQLAlchemy create them** (handled automatically by the seed script below, or manually):
```bash
python -c "from app import create_app; from database.db import db; app=create_app(); app.app_context().push(); db.create_all()"
```

## 4. Seed sample data (matches the frontend's demo catalogue)

```bash
python -m database.seed
```

This creates:
- Admin login: `admin@charammovies.com` / `Admin@123`
- Demo user login: `demo@charammovies.com` / `Demo@123`
- The 9 genres and 18 sample movies also used in the frontend demo
- 4 featured movies for the homepage hero
- 1 sample review

## 5. Run the server

```bash
python app.py
```

The API is now live at **http://127.0.0.1:5000**. Check `GET /api/health` to confirm it's up.

## 6. Connect the Charam Movies frontend

Open `charam-movies-connected.html` (the API-integrated version of the frontend). Near the top of its `<script>` block it sets:

```js
const API_BASE = "http://127.0.0.1:5000/api";
```

Change this if your backend runs elsewhere (a different port, a deployed domain, etc.). Then just open the HTML file in a browser, or serve it statically — no build step is required. CORS is already enabled on the backend for all origins by default (`CORS_ORIGINS=*` in `.env`); tighten this to your real frontend origin before going to production.

The frontend now calls these endpoints instead of using localStorage/demo logic:

| Frontend action | Endpoint |
|---|---|
| Register | `POST /api/auth/register` |
| Login | `POST /api/auth/login` |
| Logout | `POST /api/auth/logout` |
| Load profile | `GET /api/auth/me` |
| Load movie rows / hero | `GET /api/movies`, `GET /api/featured` |
| Search + filters | `GET /api/movies/search` |
| Movie details | `GET /api/movies/<id>` |
| Add/remove watchlist | `POST /api/watchlist`, `DELETE /api/watchlist/<movie_id>` |
| My List page | `GET /api/watchlist` |
| Continue watching | `GET /api/history/continue-watching` |
| Play a title | `GET /api/movies/<id>/stream` (also logs history) |
| Reviews | `GET /api/reviews/movie/<id>`, `POST /api/reviews` |
| Admin dashboard | `GET /api/admin/dashboard`, `GET /api/admin/analytics` |
| Admin add/remove movie | `POST /api/admin/movies`, `DELETE /api/admin/movies/<id>` |

## 7. Full API reference

All responses use this envelope:

```json
// success
{ "success": true, "message": "...", "data": { } }
// error
{ "success": false, "message": "..." }
```

Send a JWT on protected routes as: `Authorization: Bearer <access_token>`

### Auth — `/api/auth`
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/register` | – | Create account. Body: `full_name, email, password` |
| POST | `/login` | – | Returns `access_token`, `refresh_token`, `user` |
| POST | `/logout` | ✅ | Revokes the current access token |
| GET | `/me` | ✅ | Current user profile |
| PUT | `/me` | ✅ | Update `full_name` / `email` |
| POST | `/change-password` | ✅ | Body: `old_password, new_password` |

### Movies — `/api/movies`
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `` | – | List movies. Query: `page, per_page, genre, language, year, min_rating, country, min_duration, max_duration` |
| GET | `/search` | – | `?q=` plus any filter above |
| GET | `/filter/genre/<name>` | – | |
| GET | `/filter/language/<name>` | – | |
| GET | `/filter/year/<year>` | – | |
| GET | `/filter/rating/<min_rating>` | – | |
| GET | `/filter/country/<name>` | – | |
| GET | `/filter/duration` | – | `?min=&max=` |
| GET | `/<id>` | – | Full movie detail |
| GET | `/<id>/similar` | – | Related titles by shared genre |
| POST | `` | Admin | Create movie |
| PUT | `/<id>` | Admin | Update movie |
| DELETE | `/<id>` | Admin | Delete movie |
| GET | `/<id>/stream` | ✅ | Authorizes playback, returns `video_url`, logs history |
| PUT | `/<id>/stream/progress` | ✅ | Save resume position |

### Genres — `/api/genres`
`GET` (public), `POST` / `PUT /<id>` / `DELETE /<id>` (admin).

### Watchlist — `/api/watchlist`
`GET`, `POST` (`{movie_id}`), `DELETE /<movie_id>`, `GET /check/<movie_id>` — all require auth.

### History — `/api/history`
`POST` (`{movie_id, watch_position, completed}`), `PUT /<movie_id>/position`, `GET /continue-watching`, `GET` (full history), `DELETE /<movie_id>` — all require auth.

### Reviews — `/api/reviews`
`GET /movie/<movie_id>` (public), `POST`, `PUT /<id>`, `DELETE /<id>` (auth; owner or admin).

### Subscription — `/api/subscription`
`GET`, `POST /upgrade` (`{plan, months}`, mock payment), `POST /cancel`, `GET /status` — all require auth.

### Featured — `/api/featured`
`GET` — public, used by the homepage hero.

### Admin — `/api/admin` (all require an admin account)
`GET /dashboard`, `GET /users`, `PUT /users/<id>`, `DELETE /users/<id>`, `POST /movies`, `PUT /movies/<id>`, `DELETE /movies/<id>`, `GET /featured`, `POST /featured`, `PUT /featured/<id>`, `DELETE /featured/<id>`, `GET /analytics`.

## 8. Security notes

- Passwords are hashed with bcrypt; hashes are never returned by any API.
- JWT access tokens expire in 60 minutes by default (`JWT_ACCESS_EXPIRES_MIN`); logout revokes the current token via an in-memory blocklist (swap for Redis in production — see `utils/token_blocklist.py`).
- All database queries go through SQLAlchemy's ORM/parameter binding, which protects against SQL injection.
- `video_url` stores a reference to licensed storage (e.g. a CDN/HLS URL) — actual video files are never stored in the database.
- Set `CORS_ORIGINS` to your real frontend origin (not `*`) before deploying.
- Change `SECRET_KEY` and `JWT_SECRET_KEY` to long random values in production; never commit `.env`.

## 9. Project structure

```
charam_movies_backend/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── models/        (user, genre, movie, watchlist, history, review, subscription, featured, stream_event)
├── routes/        (auth, movies, genres, watchlist, history, reviews, streaming, subscription, admin, featured, users)
├── middleware/     (auth.py — @token_required, admin.py — @admin_required)
├── database/      (db.py, schema.sql, seed.py)
└── utils/         (jwt_utils, validators, responses, token_blocklist)
```
