import math

import constants
from db import query_all

_BASE_SQL = """
SELECT r.*,
       COUNT(v.id) AS review_count,
       AVG(v.overall) AS avg_overall,
       AVG(v.taste) AS avg_taste,
       AVG(v.service) AS avg_service,
       AVG(v.authenticity) AS avg_authenticity,
       AVG(v.value) AS avg_value
FROM restaurants r
LEFT JOIN reviews v ON v.restaurant_id = r.id
{where}
GROUP BY r.id
ORDER BY r.name
"""


def haversine_km(lat1, lng1, lat2, lng2):
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def _decorate(row, near):
    r = dict(row)
    r["dietary"] = [t for t in r["dietary_tags"].split(",") if t]
    r["cuisine_name"] = constants.CUISINE_BY_SLUG[r["cuisine"]]["name"]
    origin = constants.NEIGHBOURHOODS[near]
    r["distance_km"] = round(haversine_km(origin["lat"], origin["lng"], r["lat"], r["lng"]), 1)
    return r


def list_restaurants(near, where="", args=()):
    rows = query_all(_BASE_SQL.format(where=where), args)
    return [_decorate(row, near) for row in rows]


def get_restaurant(rid, near):
    rows = list_restaurants(near, "WHERE r.id = ?", (rid,))
    return rows[0] if rows else None


def get_restaurants_by_ids(ids, near):
    if not ids:
        return []
    marks = ",".join("?" * len(ids))
    by_id = {r["id"]: r for r in list_restaurants(near, f"WHERE r.id IN ({marks})", tuple(ids))}
    return [by_id[i] for i in ids if i in by_id]


def _rating(r):
    return r["avg_overall"] or 0


_SORT_KEYS = {
    "rating": lambda r: (-_rating(r), -r["review_count"], r["name"]),
    "reviews": lambda r: (-r["review_count"], -_rating(r), r["name"]),
    "distance": lambda r: (r["distance_km"], -_rating(r), r["name"]),
    "price_low": lambda r: (r["price_level"], -_rating(r), r["name"]),
    "price_high": lambda r: (-r["price_level"], -_rating(r), r["name"]),
}


def search_restaurants(filters, near):
    items = list_restaurants(near)
    q = filters["q"].lower()
    if q:
        items = [
            r
            for r in items
            if q in r["name"].lower()
            or q in r["cuisine_name"].lower()
            or q in r["description"].lower()
            or q in r["neighbourhood"].lower()
        ]
    if filters["cuisine"]:
        items = [r for r in items if r["cuisine"] == filters["cuisine"]]
    if filters["min_rating"]:
        items = [r for r in items if r["avg_overall"] and r["avg_overall"] >= filters["min_rating"]]
    if filters["prices"]:
        items = [r for r in items if r["price_level"] in filters["prices"]]
    if filters["diets"]:
        items = [r for r in items if all(d in r["dietary"] for d in filters["diets"])]
    if filters["max_km"]:
        items = [r for r in items if r["distance_km"] <= filters["max_km"]]
    items.sort(key=_SORT_KEYS.get(filters["sort"], _SORT_KEYS["rating"]))
    return items


def top_rated(near, limit=4):
    items = [r for r in list_restaurants(near) if r["review_count"]]
    items.sort(key=_SORT_KEYS["rating"])
    return items[:limit]


def cuisine_counts():
    return {row["cuisine"]: row["n"] for row in query_all("SELECT cuisine, COUNT(*) AS n FROM restaurants GROUP BY cuisine")}


def user_top5_ids(user_id, cuisine):
    rows = query_all(
        "SELECT restaurant_id FROM top5_entries WHERE user_id = ? AND cuisine = ? ORDER BY rank",
        (user_id, cuisine),
    )
    return [row["restaurant_id"] for row in rows]


def community_top5(cuisine, near):
    """Borda count: rank 1 earns 5 points down to rank 5 earning 1 point."""
    rows = query_all(
        """
        SELECT restaurant_id,
               SUM(6 - rank) AS points,
               COUNT(*) AS voters,
               SUM(CASE WHEN rank = 1 THEN 1 ELSE 0 END) AS first_place
        FROM top5_entries
        WHERE cuisine = ?
        GROUP BY restaurant_id
        """,
        (cuisine,),
    )
    stats = {row["restaurant_id"]: dict(row) for row in rows}
    restaurants = get_restaurants_by_ids(list(stats), near)
    for r in restaurants:
        r.update(points=stats[r["id"]]["points"], voters=stats[r["id"]]["voters"], first_place=stats[r["id"]]["first_place"])
    restaurants.sort(key=lambda r: (-r["points"], -_rating(r), r["name"]))
    return restaurants[: constants.TOP5_SIZE]


def community_voter_count(cuisine):
    return query_all("SELECT COUNT(DISTINCT user_id) AS n FROM top5_entries WHERE cuisine = ?", (cuisine,))[0]["n"]
