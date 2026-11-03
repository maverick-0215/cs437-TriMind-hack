import pytest
from flask import g

from app import create_app, db
from app.models import Claim, FoundItem, LostReport

ADMIN_EMAIL = "guard@iitgn.ac.in"
PASSWORD = "secret123"


@pytest.fixture
def app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",  # fresh in-memory DB per test
            "ADMIN_EMAILS": ADMIN_EMAIL,
            "UPLOAD_FOLDER": str(tmp_path),
        }
    )

    # Tests keep one app context open so they can query the DB between requests.
    # Flask reuses that context (and its `g`) for every request, and Flask-Login
    # caches the logged-in user on `g`. Clear it so each client is seen as itself.
    # It must run before the app's own login check, so it goes first in the list.
    def _forget_cached_user():
        g.pop("_login_user", None)

    app.before_request_funcs.setdefault(None, []).insert(0, _forget_cached_user)

    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()


def signed_up_client(app, email, name=None):
    """A test client that has signed up (and is therefore logged in) as `email`."""
    client = app.test_client()
    resp = client.post(
        "/signup", data={"name": name or email.split("@")[0], "email": email, "password": PASSWORD}
    )
    assert resp.status_code == 302, resp.get_data(as_text=True)
    return client


@pytest.fixture
def anon(app):
    return app.test_client()


@pytest.fixture
def admin(app):
    return signed_up_client(app, ADMIN_EMAIL, "Guard")


@pytest.fixture
def student(app):
    return signed_up_client(app, "asha@iitgn.ac.in", "Asha")


@pytest.fixture
def other(app):
    return signed_up_client(app, "ravi@iitgn.ac.in", "Ravi")


ITEM_DEFAULTS = {
    "category": "Bottle",
    "title": "Steel bottle",
    "date_found": "2026-10-03",
    "general_area": "Library",
    "exact_location": "SECRET-LOCATION table 4",
    "description": "SECRET-DESCRIPTION blue sticker",
}


@pytest.fixture
def add_item(admin):
    """Add a found item as admin through the real form. Returns the FoundItem."""

    def _add(**overrides):
        data = {**ITEM_DEFAULTS, **overrides}
        resp = admin.post("/admin/items/new", data=data, content_type="multipart/form-data")
        assert resp.status_code == 302, resp.get_data(as_text=True)
        return FoundItem.query.order_by(FoundItem.id.desc()).first()

    return _add


REPORT_DEFAULTS = {
    "category": "Bottle",
    "title": "My blue bottle",
    "date_lost": "2026-10-02",
    "place_lost": "Library",
    "private_details": "PRIVATE-REPORT scratch near cap",
}


@pytest.fixture
def add_report():
    """File a lost report as the given client. Returns the LostReport."""

    def _add(client, **overrides):
        resp = client.post("/reports/new", data={**REPORT_DEFAULTS, **overrides})
        assert resp.status_code == 302, resp.get_data(as_text=True)
        return LostReport.query.order_by(LostReport.id.desc()).first()

    return _add


@pytest.fixture
def claim_item():
    """Submit a claim on an item as the given client. Returns the Claim."""

    def _claim(client, item, features="Blue sticker on the side"):
        client.post(f"/items/{item.id}/claim", data={"features": features})
        return Claim.query.order_by(Claim.id.desc()).first()

    return _claim
