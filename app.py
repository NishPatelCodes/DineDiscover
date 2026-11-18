import os
import secrets
from pathlib import Path

from flask import Flask, render_template

import db
import helpers


def _load_secret_key(instance_path):
    key_file = Path(instance_path) / "secret_key"
    if not key_file.exists():
        key_file.write_text(secrets.token_hex(32), encoding="utf-8")
    return key_file.read_text(encoding="utf-8").strip()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("DINEDISCOVER_SECRET_KEY") or _load_secret_key(app.instance_path),
        DATABASE=os.path.join(app.instance_path, "dinediscover.db"),
        SESSION_COOKIE_SAMESITE="Lax",
        CSRF_ENABLED=True,
        STYLEGUIDE=os.environ.get("DINEDISCOVER_STYLEGUIDE") == "1",
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    helpers.init_app(app)

    from routes import auth, me, restaurants, reviews, top5

    app.register_blueprint(auth.bp)
    app.register_blueprint(restaurants.bp)
    app.register_blueprint(reviews.bp)
    app.register_blueprint(me.bp)
    app.register_blueprint(top5.bp)

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(500)
    def handle_error(err):
        code = getattr(err, "code", 500)
        return render_template("error.html", code=code, description=getattr(err, "description", "")), code

    if not app.config.get("TESTING") and not os.path.exists(app.config["DATABASE"]):
        from seed import seed_database

        with app.app_context():
            seed_database()

    return app
