from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

import constants
import services
from db import execute, query_one
from helpers import get_near, login_required

bp = Blueprint("reviews", __name__)

RATING_FIELDS = [*constants.RATING_CATEGORIES, ("overall", "Overall")]
BODY_MIN, BODY_MAX = 10, 1000


def _validate(form):
    values, errors = {}, {}
    for key, label in RATING_FIELDS:
        raw = form.get(key, "")
        if raw in ("1", "2", "3", "4", "5"):
            values[key] = int(raw)
        else:
            article = "an" if label[0] in "AEIOU" else "a"
            errors[key] = f"Choose {article} {label.lower()} rating from 1 to 5 stars."
    body = form.get("body", "").strip()
    values["body"] = body
    if len(body) < BODY_MIN:
        errors["body"] = f"Write at least {BODY_MIN} characters about your visit."
    elif len(body) > BODY_MAX:
        errors["body"] = f"Keep your review under {BODY_MAX} characters (currently {len(body)})."
    return values, errors


@bp.route("/restaurants/<int:rid>/review", methods=["GET", "POST"])
@login_required
def edit(rid):
    r = services.get_restaurant(rid, get_near())
    if r is None:
        abort(404, "We couldn't find that restaurant.")
    existing = query_one("SELECT * FROM reviews WHERE user_id = ? AND restaurant_id = ?", (g.user["id"], rid))
    values = dict(existing) if existing else {}
    errors = {}

    if request.method == "POST":
        values, errors = _validate(request.form)
        if not errors:
            fields = (values["taste"], values["service"], values["authenticity"], values["value"], values["overall"], values["body"])
            if existing:
                execute(
                    """UPDATE reviews SET taste = ?, service = ?, authenticity = ?, value = ?, overall = ?, body = ?,
                       updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
                    (*fields, existing["id"]),
                )
                flash("Your review was updated.", "success")
            else:
                execute(
                    """INSERT INTO reviews (user_id, restaurant_id, taste, service, authenticity, value, overall, body)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (g.user["id"], rid, *fields),
                )
                flash("Thanks! Your review was posted.", "success")
            return redirect(url_for("restaurants.detail", rid=rid) + "#reviews")

    status = 422 if errors else 200
    return render_template(
        "review_form.html",
        r=r,
        values=values,
        errors=errors,
        is_edit=existing is not None,
        rating_fields=RATING_FIELDS,
        body_min=BODY_MIN,
        body_max=BODY_MAX,
    ), status


@bp.route("/restaurants/<int:rid>/review/delete", methods=["POST"])
@login_required
def delete(rid):
    cur = execute("DELETE FROM reviews WHERE user_id = ? AND restaurant_id = ?", (g.user["id"], rid))
    flash("Your review was deleted." if cur.rowcount else "There was no review to delete.", "success" if cur.rowcount else "info")
    return redirect(url_for("restaurants.detail", rid=rid) + "#reviews")
