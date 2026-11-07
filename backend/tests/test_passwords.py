import re
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone

from lostfound.models import PasswordCode

from .conftest import ADMIN_EMAIL

EMAIL = "asha@iitgn.ac.in"
GOOD_PASSWORD = "lantern-violet-42"


def _post(client, path, **body):
    return client.post(f"/api/auth/{path}", body, format="json")


def _ask_code(client, email=EMAIL):
    mail.outbox.clear()
    response = _post(client, "password/code", email=email)
    code = re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1) if mail.outbox else None
    return response, code


def _set_password(client, code, password=GOOD_PASSWORD, email=EMAIL):
    return _post(client, "password/reset", email=email, code=code, password=password)


@pytest.mark.django_db
def test_S30_new_user_sets_password_with_emailed_code(anon):
    response, code = _ask_code(anon)
    assert response.status_code == 200
    assert mail.outbox[0].to == [EMAIL]
    # Only a hash is stored, never the code itself.
    assert code not in PasswordCode.objects.get().code_hash
    assert _set_password(anon, code).status_code == 200
    assert get_user_model().objects.get(username=EMAIL).check_password(GOOD_PASSWORD)


@pytest.mark.django_db
def test_S30_code_works_once_and_wrong_code_fails(anon):
    _, code = _ask_code(anon)
    wrong = "000000" if code != "000000" else "111111"
    assert _set_password(anon, wrong).status_code == 400
    assert _set_password(anon, code).status_code == 200
    assert _set_password(anon, code, password="another-pass-77").status_code == 400


@pytest.mark.django_db
def test_S30_code_expires_and_locks_after_5_tries(anon):
    _, code = _ask_code(anon)
    PasswordCode.objects.update(created_at=timezone.now() - timedelta(minutes=11))
    assert _set_password(anon, code).status_code == 400

    PasswordCode.objects.all().delete()
    _, code = _ask_code(anon)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        _set_password(anon, wrong)
    assert _set_password(anon, code).status_code == 400


@pytest.mark.django_db
def test_S30_new_code_replaces_old_one(anon):
    _, first = _ask_code(anon)
    PasswordCode.objects.update(created_at=timezone.now() - timedelta(minutes=2))
    _, second = _ask_code(anon)
    if first != second:
        assert _set_password(anon, first).status_code == 400
    assert _set_password(anon, second).status_code == 200


@pytest.mark.django_db
def test_S30_weak_password_is_rejected_and_code_still_works(anon):
    _, code = _ask_code(anon)
    assert _set_password(anon, code, password="12345678").status_code == 400
    assert _set_password(anon, code).status_code == 200


@pytest.mark.django_db
def test_S30_only_iitgn_emails_get_codes(anon):
    response, code = _ask_code(anon, "someone@gmail.com")
    assert response.status_code == 403 and code is None


@pytest.mark.django_db
def test_S29_sign_in_with_password(anon):
    _, code = _ask_code(anon)
    _set_password(anon, code)
    assert _post(anon, "login", email=EMAIL, password="wrong-password").status_code == 400
    response = _post(anon, "login", email=EMAIL.upper(), password=GOOD_PASSWORD, role="student")
    assert response.status_code == 200
    assert anon.get("/api/auth/me").json()["email"] == EMAIL


@pytest.mark.django_db
def test_S29_unknown_account_gets_same_message(anon):
    unknown = _post(anon, "login", email="nobody@iitgn.ac.in", password="whatever-123")
    assert unknown.status_code == 400 and unknown.json()["detail"] == "Wrong email or password."


@pytest.mark.django_db
def test_S29_role_still_checked_with_password(anon):
    _, code = _ask_code(anon, ADMIN_EMAIL)
    _set_password(anon, code, email=ADMIN_EMAIL)
    assert _post(anon, "login", email=ADMIN_EMAIL, password=GOOD_PASSWORD, role="student").status_code == 403
    assert _post(anon, "login", email=ADMIN_EMAIL, password=GOOD_PASSWORD, role="admin").json()["is_admin"] is True


@pytest.mark.django_db
def test_S29_locked_after_5_wrong_passwords(anon):
    _, code = _ask_code(anon)
    _set_password(anon, code)
    for _ in range(5):
        _post(anon, "login", email=EMAIL, password="wrong-password")
    assert _post(anon, "login", email=EMAIL, password=GOOD_PASSWORD).status_code == 429


@pytest.mark.django_db
def test_S30_failed_email_is_reported_and_nothing_is_kept(anon, settings):
    # A mail server that refuses the connection, like a misconfigured SMTP host in production.
    settings.EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    settings.EMAIL_HOST, settings.EMAIL_PORT, settings.EMAIL_TIMEOUT = "127.0.0.1", 1, 2
    for _ in range(2):
        response = _post(anon, "password/code", email=EMAIL)
        assert response.status_code == 503
        assert "couldn't send" in response.json()["detail"]
    assert not PasswordCode.objects.filter(used=False).exists()
    # Once email works again, a code goes out straight away instead of "already sent".
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    response, code = _ask_code(anon)
    assert response.status_code == 200 and code is not None
