import pytest

from lostfound.models import AdminEmail

from .conftest import ADMIN_EMAIL


def _add(client, email):
    return client.post("/api/admin/admins", {"email": email}, format="json")


@pytest.mark.django_db
def test_S28_admin_adds_another_admin(admin_client, student_client, student):
    assert student_client.get("/api/auth/me").json()["is_admin"] is False
    assert _add(admin_client, "Asha@iitgn.ac.in").status_code == 201
    # The new admin gets admin access on their next request, and loses student pages.
    assert student_client.get("/api/auth/me").json()["is_admin"] is True
    assert student_client.get("/api/admin/items").status_code == 200
    assert student_client.get("/api/reports").status_code == 403
    body = admin_client.get("/api/admin/admins").json()
    assert body["permanent"] == [ADMIN_EMAIL]
    assert [(a["email"], a["added_by"]) for a in body["added"]] == [(student.email, ADMIN_EMAIL)]


@pytest.mark.django_db
def test_S28_added_admin_can_use_admin_sign_in(anon, settings, admin_client):
    settings.DEV_LOGIN = True
    login = lambda role: anon.post("/api/auth/dev-login", {"email": "new.guard@iitgn.ac.in", "role": role}, format="json")
    assert login("admin").status_code == 403
    _add(admin_client, "new.guard@iitgn.ac.in")
    assert login("student").status_code == 403
    assert login("admin").status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("email", ["someone@gmail.com", ADMIN_EMAIL, "not-an-email"])
def test_S28_bad_or_duplicate_admin_emails_are_rejected(admin_client, email):
    assert _add(admin_client, email).status_code in (400, 409)
    assert not AdminEmail.objects.exists()


@pytest.mark.django_db
def test_S28_admin_removes_added_admin_but_not_self(admin_client, student_client, admin_user):
    _add(admin_client, "asha@iitgn.ac.in")
    added = AdminEmail.objects.get()
    # The added admin cannot remove themselves.
    assert student_client.post(f"/api/admin/admins/{added.pk}/remove").status_code == 400
    assert admin_client.post(f"/api/admin/admins/{added.pk}/remove").status_code == 204
    assert student_client.get("/api/auth/me").json()["is_admin"] is False
    assert not AdminEmail.objects.exists()


@pytest.mark.django_db
def test_S28_students_cannot_add_admins(student_client):
    assert _add(student_client, "asha@iitgn.ac.in").status_code == 403
    assert not AdminEmail.objects.exists()
