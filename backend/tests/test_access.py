import re

import pytest
from django.contrib.auth import get_user_model
from django.urls import URLPattern, get_resolver

from .conftest import ADMIN_EMAIL


@pytest.fixture
def google(monkeypatch):
    """Stand in for Google: the token string is the email it vouches for. Like real Google,
    a Workspace account carries its hosted domain in "hd"; "|personal" is a personal Google
    account registered with that email, which has no "hd"."""

    def verify(credential):
        if credential == "bad-token":
            raise ValueError("invalid token")
        email, _, flag = credential.partition("|")
        claims = {"email": email, "email_verified": flag != "unverified", "name": "Test"}
        if flag != "personal":
            claims["hd"] = email.rpartition("@")[2].lower()
        return claims

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
@pytest.mark.parametrize("email", ["new.student@iitgn.ac.in", ADMIN_EMAIL])
def test_S1_personal_google_account_with_iitgn_email_is_rejected(anon, google, email):
    """A personal Google account made with an IITGN address has no hd: IITGN does not manage it."""
    response = _google_login(anon, f"{email}|personal")
    assert response.status_code == 403
    assert "IITGN Google account" in response.json()["detail"]
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
    assert len(_api_urls("admin/")) == 10


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
def test_S23_api_returns_401_after_logout(student_client):
    assert student_client.get("/api/reports").status_code == 200
    student_client.post("/api/auth/logout")
    assert student_client.get("/api/reports").status_code == 401


@pytest.mark.django_db
def test_S23_login_page_config_is_open(anon):
    response = anon.get("/api/auth/config")
    assert response.status_code == 200
    assert set(response.json()) == {"google_client_id", "dev_login"}


@pytest.mark.django_db
def test_S24_sign_in_option_must_match_role(anon, google):
    def login(email, role):
        return anon.post("/api/auth/google", {"credential": email, "role": role}, format="json")

    assert login("asha@iitgn.ac.in", "admin").status_code == 403
    assert login(ADMIN_EMAIL, "student").status_code == 403
    assert _users() == set()
    assert login("asha@iitgn.ac.in", "student").status_code == 200
    anon.post("/api/auth/logout")
    response = login(ADMIN_EMAIL, "admin")
    assert response.status_code == 200 and response.json()["is_admin"] is True


@pytest.mark.django_db
def test_google_sign_in_popup_can_report_back(anon):
    # "same-origin" would leave the Google popup blank: it could not hand the sign-in back.
    assert anon.get("/api/auth/config")["Cross-Origin-Opener-Policy"] == "same-origin-allow-popups"


@pytest.mark.django_db
def test_S24_dev_login_checks_role_too(anon, settings):
    settings.DEV_LOGIN = True
    post = lambda email, role: anon.post("/api/auth/dev-login", {"email": email, "role": role}, format="json")
    assert post("asha@iitgn.ac.in", "admin").status_code == 403
    assert post(ADMIN_EMAIL, "admin").status_code == 200



@pytest.mark.django_db
def test_pages_outside_api_get_the_react_app(anon, settings, tmp_path):
    settings.FRONTEND_DIST = tmp_path
    assert anon.get("/reports").status_code == 404  # not built yet
    (tmp_path / "index.html").write_text("<div id=root></div>")
    for path in ["/", "/reports/5", "/admin/items/new"]:
        response = anon.get(path)
        assert response.status_code == 200 and b"id=root" in b"".join(response.streaming_content)
    # The API is untouched.
    assert anon.get("/api/reports").status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize("path", ["auth/login", "auth/password/code", "auth/password/reset"])
def test_S1_there_is_no_password_sign_in(anon, path):
    # Issue #17: sign-in is through Google only, so there are no passwords or reset codes to attack.
    response = anon.post(f"/api/{path}", {"email": "asha@iitgn.ac.in", "password": "x", "code": "123456"}, format="json")
    assert response.status_code == 404


@pytest.mark.django_db
def test_S1_google_accounts_have_no_password(anon, google):
    _google_login(anon, "new.student@iitgn.ac.in")
    user = get_user_model().objects.get(username="new.student@iitgn.ac.in")
    assert not user.has_usable_password()

def test_google_signing_keys_are_kept_for_an_hour(monkeypatch):
    """Faster sign-in: Google's public keys are fetched once, not on every sign-in."""
    from lostfound.auth_views import _CachingGoogleRequest

    class Reply:
        status = 200
        data = b"{}"

    calls = []
    keys = _CachingGoogleRequest()
    monkeypatch.setattr(keys, "_request", lambda url, method="GET", **kw: calls.append(url) or Reply())
    for _ in range(3):
        keys("https://www.googleapis.com/oauth2/v1/certs")
    assert len(calls) == 1
    keys.forget()  # e.g. Google switched keys
    keys("https://www.googleapis.com/oauth2/v1/certs")
    assert len(calls) == 2
