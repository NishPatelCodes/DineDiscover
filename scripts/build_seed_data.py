"""Turn Overpass OSM data into a curated ~50-restaurant seed JSON for DineDiscover."""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "instance" / "osm_raw.json"
OUT = ROOT / "data" / "halifax_restaurants.json"

NEIGHBOURHOODS = {
    "Downtown Halifax": (44.6488, -63.5752),
    "North End": (44.6620, -63.5960),
    "South End": (44.6370, -63.5800),
    "Dartmouth": (44.6656, -63.5670),
    "Bedford": (44.7325, -63.6560),
    "Clayton Park": (44.6600, -63.6450),
}

# OSM cuisine token -> our slug. First matching token wins.
CUISINE_MAP = [
    ("indian", "indian"),
    ("italian", "italian"),
    ("pizza", "italian"),
    ("japanese", "japanese"),
    ("sushi", "japanese"),
    ("ramen", "japanese"),
    ("chinese", "chinese"),
    ("mexican", "mexican"),
    ("thai", "thai"),
    ("lebanese", "middle-eastern"),
    ("turkish", "middle-eastern"),
    ("kebab", "middle-eastern"),
    ("middle_eastern", "middle-eastern"),
    ("falafel", "middle-eastern"),
    ("seafood", "seafood"),
    ("fish_and_chips", "seafood"),
    ("fish", "seafood"),
]

PHOTO_BY_CUISINE = {
    "indian": [
        ("1585937421612-70a008356fbe", "Bowls of Indian curries garnished with herbs"),
        ("1565557623262-b51c2513a641", "Chicken curry with garlic naan"),
        ("1601050690597-df0568f70950", "Crispy samosas with green chilies"),
        ("1588166524941-3bf61a9c41db", "Paneer curry topped with fresh herbs"),
        ("1546833999-b9f581a1996d", "Biryani rice dish with spices"),
        ("1517248135467-4c7edcad34c4", "Restaurant dining room with warm lighting"),
    ],
    "italian": [
        ("1621996346565-e3dbc646d9a9", "Penne pasta in tomato sauce"),
        ("1574071318508-1cdbab80d002", "Wood-fired pizza with basil"),
        ("1595295333158-4742f28fbd85", "Spaghetti with seafood"),
        ("1551183053-bf91a1d81141", "Fresh pasta and sauce"),
        ("1414235077428-338989a2e8c0", "Restaurant table with Italian food"),
        ("1476224203421-9ac39bcb3327", "Pizza on a wooden board"),
    ],
    "japanese": [
        ("1611143669185-af224c5e3252", "Assorted sushi rolls and nigiri"),
        ("1569718212165-3a8278d5f624", "Ramen bowl with egg and green onions"),
        ("1617196034796-73dfa7b1fd56", "Nigiri sushi on a slate"),
        ("1579871494447-9811cf80d66c", "Sushi platter"),
        ("1553621042-f6e147245754", "Japanese restaurant dishes"),
        ("1611143669185-af224c5e3252", "Assorted sushi"),
    ],
    "chinese": [
        ("1563245372-f21724e3856d", "Steamed dumplings in bamboo baskets"),
        ("1585032226651-759b368d7246", "Stir-fried noodles with chopsticks"),
        ("1496116218417-1a781b1c416c", "Pan-fried dumplings"),
        ("1525755662778-989d0522089b", "Chinese takeout dishes"),
        ("1563379926898-05f4575a45d8", "Asian noodle soup"),
        ("1544025162-d76694265947", "Shared plates on a restaurant table"),
    ],
    "mexican": [
        ("1565299585323-38d6b0865b47", "Soft tacos with cilantro"),
        ("1599974579688-8dbdd335c77f", "Colourful vegetable tacos"),
        ("1626700051175-6818013e1d4f", "Burrito cut in half"),
        ("1552332386-f8dd00dc2f85", "Mexican street food"),
        ("1513456852971-30c0b8199d4d", "Tacos and salsa"),
        ("1504674900247-0877df9cc836", "Restaurant meal spread"),
    ],
    "thai": [
        ("1559314809-0d155014e29e", "Thai green curry with rice"),
        ("1562565652-a0d8f0c59eb4", "Pad Thai noodles"),
        ("1455619452474-d2be8b1e70cd", "Thai soup with herbs"),
        ("1546069901-ba9599a7e63c", "Colourful plated meal"),
        ("1512058561765-5d4a8b9c0f1a", "Asian noodle dish"),
        ("1476224203421-9ac39bcb3327", "Shared restaurant plates"),
    ],
    "middle-eastern": [
        ("1529006557811-74b19280a4dc", "Shawarma wrap and sides"),
        ("1544025162-d76694265947", "Grill platter with salads"),
        ("1601050690597-df0568f70950", "Fried appetizers with dips"),
        ("1555939594-58d7cb561ad1", "Burger-style wrap meal"),
        ("1517248135467-4c7edcad34c4", "Warm restaurant interior"),
        ("1414235077428-338989a2e8c0", "Restaurant table setting"),
    ],
    "seafood": [
        ("1559339352-11d035aa65de", "Lobster dinner"),
        ("1559847844-5315695dadae", "Fish and chips"),
        ("1467003909585-2f5a4ba7b0f0", "Seafood platter"),
        ("1565299624946-b28f40a0ae38", "Fresh cooked seafood"),
        ("1476224203421-9ac39bcb3327", "Restaurant seafood dishes"),
        ("1414235077428-338989a2e8c0", "Fine dining table"),
    ],
}

