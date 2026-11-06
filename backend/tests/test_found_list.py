from datetime import date

import pytest

from lostfound.models import FoundItem

PUBLIC_KEYS = {"id", "category", "title", "date_found", "general_area"}


def _titles(client, **params):
    response = client.get("/api/items", params)
    assert response.status_code == 200
    return [item["title"] for item in response.json()]


@pytest.mark.django_db
def test_S6_logged_in_user_sees_available_items_newest_first(student_client, make_item):
    make_item(title="Old umbrella", date_found=date(2026, 9, 1))
    make_item(title="New watch", date_found=date(2026, 10, 20))
    make_item(title="Claimed bag", status=FoundItem.Status.CLAIMED)
    assert _titles(student_client) == ["New watch", "Old umbrella"]


@pytest.mark.django_db
def test_S6_list_shows_category_title_date_and_area(student_client, make_item):
    make_item(title="New watch", category="Jewellery & watches", date_found=date(2026, 10, 20), general_area="Gym")
    item = student_client.get("/api/items").json()[0]
    assert (item["category"], item["title"], item["date_found"], item["general_area"]) == (
        "Jewellery & watches", "New watch", "2026-10-20", "Gym",
    )


@pytest.mark.django_db
def test_S7_list_never_shows_private_details(student_client, make_item):
    item = make_item()
    response = student_client.get("/api/items")
    assert set(response.json()[0]) == PUBLIC_KEYS
    assert "SECRET" not in response.content.decode()
    assert student_client.get(f"/api/admin/items/{item.pk}/photo").status_code == 403


@pytest.mark.django_db
def test_S8_filter_by_category(student_client, make_item):
    make_item(title="Phone", category="Electronics")
    make_item(title="Umbrella", category="Umbrella")
    assert _titles(student_client, category="Umbrella") == ["Umbrella"]


@pytest.mark.django_db
def test_S9_filter_by_date_found_range(student_client, make_item):
    make_item(title="September", date_found=date(2026, 9, 15))
    make_item(title="October", date_found=date(2026, 10, 15))
    make_item(title="November", date_found=date(2026, 11, 1))
    assert _titles(student_client, date_from="2026-10-01", date_to="2026-10-31") == ["October"]
    assert _titles(student_client, date_from="2026-10-01") == ["November", "October"]
    assert _titles(student_client, date_to="2026-10-01") == ["September"]


@pytest.mark.django_db
def test_S10_keyword_matches_title_or_category_ignoring_case(student_client, make_item):
    make_item(title="Black PHONE", category="Electronics")
    make_item(title="Red umbrella", category="Umbrella")
    make_item(title="Notebook", category="Books & stationery", description="phone number written inside")
    assert _titles(student_client, q="phone") == ["Black PHONE"]
    assert _titles(student_client, q="ELECTRONICS") == ["Black PHONE"]
    assert _titles(student_client, q="Umbr") == ["Red umbrella"]


@pytest.mark.django_db
def test_S22_returned_items_are_not_listed(student_client, make_item):
    make_item(title="Returned phone", status=FoundItem.Status.RETURNED)
    assert _titles(student_client) == []
