"""Recreate the database with real Halifax restaurants (OpenStreetMap), demo users, reviews and Top 5 lists.

Restaurants are a hand-curated list of real Halifax-area places (data/halifax_restaurants.json,
built by scripts/build_seed_data.py). Member reviews and rankings are generated for the course demo.
Photos are representative Unsplash images by cuisine. Run with:  python seed.py
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from werkzeug.security import generate_password_hash

from db import get_db, init_db

DEMO_PASSWORD = "dinediscover"
DATA_PATH = Path(__file__).resolve().parent / "data" / "halifax_restaurants.json"

DEMO_USERS = ["priya", "sofia", "liam", "emma", "ahmed", "chen", "marcus"]

DISHES = {
    "indian": ["butter chicken", "lamb vindaloo", "chana masala", "biryani", "garlic naan", "palak paneer"],
    "italian": ["gnocchi", "margherita pizza", "carbonara", "tiramisu", "lasagna", "seafood linguine"],
    "japanese": ["spicy salmon roll", "tonkotsu ramen", "nigiri", "gyoza", "chirashi bowl", "karaage"],
    "chinese": ["ginger beef", "dim sum", "egg rolls", "General Tao chicken", "Singapore noodles", "dumplings"],
    "mexican": ["birria tacos", "carnitas", "burrito", "nachos", "fish tacos", "churros"],
    "thai": ["pad thai", "green curry", "tom yum", "massaman curry", "drunken noodles", "mango sticky rice"],
    "middle-eastern": ["donair", "chicken shawarma", "falafel", "fattoush", "garlic potatoes", "baklava"],
    "seafood": ["seafood chowder", "lobster roll", "fish and chips", "Malpeque oysters", "pan-fried haddock", "scallops"],
}
DISH_LINES = [
    "The {dish} was excellent.",
    "Had the {dish} and it was spot on.",
    "Their {dish} is the reason I keep coming back.",
    "The {dish} was good, though not the best I've had.",
]

PRAISE = {
    "taste": [
        "Every dish was full of flavour.",
        "The food was delicious and well seasoned.",
        "Flavours were balanced and fresh.",
        "Tasty, but a little uneven across dishes.",
    ],
    "service": [
        "Staff were friendly and quick.",
        "Service was warm and attentive.",
        "We waited a while, but the staff were kind.",
        "Service was efficient.",
    ],
    "value": [
        "Great value for the portion size.",
        "Prices are fair for the quality.",
        "A bit pricey, but worth it for a treat.",
        "Good portions for the price.",
    ],
}
CLOSERS = [
    "Would definitely come back.",
    "I'd recommend it to friends.",
    "A solid choice for this cuisine.",
    "Already planning my next visit.",
    "Worth a try if you're nearby.",
]


def _photo(photo_id: str) -> str:
    return f"https://images.unsplash.com/photo-{photo_id}?auto=format&fit=crop&w=900&q=70"


def _clamp(value):
    return max(1, min(5, round(value)))


def load_restaurants():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def seed_database():
    init_db()
    db = get_db()
    rng = random.Random(2026)
    rows = load_restaurants()

    user_ids = []
    for name in DEMO_USERS:
        cur = db.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (name, f"{name}@example.com", generate_password_hash(DEMO_PASSWORD)),
        )
        user_ids.append(cur.lastrowid)

    restaurants = []
    for row in rows:
        cur = db.execute(
            """INSERT INTO restaurants (name, cuisine, neighbourhood, address, lat, lng, price_level,
               dietary_tags, photo_url, photo_alt, description, hours, phone, website)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                row["name"],
                row["cuisine"],
                row["neighbourhood"],
                row["address"],
                row["lat"],
                row["lng"],
                row["price_level"],
                row["dietary"],
                _photo(row["photo_id"]),
                row["photo_alt"],
                row["description"],
                row["hours"],
                row.get("phone", ""),
                row.get("website", ""),
            ),
        )
        restaurants.append({"id": cur.lastrowid, "cuisine": row["cuisine"], "quality": row.get("quality", 4.0)})

    scores = {}
    for r in restaurants:
        for uid in rng.sample(user_ids, rng.randint(2, 6)):
            q = r["quality"]
            ratings = {k: _clamp(q + rng.uniform(-0.9, 0.7)) for k in ("taste", "service", "authenticity", "value")}
            overall = _clamp(sum(ratings.values()) / 4 + rng.uniform(-0.3, 0.3))
            body = " ".join(
                [
                    rng.choice(DISH_LINES).format(dish=rng.choice(DISHES[r["cuisine"]])),
                    rng.choice(PRAISE["taste"]),
                    rng.choice(PRAISE["service"]),
                    rng.choice(PRAISE["value"]),
                    rng.choice(CLOSERS),
                ]
            )
            days_ago = rng.randint(1, 240)
            db.execute(
                """INSERT INTO reviews (user_id, restaurant_id, taste, service, authenticity, value, overall, body, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now', ?))""",
                (uid, r["id"], *ratings.values(), overall, body, f"-{days_ago} days"),
            )
            scores[(uid, r["id"])] = overall + rng.uniform(0, 0.9)

    by_cuisine = {}
    for r in restaurants:
        by_cuisine.setdefault(r["cuisine"], []).append(r["id"])
    for uid in user_ids:
        for cuisine, ids in by_cuisine.items():
            ranked = sorted((rid for rid in ids if (uid, rid) in scores), key=lambda rid: -scores[(uid, rid)])
            if len(ranked) < 2 or rng.random() < 0.25:
                continue
            for rank, rid in enumerate(ranked[:5], start=1):
                db.execute(
                    "INSERT INTO top5_entries (user_id, cuisine, restaurant_id, rank) VALUES (?, ?, ?, ?)",
                    (uid, cuisine, rid, rank),
                )

    for uid in user_ids:
        for r in rng.sample(restaurants, 3):
            db.execute("INSERT INTO favorites (user_id, restaurant_id) VALUES (?, ?)", (uid, r["id"]))

    db.commit()
    return len(rows)


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        count = seed_database()
    print(f"Seeded {count} Halifax restaurants and {len(DEMO_USERS)} demo users (password: {DEMO_PASSWORD}).")
