import re

from app.models import User
from conftest import PASSWORD


def test_S1_iitgn_email_can_sign_up(anon):
    resp = anon.post("/signup", data={"name": "Asha", "email": "Asha@IITGN.ac.in", "password": PASSWORD})
    assert resp.status_code == 302
    assert User.query.filter_by(email="asha@iitgn.ac.in").count() == 1


def test_S1_other_domains_cannot_sign_up(anon):
    for email in ["asha@gmail.com", "asha@iitgn.ac.in.evil.com", "asha@fake-iitgn.ac.in", "@iitgn.ac.in"]:
        resp = anon.post("/signup", data={"name": "Asha", "email": email, "password": PASSWORD})
        assert resp.status_code == 400, email
        assert "Only @iitgn.ac.in emails can sign up." in resp.get_data(as_text=True)
    assert User.query.count() == 0


def test_S1_other_domains_cannot_log_in(app, anon):
    # Even if such a user somehow existed in the database, login must refuse the domain.
    user = User(name="X", email="x@gmail.com")
    user.set_password(PASSWORD)
    from app import db

    db.session.add(user)
    db.session.commit()

    resp = anon.post("/login", data={"email": "x@gmail.com", "password": PASSWORD})
    assert resp.status_code == 400
    assert "Only @iitgn.ac.in emails can log in." in resp.get_data(as_text=True)
    assert anon.get("/reports").status_code == 302  # still logged out


def test_S1_iitgn_email_can_log_in(app, student):
    client = app.test_client()
    resp = client.post("/login", data={"email": "asha@iitgn.ac.in", "password": PASSWORD})
    assert resp.status_code == 302
    assert client.get("/reports").status_code == 200


def test_S2_email_in_admin_emails_is_admin(admin, student):
    assert User.query.filter_by(email="guard@iitgn.ac.in").one().is_admin
    assert not User.query.filter_by(email="asha@iitgn.ac.in").one().is_admin
    assert admin.get("/admin").status_code == 200


def test_S2_admin_emails_list_is_comma_separated_and_case_insensitive(app, student):
    app.config["ADMIN_EMAILS"] = " someone@iitgn.ac.in , ASHA@iitgn.ac.in "
    assert User.query.filter_by(email="asha@iitgn.ac.in").one().is_admin
    assert student.get("/admin").status_code == 200


def admin_urls(app):
    """Every admin route in the app, with placeholder ids filled in."""
    for rule in app.url_map.iter_rules():
        if rule.rule.startswith("/admin"):
            url = re.sub(r"<[^>]+>", "1", rule.rule)
            for method in rule.methods - {"HEAD", "OPTIONS"}:
                yield method, url


def test_S3_student_gets_403_on_every_admin_route(app, student, add_item, claim_item, other):
    item = add_item()
    claim_item(other, item)  # so /admin/claims/1/... exists
    routes = list(admin_urls(app))
    assert len(routes) >= 9  # guards against the check silently covering nothing
    for method, url in routes:
        resp = student.open(url, method=method)
        assert resp.status_code == 403, f"{method} {url} returned {resp.status_code}"


def test_S3_logged_out_user_cannot_open_admin_routes(app, anon):
    for method, url in admin_urls(app):
        resp = anon.open(url, method=method)
        assert resp.status_code == 302 and "/login" in resp.headers["Location"], f"{method} {url}"


def test_S23_logged_out_visitor_can_open_login_and_signup(anon):
    assert anon.get("/login").status_code == 200
    assert anon.get("/signup").status_code == 200


def test_S23_logged_out_visitor_is_sent_to_login_from_every_other_page(app, anon, add_item):
    add_item(title="Hidden bottle")
    open_pages = {"/login", "/signup", "/static/<path:filename>"}
    checked = 0
    for rule in app.url_map.iter_rules():
        if rule.rule in open_pages:
            continue
        url = re.sub(r"<[^>]+>", "1", rule.rule)
        for method in rule.methods - {"HEAD", "OPTIONS"}:
            resp = anon.open(url, method=method)
            body = resp.get_data(as_text=True)
            assert "Hidden bottle" not in body, f"{method} {url}"
            if url.startswith("/api/"):
                assert resp.status_code == 401, f"{method} {url}"
            else:
                assert resp.status_code == 302 and "/login" in resp.headers["Location"], f"{method} {url}"
            checked += 1
    assert checked >= 20  # guards against the check silently covering nothing


def test_S23_after_logout_the_list_is_hidden_again(student, add_item):
    add_item(title="Hidden bottle")
    assert "Hidden bottle" in student.get("/").get_data(as_text=True)
    student.post("/logout")
    resp = student.get("/")
    assert resp.status_code == 302 and "/login" in resp.headers["Location"]
    assert student.get("/api/items").status_code == 401
