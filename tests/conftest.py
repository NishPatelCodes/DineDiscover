import pytest

from app import create_app
from seed import seed_database


@pytest.fixture()
def app(tmp_path):
    db_path = tmp_path / "test.db"
    application = create_app(
        {
            "TESTING": True,
            "CSRF_ENABLED": False,
            "DATABASE": str(db_path),
            "SECRET_KEY": "test-secret",
            "STYLEGUIDE": True,
        }
    )
    with application.app_context():
        seed_database()
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def login(client):
    def _login(username="priya", password="dinediscover"):
        return client.post(
            "/login",
            data={"login": username, "password": password, "next": "/"},
            follow_redirects=False,
        )

    return _login
