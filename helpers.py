import functools
import secrets
from urllib.parse import urlsplit

from flask import (
    abort,
    current_app,
    flash,
    g,
    jsonify,
    redirect,
    request,
    session,
    url_for,
)

import constants
from db import query_all, query_one


def wants_json():
    return request.headers.get("X-Requested-With") == "fetch" or request.is_json


def safe_next(target):
    """Return target only if it is a local path, to prevent open redirects."""
    if not target or not target.startswith("/") or target.startswith("//") or "\\" in target:
        return None
    return target.rstrip("?") or "/"


def referrer_path():
    ref = request.referrer
    if not ref:
        return None
    parts = urlsplit(ref)
    if parts.netloc and parts.netloc != request.host:
        return None
    return safe_next(parts.path + (f"?{parts.query}" if parts.query else ""))


def current_path():
    return safe_next(request.full_path) or "/"


def redirect_back(default="/"):
    return redirect(safe_next(request.form.get("next")) or referrer_path() or default)


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            if request.method == "GET":
                next_target = current_path()
            else:
                next_target = safe_next(request.form.get("next")) or referrer_path() or "/"
            login_url = url_for("auth.login", next=next_target)
            if wants_json():
                return jsonify(error="Please log in first.", login_url=login_url), 401
            flash("Please log in to continue.", "info")
            return redirect(login_url)
        return view(*args, **kwargs)

    return wrapped


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def _load_user():
    uid = session.get("user_id")
    g.user = query_one("SELECT id, username, email FROM users WHERE id = ?", (uid,)) if uid else None
    if uid and g.user is None:
        session.pop("user_id", None)


def _csrf_protect():
    if not current_app.config.get("CSRF_ENABLED", True):
        return None
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return None
    sent = request.form.get("csrf_token") or request.headers.get("X-CSRFToken", "")
    expected = session.get("_csrf", "")
    if not sent or not expected or not secrets.compare_digest(sent, expected):
        message = "Your session expired. Refresh the page and try again."
        if wants_json():
            return jsonify(error=message), 400
        abort(400, message)
    return None


def get_near():
    near = session.get("near", constants.DEFAULT_NEAR)
    return near if near in constants.NEIGHBOURHOODS else constants.DEFAULT_NEAR


def set_near(value):
    if value in constants.NEIGHBOURHOODS:
        session["near"] = value
        return value
    return get_near()


def compare_ids():
    return [int(i) for i in session.get("compare", [])][: constants.MAX_COMPARE]


def compare_items():
    ids = compare_ids()
    if not ids:
        return []
    marks = ",".join("?" * len(ids))
    rows = {r["id"]: r for r in query_all(f"SELECT id, name FROM restaurants WHERE id IN ({marks})", ids)}
    return [{"id": i, "name": rows[i]["name"]} for i in ids if i in rows]


def _inject_globals():
    return {
        "current_user": g.get("user"),
        "csrf_token": csrf_token,
        "current_path": current_path,
        "C": constants,
        "near": get_near(),
        "compare_items": compare_items(),
    }


def format_price(level):
    return "$" * int(level or 0)


def format_rating(value):
    return f"{value:.1f}" if value is not None else "–"


def format_km(value):
    return f"{value:.1f} km"


def init_app(app):
    app.before_request(_load_user)
    app.before_request(_csrf_protect)
    app.context_processor(_inject_globals)
    app.jinja_env.filters["price"] = format_price
    app.jinja_env.filters["rating"] = format_rating
    app.jinja_env.filters["km"] = format_km
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