TARGET_PER = {
    "indian": 7,
    "italian": 7,
    "japanese": 7,
    "chinese": 6,
    "mexican": 6,
    "thai": 5,
    "middle-eastern": 6,
    "seafood": 6,
}


def haversine(lat1, lng1, lat2, lng2):
    r = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_hood(lat, lng):
    return min(NEIGHBOURHOODS.items(), key=lambda kv: haversine(lat, lng, kv[1][0], kv[1][1]))[0]


def map_cuisine(raw: str | None) -> str | None:
    if not raw:
        return None
    tokens = [t.strip().lower().replace(" ", "_") for t in raw.replace(",", ";").split(";")]
    for token in tokens:
        for needle, slug in CUISINE_MAP:
            if needle in token:
                return slug
    return None


def coords(el):
    if "lat" in el and "lon" in el:
        return el["lat"], el["lon"]
    c = el.get("center") or {}
    if "lat" in c and "lon" in c:
        return c["lat"], c["lon"]
    return None


def address(tags):
    parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
    ]
    line = " ".join(p for p in parts if p)
    if not line:
        line = tags.get("addr:full") or tags.get("addr:place") or "Halifax, NS"
    return line


def dietary(tags, cuisine):
    labels = []
    if tags.get("diet:vegetarian") in ("yes", "only") or tags.get("vegetarian") == "yes":
        labels.append("vegetarian")
    if tags.get("diet:vegan") in ("yes", "only") or tags.get("vegan") == "yes":
        labels.append("vegan")
    if tags.get("diet:halal") in ("yes", "only") or tags.get("halal") == "yes":
        labels.append("halal")
    if tags.get("diet:gluten_free") in ("yes", "only"):
        labels.append("gluten-free")
    # Light defaults so filters stay useful when OSM lacks diet tags.
    if not labels:
        defaults = {
            "indian": ["vegetarian", "vegan", "halal"],
            "italian": ["vegetarian"],
            "japanese": ["gluten-free"],
            "chinese": ["vegetarian", "vegan"],
            "mexican": ["vegetarian", "gluten-free"],
            "thai": ["vegetarian", "vegan", "gluten-free"],
            "middle-eastern": ["vegetarian", "halal"],
            "seafood": ["gluten-free"],
        }
        labels = defaults.get(cuisine, [])[:3]
    return ",".join(labels)


def price_level(tags, cuisine):
    raw = (tags.get("price") or tags.get("price_range") or "").strip()
    if raw in ("$", "1", "cheap"):
        return 1
    if raw in ("$$", "2", "moderate"):
        return 2
    if raw in ("$$$", "3"):
        return 3
    if raw in ("$$$$", "4"):
        return 4
    return {"seafood": 3, "japanese": 3, "italian": 2, "indian": 2}.get(cuisine, 2)


