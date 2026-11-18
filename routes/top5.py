from flask import Blueprint, abort, flash, g, jsonify, redirect, render_template, request, url_for

import constants
import services
from db import get_db, query_all
from helpers import get_near, login_required, redirect_back, wants_json

bp = Blueprint("top5", __name__, url_prefix="/top5")


def _check_cuisine(cuisine):
    if cuisine not in constants.CUISINE_BY_SLUG:
        abort(404, "That cuisine doesn't exist.")
    return constants.CUISINE_BY_SLUG[cuisine]


def _save_order(user_id, cuisine, ids):
    db = get_db()
    db.execute("DELETE FROM top5_entries WHERE user_id = ? AND cuisine = ?", (user_id, cuisine))
    db.executemany(
        "INSERT INTO top5_entries (user_id, cuisine, restaurant_id, rank) VALUES (?, ?, ?, ?)",
        [(user_id, cuisine, rid, rank) for rank, rid in enumerate(ids, start=1)],
    )
    db.commit()


def _cuisine_restaurant_ids(cuisine):
    return {row["id"] for row in query_all("SELECT id FROM restaurants WHERE cuisine = ?", (cuisine,))}


def _respond(cuisine, message, category="success", status=200):
    if wants_json():
        payload = {"order": services.user_top5_ids(g.user["id"], cuisine), "message": message}
        if status >= 400:
            payload["error"] = message
        return jsonify(payload), status
    flash(message, category)
    return redirect_back(url_for("top5.mine", cuisine=cuisine))


@bp.route("/")
@login_required
def mine():
    cuisine = request.args.get("cuisine") or "indian"
    info = _check_cuisine(cuisine)
    near = get_near()
    ids = services.user_top5_ids(g.user["id"], cuisine)
    entries = services.get_restaurants_by_ids(ids, near)
    available = [r for r in services.list_restaurants(near, "WHERE r.cuisine = ?", (cuisine,)) if r["id"] not in ids]
    lists = {
        row["cuisine"]: row["n"]
        for row in query_all("SELECT cuisine, COUNT(*) AS n FROM top5_entries WHERE user_id = ? GROUP BY cuisine", (g.user["id"],))
    }
    return render_template("top5.html", cuisine=cuisine, info=info, entries=entries, available=available, lists=lists)


@bp.route("/<cuisine>/add", methods=["POST"])
@login_required
def add(cuisine):
    info = _check_cuisine(cuisine)
    rid = request.form.get("restaurant_id", type=int)
    ids = services.user_top5_ids(g.user["id"], cuisine)
    if rid not in _cuisine_restaurant_ids(cuisine):
        return _respond(cuisine, f"Choose a {info['name']} restaurant to add.", "error", 400)
    if rid in ids:
        return _respond(cuisine, f"That restaurant is already #{ids.index(rid) + 1} in your list.", "info")
    if len(ids) >= constants.TOP5_SIZE:
        return _respond(cuisine, "Your Top 5 is full. Remove a restaurant before adding another.", "error", 409)
    _save_order(g.user["id"], cuisine, [*ids, rid])
    name = query_all("SELECT name FROM restaurants WHERE id = ?", (rid,))[0]["name"]
    return _respond(cuisine, f"Added {name} at #{len(ids) + 1} in your Top 5 {info['name']}.")


@bp.route("/<cuisine>/move", methods=["POST"])
@login_required
def move(cuisine):
    _check_cuisine(cuisine)
    rid = request.form.get("restaurant_id", type=int)
    direction = request.form.get("direction")
    ids = services.user_top5_ids(g.user["id"], cuisine)
    if rid not in ids or direction not in ("up", "down"):
        return _respond(cuisine, "That move isn't possible.", "error", 400)
    i = ids.index(rid)
    j = i - 1 if direction == "up" else i + 1
    if 0 <= j < len(ids):
        ids[i], ids[j] = ids[j], ids[i]
        _save_order(g.user["id"], cuisine, ids)
    return _respond(cuisine, f"Moved to #{ids.index(rid) + 1}.")


@bp.route("/<cuisine>/remove", methods=["POST"])
@login_required
def remove(cuisine):
    _check_cuisine(cuisine)
    rid = request.form.get("restaurant_id", type=int)
    ids = services.user_top5_ids(g.user["id"], cuisine)
    if rid in ids:
        ids.remove(rid)
        _save_order(g.user["id"], cuisine, ids)
    return _respond(cuisine, "Removed from your Top 5.")


@bp.route("/<cuisine>/order", methods=["POST"])
@login_required
def order(cuisine):
    _check_cuisine(cuisine)
    payload = request.get_json(silent=True) or {}
    raw = payload.get("order")
    if not isinstance(raw, list) or not all(isinstance(i, int) for i in raw):
        return jsonify(error="Invalid order."), 400
    if len(raw) > constants.TOP5_SIZE or len(set(raw)) != len(raw) or not set(raw) <= _cuisine_restaurant_ids(cuisine):
        return jsonify(error="That list can't be saved. Refresh the page and try again."), 400
    _save_order(g.user["id"], cuisine, raw)
    return jsonify(order=raw, message="Saved")


@bp.route("/community")
def community():
    near = get_near()
    boards = [
        {"cuisine": c, "entries": services.community_top5(c["slug"], near), "voters": services.community_voter_count(c["slug"])}
        for c in constants.CUISINES
    ]
    selected = request.args.get("cuisine")
    if selected not in constants.CUISINE_BY_SLUG:
        selected = constants.CUISINES[0]["slug"]
    return render_template("community_top5.html", boards=boards, selected=selected)
