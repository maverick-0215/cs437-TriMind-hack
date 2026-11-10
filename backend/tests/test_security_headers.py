import pytest


@pytest.fixture
def built_frontend(settings, tmp_path):
    (tmp_path / "index.html").write_text("<!doctype html><div id=root></div>", encoding="utf-8")
    settings.FRONTEND_DIST = tmp_path


def _policy(response):
    header = response.headers.get("Content-Security-Policy")
    assert header, "no Content-Security-Policy header"
    return dict(
        (part.split()[0], part.split()[1:]) for part in (p.strip() for p in header.split(";")) if part
    )


@pytest.mark.django_db
def test_home_page_sends_a_content_security_policy(anon, built_frontend):
    response = anon.get("/")
    assert response.status_code == 200
    policy = _policy(response)
    assert policy["default-src"] == ["'self'"]
    assert policy["object-src"] == ["'none'"]
    assert policy["frame-ancestors"] == ["'none'"]
    # Only our own scripts and Google's sign-in script; nothing inline, nothing eval'd.
    assert set(policy["script-src"]) == {"'self'", "https://accounts.google.com/gsi/client"}
    assert "'unsafe-inline'" not in str(policy) and "'unsafe-eval'" not in str(policy)


@pytest.mark.django_db
def test_api_responses_also_send_the_policy(anon, student_client):
    assert _policy(anon.get("/api/auth/config"))
    assert _policy(student_client.get("/api/items"))
