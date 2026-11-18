from flask import Blueprint, abort, flash, g, jsonify, render_template, request, session, url_for

import constants
import services
from db import execute, query_all, query_one
from helpers import compare_ids, compare_items, get_near, login_required, redirect_back, wants_json

bp = Blueprint("me", __name__)


def _restaurant_name(rid):
    row = query_one("SELECT name FROM restaurants WHERE id = ?", (rid,))
    if row is None:
        abort(404, "We couldn't find that restaurant.")
    return row["name"]


@bp.route("/favorites")
@login_required
def favorites():
    rows = query_all(
        "SELECT restaurant_id FROM favorites WHERE user_id = ? ORDER BY created_at DESC, rowid DESC",
        (g.user["id"],),
    )
    items = services.get_restaurants_by_ids([row["restaurant_id"] for row in rows], get_near())
    return render_template(
        "favorites.html",
        items=items,
        favorite_ids={r["id"] for r in items},
        compare_set=set(compare_ids()),
    )


@bp.route("/favorites/<int:rid>", methods=["POST"])
@login_required
def toggle_favorite(rid):
    name = _restaurant_name(rid)
    exists = bool(query_one("SELECT 1 FROM favorites WHERE user_id = ? AND restaurant_id = ?", (g.user["id"], rid)))
    wanted = request.form.get("favorite")
    favorited = (wanted == "1") if wanted in ("0", "1") else not exists

    if favorited and not exists:
        execute("INSERT INTO favorites (user_id, restaurant_id) VALUES (?, ?)", (g.user["id"], rid))
    elif not favorited and exists:
        execute("DELETE FROM favorites WHERE user_id = ? AND restaurant_id = ?", (g.user["id"], rid))

    message = f"Saved {name} to favorites." if favorited else f"Removed {name} from favorites."
    if wants_json():
        return jsonify(favorited=favorited, message=message, name=name)
    flash(message, "success")
    return redirect_back(url_for("me.favorites"))


@bp.route("/compare")
def compare():
    items = services.get_restaurants_by_ids(compare_ids(), get_near())
    best = {}
    if len(items) > 1:
        rated = [r for r in items if r["avg_overall"] is not None]
        for key in ("avg_overall", "avg_taste", "avg_service", "avg_authenticity", "avg_value"):
            if rated:
                top = max(r[key] for r in rated)
                best[key] = {r["id"] for r in rated if r[key] == top}
        best["price_level"] = {r["id"] for r in items if r["price_level"] == min(i["price_level"] for i in items)}
        best["distance_km"] = {r["id"] for r in items if r["distance_km"] == min(i["distance_km"] for i in items)}
        best["review_count"] = {r["id"] for r in items if r["review_count"] == max(i["review_count"] for i in items) and r["review_count"]}
    return render_template("compare.html", items=items, best=best)


@bp.route("/compare/<int:rid>", methods=["POST"])
def toggle_compare(rid):
    name = _restaurant_name(rid)
    ids = compare_ids()
    wanted = request.form.get("compare")
    add = (wanted == "1") if wanted in ("0", "1") else rid not in ids

    if add and rid not in ids:
        if len(ids) >= constants.MAX_COMPARE:
            message = f"You can compare up to {constants.MAX_COMPARE} restaurants. Remove one first."
            if wants_json():
                return jsonify(error=message, items=compare_items()), 409
            flash(message, "error")
            return redirect_back(url_for("me.compare"))
        ids.append(rid)
        message = f"Added {name} to compare."
    elif not add and rid in ids:
        ids.remove(rid)
        message = f"Removed {name} from compare."
    else:
        message = f"{name} is {'already' if add else 'not'} in compare."
    session["compare"] = ids

    if wants_json():
        return jsonify(in_compare=rid in ids, message=message, items=compare_items(), compare_url=url_for("me.compare"))
    flash(message, "success")
    return redirect_back(url_for("me.compare"))


@bp.route("/compare/clear", methods=["POST"])
def clear_compare():
    session["compare"] = []
    flash("Cleared your comparison.", "info")
    return redirect_back(url_for("restaurants.home"))
