CUISINES = [
    {"slug": "indian", "name": "Indian", "emoji": "\U0001F35B"},
    {"slug": "italian", "name": "Italian", "emoji": "\U0001F35D"},
    {"slug": "japanese", "name": "Japanese", "emoji": "\U0001F363"},
    {"slug": "chinese", "name": "Chinese", "emoji": "\U0001F95F"},
    {"slug": "mexican", "name": "Mexican", "emoji": "\U0001F32E"},
    {"slug": "thai", "name": "Thai", "emoji": "\U0001F35C"},
    {"slug": "middle-eastern", "name": "Middle Eastern", "emoji": "\U0001F9C6"},
    {"slug": "seafood", "name": "Seafood", "emoji": "\U0001F99E"},
]
CUISINE_BY_SLUG = {c["slug"]: c for c in CUISINES}

NEIGHBOURHOODS = {
    "downtown": {"name": "Downtown Halifax", "lat": 44.6488, "lng": -63.5752},
    "north-end": {"name": "North End", "lat": 44.6620, "lng": -63.5960},
    "south-end": {"name": "South End", "lat": 44.6370, "lng": -63.5800},
    "west-end": {"name": "West End", "lat": 44.6460, "lng": -63.6010},
    "dartmouth": {"name": "Dartmouth", "lat": 44.6656, "lng": -63.5670},
    "bedford": {"name": "Bedford", "lat": 44.7325, "lng": -63.6560},
    "clayton-park": {"name": "Clayton Park", "lat": 44.6600, "lng": -63.6450},
}
DEFAULT_NEAR = "downtown"

DIETARY = [
    ("vegetarian", "Vegetarian"),
    ("vegan", "Vegan"),
    ("halal", "Halal"),
    ("gluten-free", "Gluten-free"),
]
DIETARY_LABELS = dict(DIETARY)

PRICE_LABELS = {1: "Inexpensive", 2: "Moderate", 3: "Pricey", 4: "Very expensive"}

MIN_RATINGS = [("", "Any"), ("3", "3+"), ("4", "4+"), ("4.5", "4.5+")]

SORTS = [
    ("rating", "Highest rated"),
    ("reviews", "Most reviewed"),
    ("distance", "Nearest"),
    ("price_low", "Price: low to high"),
    ("price_high", "Price: high to low"),
]
SORT_LABELS = dict(SORTS)

MAX_DISTANCE_KM = 15

RATING_CATEGORIES = [
    ("taste", "Taste"),
    ("service", "Service"),
    ("authenticity", "Authenticity"),
    ("value", "Value"),
]

MAX_COMPARE = 3
TOP5_SIZE = 5
