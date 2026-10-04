-- Charam Movies — MySQL schema
-- Run with:  mysql -u root -p charam_movies < database/schema.sql
-- (create the database first: CREATE DATABASE charam_movies CHARACTER SET utf8mb4;)

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ---------------------------------------------------------------- users
CREATE TABLE IF NOT EXISTS users (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    full_name          VARCHAR(120) NOT NULL,
    email              VARCHAR(190) NOT NULL UNIQUE,
    password_hash      VARCHAR(255) NOT NULL,
    role               ENUM('user','admin') NOT NULL DEFAULT 'user',
    subscription_type  ENUM('free','premium') NOT NULL DEFAULT 'free',
    is_active          TINYINT(1) NOT NULL DEFAULT 1,
    created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------- genres
CREATE TABLE IF NOT EXISTS genres (
    id     INT AUTO_INCREMENT PRIMARY KEY,
    name   VARCHAR(60) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------------- movies
CREATE TABLE IF NOT EXISTS movies (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    title         VARCHAR(200) NOT NULL,
    release_year  INT NOT NULL,
    rating        DECIMAL(3,1) NOT NULL DEFAULT 0,
    language      VARCHAR(60) NOT NULL,
    duration      INT NOT NULL,              -- minutes
    country       VARCHAR(80) NOT NULL,
    quality       ENUM('HD','4K') NOT NULL DEFAULT 'HD',
    description   TEXT,
    poster_url    VARCHAR(500),
    trailer_url   VARCHAR(500),
    video_url     VARCHAR(500),              -- licensed storage reference, not a file
    director      VARCHAR(150),
    cast_list     TEXT,                      -- comma separated cast names
    is_active     TINYINT(1) NOT NULL DEFAULT 1,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_movies_title (title),
    INDEX idx_movies_year (release_year),
    INDEX idx_movies_language (language),
    INDEX idx_movies_country (country)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------- movie_genres
CREATE TABLE IF NOT EXISTS movie_genres (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    movie_id   INT NOT NULL,
    genre_id   INT NOT NULL,
    UNIQUE KEY uq_movie_genre (movie_id, genre_id),
    CONSTRAINT fk_mg_movie FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
    CONSTRAINT fk_mg_genre FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------ watchlist
CREATE TABLE IF NOT EXISTS watchlist (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    movie_id    INT NOT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_user_movie_watchlist (user_id, movie_id),
    CONSTRAINT fk_wl_user  FOREIGN KEY (user_id)  REFERENCES users(id)  ON DELETE CASCADE,
    CONSTRAINT fk_wl_movie FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------- watch_history
CREATE TABLE IF NOT EXISTS watch_history (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT NOT NULL,
    movie_id       INT NOT NULL,
    watch_position INT NOT NULL DEFAULT 0,     -- seconds
    completed      TINYINT(1) NOT NULL DEFAULT 0,
    watched_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_user_movie_history (user_id, movie_id),
    CONSTRAINT fk_wh_user  FOREIGN KEY (user_id)  REFERENCES users(id)  ON DELETE CASCADE,
    CONSTRAINT fk_wh_movie FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -------------------------------------------------------------- reviews
CREATE TABLE IF NOT EXISTS reviews (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    movie_id     INT NOT NULL,
    rating       INT NOT NULL,
    review_text  TEXT,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_user_movie_review (user_id, movie_id),
    CONSTRAINT fk_rv_user  FOREIGN KEY (user_id)  REFERENCES users(id)  ON DELETE CASCADE,
    CONSTRAINT fk_rv_movie FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
    CONSTRAINT ck_review_rating_range CHECK (rating BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------- subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    user_id              INT NOT NULL UNIQUE,
    plan                 ENUM('free','premium') NOT NULL DEFAULT 'free',
    subscription_start   DATETIME,
    subscription_end     DATETIME,
    payment_status       ENUM('none','paid','cancelled','expired') NOT NULL DEFAULT 'none',
    created_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_sub_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------- featured_movies
CREATE TABLE IF NOT EXISTS featured_movies (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    movie_id       INT NOT NULL,
    display_order  INT NOT NULL DEFAULT 0,
    active         TINYINT(1) NOT NULL DEFAULT 1,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_feat_movie FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------- stream_events
CREATE TABLE IF NOT EXISTS stream_events (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    user_id           INT NOT NULL,
    movie_id          INT NOT NULL,
    started_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    duration_watched  INT NOT NULL DEFAULT 0,
    INDEX idx_stream_started (started_at),
    CONSTRAINT fk_se_user  FOREIGN KEY (user_id)  REFERENCES users(id)  ON DELETE CASCADE,
    CONSTRAINT fk_se_movie FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;
