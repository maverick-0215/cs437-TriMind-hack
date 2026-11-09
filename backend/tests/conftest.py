from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from lostfound.models import FoundItem, LostReport

ADMIN_EMAIL = "guard@iitgn.ac.in"


@pytest.fixture(autouse=True)
def _media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"



def _user(email):
    return get_user_model().objects.create_user(username=email, email=email)


def _client(user):
    client = APIClient()
    client.force_login(user)
    return client


@pytest.fixture
def admin_user(db):
    return _user(ADMIN_EMAIL)


@pytest.fixture
def student(db):
    return _user("asha@iitgn.ac.in")


@pytest.fixture
def other_student(db):
    return _user("ravi@iitgn.ac.in")


@pytest.fixture
def anon(db):
    return APIClient()


@pytest.fixture
def admin_client(admin_user):
    return _client(admin_user)


@pytest.fixture
def student_client(student):
    return _client(student)


@pytest.fixture
def other_client(other_student):
    return _client(other_student)


@pytest.fixture
def make_item(admin_user):
    def make(**fields):
        defaults = {
            "category": "Electronics",
            "title": "Black phone",
            "date_found": date(2026, 10, 10),
            "general_area": "Library",
            "exact_location": "SECRET-LOCATION desk 14",
            "description": "SECRET-DESCRIPTION cracked corner",
            "added_by": admin_user,
        }
        return FoundItem.objects.create(**{**defaults, **fields})

    return make


@pytest.fixture
def make_report(student):
    def make(**fields):
        defaults = {
            "student": student,
            "category": "Electronics",
            "title": "Lost my phone",
            "date_lost": date(2026, 10, 9),
            "place_lost": "Library",
            "private_details": "PRIVATE-REPORT Totoro sticker",
        }
        return LostReport.objects.create(**{**defaults, **fields})

    return make
