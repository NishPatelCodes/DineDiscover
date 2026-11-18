import re
import sqlite3

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import execute, query_one
from helpers import safe_next

bp = Blueprint("auth", __name__)

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _start_session(user_id):
    keep = {k: session[k] for k in ("near", "compare", "recent_views", "recent_searches") if k in session}
    session.clear()
    session.update(keep)
    session["user_id"] = user_id


@bp.route("/register", methods=["GET", "POST"])
def register():
    next_url = safe_next(request.values.get("next")) or url_for("restaurants.home")
    if g.user:
        return redirect(next_url)
    values, errors = {}, {}
    if request.method == "POST":
        values = {k: request.form.get(k, "").strip() for k in ("username", "email")}
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not values["username"]:
            errors["username"] = "Enter a username."
        elif not USERNAME_RE.match(values["username"]):
            errors["username"] = "Use 3 to 30 letters, numbers or underscores."
        elif query_one("SELECT 1 FROM users WHERE username = ?", (values["username"],)):
            errors["username"] = "That username is taken. Try another."

        if not values["email"]:
            errors["email"] = "Enter your email address."
        elif not EMAIL_RE.match(values["email"]):
            errors["email"] = "Enter an email address like name@example.com."
        elif query_one("SELECT 1 FROM users WHERE email = ?", (values["email"],)):
            errors["email"] = "An account with this email already exists. Try logging in."

        if len(password) < 8:
            errors["password"] = "Use at least 8 characters for your password."
        elif password != confirm:
            errors["confirm"] = "Passwords don't match."

        if not errors:
            try:
                cur = execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (values["username"], values["email"], generate_password_hash(password)),
                )
            except sqlite3.IntegrityError:
                errors["username"] = "That username or email is already registered."
            else:
                _start_session(cur.lastrowid)
                flash(f"Welcome to DineDiscover, {values['username']}!", "success")
                return redirect(next_url)
    status = 422 if errors else 200
    return render_template("register.html", values=values, errors=errors, next_url=next_url), status


@bp.route("/login", methods=["GET", "POST"])
def login():
    next_url = safe_next(request.values.get("next")) or url_for("restaurants.home")
    if g.user:
        return redirect(next_url)
    values, errors = {}, {}
    if request.method == "POST":
        values = {"login": request.form.get("login", "").strip()}
        password = request.form.get("password", "")
        if not values["login"]:
            errors["login"] = "Enter your username or email."
        if not password:
            errors["password"] = "Enter your password."
        if not errors:
            user = query_one(
                "SELECT id, username, password_hash FROM users WHERE username = ? OR email = ?",
                (values["login"], values["login"]),
            )
            if user and check_password_hash(user["password_hash"], password):
                _start_session(user["id"])
                flash(f"Welcome back, {user['username']}!", "success")
                return redirect(next_url)
            errors["form"] = "That username or password is incorrect. Check them and try again."
    status = 422 if errors else 200
    return render_template("login.html", values=values, errors=errors, next_url=next_url), status


@bp.route("/logout", methods=["POST"])
def logout():
    _start_session(None)
    session.pop("user_id", None)
    flash("You've been logged out.", "info")
    return redirect(url_for("restaurants.home"))
