DROP TABLE IF EXISTS top5_entries;
DROP TABLE IF EXISTS favorites;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS restaurants;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE restaurants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    cuisine TEXT NOT NULL,
    neighbourhood TEXT NOT NULL,
    address TEXT NOT NULL,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    price_level INTEGER NOT NULL CHECK (price_level BETWEEN 1 AND 4),
    dietary_tags TEXT NOT NULL DEFAULT '',
    photo_url TEXT NOT NULL,
    photo_alt TEXT NOT NULL,
    description TEXT NOT NULL,
    hours TEXT NOT NULL,
    phone TEXT NOT NULL DEFAULT '',
    website TEXT NOT NULL DEFAULT ''
);
CREATE INDEX idx_restaurants_cuisine ON restaurants (cuisine);

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants (id) ON DELETE CASCADE,
    taste INTEGER NOT NULL CHECK (taste BETWEEN 1 AND 5),
    service INTEGER NOT NULL CHECK (service BETWEEN 1 AND 5),
    authenticity INTEGER NOT NULL CHECK (authenticity BETWEEN 1 AND 5),
    value INTEGER NOT NULL CHECK (value BETWEEN 1 AND 5),
    overall INTEGER NOT NULL CHECK (overall BETWEEN 1 AND 5),
    body TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT,
    UNIQUE (user_id, restaurant_id)
);
CREATE INDEX idx_reviews_restaurant ON reviews (restaurant_id);

CREATE TABLE favorites (
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants (id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, restaurant_id)
);

CREATE TABLE top5_entries (
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    cuisine TEXT NOT NULL,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants (id) ON DELETE CASCADE,
    rank INTEGER NOT NULL CHECK (rank BETWEEN 1 AND 5),
    PRIMARY KEY (user_id, cuisine, rank),
    UNIQUE (user_id, cuisine, restaurant_id)
);
