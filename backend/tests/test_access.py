import re

import pytest
from django.contrib.auth import get_user_model
from django.urls import URLPattern, get_resolver

from .conftest import ADMIN_EMAIL


@pytest.fixture
def google(monkeypatch):
    """Stand in for Google: the token string is the email it vouches for."""

    def verify(credential):
        if credential == "bad-token":
            raise ValueError("invalid token")
        email, _, flag = credential.partition("|")
        return {"email": email, "email_verified": flag != "unverified", "name": "Test"}

    monkeypatch.setattr("lostfound.auth_views.verify_google_token", verify)


def _google_login(client, credential):
    return client.post("/api/auth/google", {"credential": credential}, format="json")


def _users():
    return set(get_user_model().objects.values_list("email", flat=True))


@pytest.mark.django_db
def test_S1_iitgn_google_account_can_sign_up_and_log_in(anon, google):
    response = _google_login(anon, "New.Student@iitgn.ac.in")
    assert response.status_code == 200
    assert _users() == {"new.student@iitgn.ac.in"}
    assert anon.get("/api/auth/me").json()["email"] == "new.student@iitgn.ac.in"
    # Logging in again reuses the account.
    anon.post("/api/auth/logout")
    assert _google_login(anon, "new.student@iitgn.ac.in").status_code == 200
    assert len(_users()) == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "email", ["someone@gmail.com", "x@iitgn.ac.in.evil.com", "x@fake-iitgn.ac.in", "x@students.iitgn.ac.in"]
)
def test_S1_other_domains_are_rejected(anon, google, email):
    assert _google_login(anon, email).status_code == 403
    assert _users() == set()
    assert anon.get("/api/auth/me").status_code == 401


@pytest.mark.django_db
def test_S1_unverified_or_invalid_google_logins_are_rejected(anon, google):
    assert _google_login(anon, f"{ADMIN_EMAIL}|unverified").status_code == 403
    assert _google_login(anon, "bad-token").status_code == 400
    assert _users() == set()


@pytest.mark.django_db
def test_S1_dev_login_is_off_unless_enabled(anon, settings):
    assert anon.post("/api/auth/dev-login", {"email": "asha@iitgn.ac.in"}, format="json").status_code == 404
    settings.DEV_LOGIN = True
    assert anon.post("/api/auth/dev-login", {"email": "x@gmail.com"}, format="json").status_code == 403
    assert anon.post("/api/auth/dev-login", {"email": "asha@iitgn.ac.in"}, format="json").status_code == 200


@pytest.mark.django_db
def test_S2_email_in_admin_emails_is_admin(anon, google):
    _google_login(anon, ADMIN_EMAIL)
    assert anon.get("/api/auth/me").json()["is_admin"] is True
    assert anon.get("/api/admin/items").status_code == 200


@pytest.mark.django_db
def test_S2_every_other_user_is_a_student(anon, google, settings):
    settings.ADMIN_EMAILS = {"someone.else@iitgn.ac.in"}
    _google_login(anon, ADMIN_EMAIL)
    assert anon.get("/api/auth/me").json()["is_admin"] is False
    assert anon.get("/api/admin/items").status_code == 403


def _api_urls(prefix=""):
    """Every API route (optionally only those under `prefix`), with ids filled in."""
    urls = []
    for pattern in get_resolver("lostfound.urls").url_patterns:
        route = str(pattern.pattern)
        if isinstance(pattern, URLPattern) and route.startswith(prefix):
            urls.append("/api/" + re.sub(r"<[^>]+>", "1", route))
    return urls


@pytest.mark.django_db
@pytest.mark.parametrize("url", _api_urls("admin/"))
def test_S3_student_gets_403_on_every_admin_route(student_client, url):
    assert student_client.get(url).status_code == 403
    assert student_client.post(url).status_code == 403


def test_S3_admin_route_check_covers_all_admin_routes():
    assert len(_api_urls("admin/")) == 9


OPEN_TO_VISITORS = {"/api/auth/config", "/api/auth/google", "/api/auth/dev-login", "/api/auth/logout"}


@pytest.mark.django_db
@pytest.mark.parametrize("url", [u for u in _api_urls() if u not in OPEN_TO_VISITORS])
def test_S23_logged_out_visitor_gets_401_everywhere_else(anon, make_item, url):
    make_item(title="Hidden phone")
    for response in (anon.get(url), anon.post(url)):
        assert response.status_code in (401, 405), url
        assert "Hidden phone" not in response.content.decode()
    if url != "/api/auth/me":
        assert anon.get(url).status_code == 401


@pytest.mark.django_db
def test_S23_items_api_returns_401_after_logout(student_client, make_item):
    make_item()
    assert student_client.get("/api/items").status_code == 200
    student_client.post("/api/auth/logout")
    assert student_client.get("/api/items").status_code == 401


@pytest.mark.django_db
def test_S23_login_page_config_is_open(anon):
    response = anon.get("/api/auth/config")
    assert response.status_code == 200
    assert set(response.json()) == {"google_client_id", "dev_login"}
