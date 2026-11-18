from flask import Blueprint, abort, current_app, g, render_template, request, session, url_for

import constants
import services
from db import query_all, query_one
from helpers import compare_ids, get_near, set_near

bp = Blueprint("restaurants", __name__)

MAX_RECENT_VIEWS = 6
MAX_RECENT_SEARCHES = 5


def _float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_filters(args):
    cuisine = args.get("cuisine", "")
    min_rating = _float(args.get("min_rating"))
    max_km = _float(args.get("max_km"))
    sort = args.get("sort", "rating")
    return {
        "q": args.get("q", "").strip()[:80],
        "cuisine": cuisine if cuisine in constants.CUISINE_BY_SLUG else "",
        "min_rating": min_rating if min_rating and 0 < min_rating <= 5 else None,
        "prices": sorted({int(p) for p in args.getlist("price") if p in ("1", "2", "3", "4")}),
        "diets": [d for d, _ in constants.DIETARY if d in args.getlist("diet")],
        "max_km": max_km if max_km and 0 < max_km < constants.MAX_DISTANCE_KM else None,
        "sort": sort if sort in constants.SORT_LABELS else "rating",
    }


def filters_to_args(f, near):
    args = {"near": near}
    if f["q"]:
        args["q"] = f["q"]
    if f["cuisine"]:
        args["cuisine"] = f["cuisine"]
    if f["min_rating"]:
        args["min_rating"] = f"{f['min_rating']:g}"
    if f["prices"]:
        args["price"] = [str(p) for p in f["prices"]]
    if f["diets"]:
        args["diet"] = list(f["diets"])
    if f["max_km"]:
        args["max_km"] = f"{f['max_km']:g}"
    if f["sort"] != "rating":
        args["sort"] = f["sort"]
    return args


def active_chips(f, near):
    """Removable chips describing each active filter, each linking to the results without it."""
    base = filters_to_args(f, near)
    chips = []

    def without(key, value=None):
        args = {k: (list(v) if isinstance(v, list) else v) for k, v in base.items()}
        if value is None:
            args.pop(key, None)
        else:
            args[key] = [v for v in args[key] if v != value]
        return url_for("restaurants.search", **args)

    if f["q"]:
        chips.append({"label": f"\u201c{f['q']}\u201d", "kind": "Search", "url": without("q")})
    if f["cuisine"]:
        chips.append({"label": constants.CUISINE_BY_SLUG[f["cuisine"]]["name"], "kind": "Cuisine", "url": without("cuisine")})
    if f["min_rating"]:
        chips.append({"label": f"{f['min_rating']:g}+ stars", "kind": "Rating", "url": without("min_rating")})
    for p in f["prices"]:
        chips.append({"label": "$" * p, "sr": constants.PRICE_LABELS[p], "kind": "Price", "url": without("price", str(p))})
    for d in f["diets"]:
        chips.append({"label": constants.DIETARY_LABELS[d], "kind": "Dietary", "url": without("diet", d)})
    if f["max_km"]:
        chips.append({"label": f"Within {f['max_km']:g} km", "kind": "Distance", "url": without("max_km")})
    return chips


def _remember_search(f, near):
    if not (f["q"] or f["cuisine"]):
        return
    what = constants.CUISINE_BY_SLUG[f["cuisine"]]["name"] if f["cuisine"] else f"\u201c{f['q']}\u201d"
    if f["q"] and f["cuisine"]:
        what = f"{what} \u00b7 \u201c{f['q']}\u201d"
    entry = {"label": f"{what} near {constants.NEIGHBOURHOODS[near]['name']}",
             "url": url_for("restaurants.search", **filters_to_args(f, near))}
    recent = [s for s in session.get("recent_searches", []) if s["label"] != entry["label"]]
    session["recent_searches"] = [entry, *recent][:MAX_RECENT_SEARCHES]


def _favorite_ids():
    if not g.user:
        return set()
    return {r["restaurant_id"] for r in query_all("SELECT restaurant_id FROM favorites WHERE user_id = ?", (g.user["id"],))}


@bp.route("/")
def home():
    near = get_near()
    recent_ids = session.get("recent_views", [])
    return render_template(
        "home.html",
        counts=services.cuisine_counts(),
        top_rated=services.top_rated(near),
        recent_views=services.get_restaurants_by_ids(recent_ids, near),
        recent_searches=session.get("recent_searches", []),
        favorite_ids=_favorite_ids(),
        compare_set=set(compare_ids()),
    )


@bp.route("/search")
def search():
    near = set_near(request.args.get("near", "")) if request.args.get("near") else get_near()
    f = parse_filters(request.args)
    results = services.search_restaurants(f, near)
    _remember_search(f, near)
    context = {
        "filters": f,
        "results": results,
        "chips": active_chips(f, near),
        "clear_url": url_for("restaurants.search", near=near),
        "near": near,
        "favorite_ids": _favorite_ids(),
        "compare_set": set(compare_ids()),
    }
    if request.args.get("partial") == "1":
        return render_template("_results.html", **context)
    return render_template("results.html", **context)


@bp.route("/restaurants/<int:rid>")
def detail(rid):
    near = get_near()
    r = services.get_restaurant(rid, near)
    if r is None:
        abort(404, "We couldn't find that restaurant.")

    recent = [i for i in session.get("recent_views", []) if i != rid]
    session["recent_views"] = [rid, *recent][:MAX_RECENT_VIEWS]

    reviews = query_all(
        """SELECT v.*, u.username FROM reviews v JOIN users u ON u.id = v.user_id
           WHERE v.restaurant_id = ? ORDER BY COALESCE(v.updated_at, v.created_at) DESC""",
        (rid,),
    )
    user_review, is_favorite, top5_ids = None, False, []
    if g.user:
        user_review = next((v for v in reviews if v["user_id"] == g.user["id"]), None)
        is_favorite = bool(query_one("SELECT 1 FROM favorites WHERE user_id = ? AND restaurant_id = ?", (g.user["id"], rid)))
        top5_ids = services.user_top5_ids(g.user["id"], r["cuisine"])
    top5_rank = top5_ids.index(rid) + 1 if rid in top5_ids else None

    return render_template(
        "restaurant.html",
        r=r,
        reviews=reviews,
        user_review=user_review,
        is_favorite=is_favorite,
        in_compare=rid in compare_ids(),
        top5_rank=top5_rank,
        top5_full=len(top5_ids) >= constants.TOP5_SIZE,
    )


@bp.route("/styleguide")
def styleguide():
    if not (current_app.debug or current_app.config.get("STYLEGUIDE")):
        abort(404)
    sample = services.top_rated(get_near(), limit=1)
    return render_template("styleguide.html", sample=sample[0] if sample else None, favorite_ids=set(), compare_set=set())