def description(name, cuisine, hood, tags):
    cuisine_names = {
        "indian": "Indian",
        "italian": "Italian",
        "japanese": "Japanese",
        "chinese": "Chinese",
        "mexican": "Mexican",
        "thai": "Thai",
        "middle-eastern": "Middle Eastern",
        "seafood": "seafood",
    }
    label = cuisine_names[cuisine]
    extra = tags.get("cuisine", "").replace("_", " ").replace(";", ", ")
    base = f"{name} is a {label} restaurant in {hood}."
    if extra and extra.lower() not in label.lower():
        base += f" OpenStreetMap lists cuisine as {extra}."
    if tags.get("outdoor_seating") == "yes":
        base += " Outdoor seating available."
    if tags.get("takeaway") == "yes":
        base += " Takeaway offered."
    return base


def hours(tags):
    return tags.get("opening_hours") or "Hours vary — check before you go"


def phone(tags):
    return tags.get("phone") or tags.get("contact:phone") or ""


def main():
    rng = random.Random(2026)
    data = json.loads(RAW.read_text(encoding="utf-8"))
    buckets = {slug: [] for slug in TARGET_PER}

    seen_names = set()
    for el in data["elements"]:
        tags = el.get("tags") or {}
        name = (tags.get("name") or "").strip()
        if not name or name.lower() in seen_names:
            continue
        loc = coords(el)
        if not loc:
            continue
        cuisine = map_cuisine(tags.get("cuisine"))
        if not cuisine:
            continue
        lat, lng = loc
        hood = nearest_hood(lat, lng)
        item = {
            "name": name,
            "cuisine": cuisine,
            "neighbourhood": hood,
            "address": address(tags),
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "price_level": price_level(tags, cuisine),
            "dietary": dietary(tags, cuisine),
            "phone": phone(tags),
            "hours": hours(tags),
            "description": description(name, cuisine, hood, tags),
            "osm_id": f"{el['type']}/{el['id']}",
            "website": tags.get("website") or tags.get("contact:website") or "",
        }
        buckets[cuisine].append(item)
        seen_names.add(name.lower())

    chosen = []
    for slug, target in TARGET_PER.items():
        pool = buckets[slug]
        # Prefer places with a street address, then shuffle stably.
        pool.sort(key=lambda r: (0 if "St" in r["address"] or "Rd" in r["address"] or "Ave" in r["address"] or "Dr" in r["address"] else 1, r["name"]))
        # Spread across neighbourhoods when possible.
        by_hood = {}
        for r in pool:
            by_hood.setdefault(r["neighbourhood"], []).append(r)
        picked = []
        while len(picked) < target and any(by_hood.values()):
            for hood in list(by_hood.keys()):
                if len(picked) >= target:
                    break
                if by_hood[hood]:
                    picked.append(by_hood[hood].pop(0))
                if not by_hood[hood]:
                    del by_hood[hood]
        # Fill leftovers if neighbourhood spread ran out.
        remaining = [r for r in pool if r not in picked]
        rng.shuffle(remaining)
        while len(picked) < target and remaining:
            picked.append(remaining.pop())
        for i, r in enumerate(picked):
            photos = PHOTO_BY_CUISINE[slug]
            photo_id, alt = photos[i % len(photos)]
            r["photo_id"] = photo_id
            r["photo_alt"] = alt
            # Synthetic review quality bias for demo rankings (not a real star rating).
            r["quality"] = round(3.6 + (hash(r["name"]) % 12) / 10, 1)
        chosen.extend(picked)

    chosen.sort(key=lambda r: (r["cuisine"], r["name"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(chosen, indent=2), encoding="utf-8")
    print(f"wrote {len(chosen)} restaurants to {OUT}")
    counts = {}
    for r in chosen:
        counts[r["cuisine"]] = counts.get(r["cuisine"], 0) + 1
    print(counts)
    for r in chosen[:5]:
        print("-", r["name"], r["cuisine"], r["neighbourhood"], r["address"])


if __name__ == "__main__":
    main()
