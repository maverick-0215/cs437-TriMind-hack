from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from lostfound.models import FoundItem

NEW_ITEM = {
    "category": "Electronics",
    "title": "Black phone",
    "date_found": "2026-10-10",
    "general_area": "Library",
    "exact_location": "Second floor, desk 14",
    "description": "Samsung with a cracked corner",
}


def _png():
    buf = BytesIO()
    Image.new("RGB", (4, 4), "red").save(buf, "PNG")
    return SimpleUploadedFile("phone.png", buf.getvalue(), content_type="image/png")


@pytest.mark.django_db
def test_S4_admin_adds_item_with_private_details_and_photo(admin_client, admin_user):
    response = admin_client.post("/api/admin/items", {**NEW_ITEM, "photo": _png()}, format="multipart")
    assert response.status_code == 201
    item = FoundItem.objects.get()
    assert (item.category, item.title, str(item.date_found), item.general_area) == (
        "Electronics", "Black phone", "2026-10-10", "Library",
    )
    assert item.exact_location == "Second floor, desk 14"
    assert item.description == "Samsung with a cracked corner"
    assert item.added_by == admin_user
    photo = admin_client.get(f"/api/admin/items/{item.pk}/photo")
    assert photo.status_code == 200
    assert b"".join(photo.streaming_content).startswith(b"\x89PNG")


@pytest.mark.django_db
def test_S4_photo_is_optional(admin_client):
    assert admin_client.post("/api/admin/items", NEW_ITEM, format="multipart").status_code == 201
    assert FoundItem.objects.get().photo.name == ""


@pytest.mark.django_db
@pytest.mark.parametrize("bad", [{"title": ""}, {"exact_location": ""}, {"category": "Spaceship"}, {"date_found": "x"}])
def test_S4_missing_or_invalid_fields_are_rejected(admin_client, bad):
    assert admin_client.post("/api/admin/items", {**NEW_ITEM, **bad}, format="multipart").status_code == 400
    assert not FoundItem.objects.exists()


@pytest.mark.django_db
def test_S4_non_image_photo_is_rejected(admin_client):
    fake = SimpleUploadedFile("evil.png", b"<script>alert(1)</script>", content_type="image/png")
    assert admin_client.post("/api/admin/items", {**NEW_ITEM, "photo": fake}, format="multipart").status_code == 400


@pytest.mark.django_db
def test_S5_new_item_is_available(admin_client):
    response = admin_client.post("/api/admin/items", NEW_ITEM, format="multipart")
    assert response.json()["status"] == "AVAILABLE"
    assert FoundItem.objects.get().status == FoundItem.Status.AVAILABLE



@pytest.mark.django_db
def test_S31_future_dates_are_rejected(admin_client, student_client):
    from datetime import timedelta

    from django.utils import timezone

    from lostfound.models import FoundItem, LostReport

    today = timezone.localdate()
    tomorrow = today + timedelta(days=1)
    item = {"category": "Bag", "title": "Blue bag", "general_area": "Mess", "exact_location": "Gate", "description": "x"}
    assert admin_client.post("/api/admin/items", {**item, "date_found": tomorrow}, format="multipart").status_code == 400
    assert admin_client.post("/api/admin/items", {**item, "date_found": today}, format="multipart").status_code == 201
    report = {"category": "Bag", "title": "Blue bag", "place_lost": "Mess", "private_details": "x"}
    assert student_client.post("/api/reports", {**report, "date_lost": tomorrow}, format="json").status_code == 400
    assert student_client.post("/api/reports", {**report, "date_lost": today}, format="json").status_code == 201
    assert (FoundItem.objects.count(), LostReport.objects.count()) == (1, 1)



@pytest.mark.django_db
def test_S7_students_never_see_private_details(student_client, make_item, make_report, admin_client):
    item = make_item()
    report = make_report()
    admin_client.post(f"/api/admin/items/{item.pk}/approve", {"report_id": report.pk}, format="json")
    for url in ["/api/reports", f"/api/reports/{report.pk}", "/api/claims", "/api/notifications"]:
        assert "SECRET" not in student_client.get(url).content.decode(), url
    assert student_client.get(f"/api/admin/items/{item.pk}").status_code == 403
    assert student_client.get(f"/api/admin/items/{item.pk}/photo").status_code == 403



@pytest.mark.django_db
def test_S32_double_submitted_found_item_is_saved_once(admin_client, make_report):
    from datetime import date, timedelta

    from django.utils import timezone

    from lostfound.models import FoundItem, Notification

    make_report(title="Lost my phone", place_lost="Library", date_lost=date(2026, 10, 9))
    item = {
        "category": "Electronics", "title": "Black phone", "date_found": "2026-10-10",
        "general_area": "Library", "exact_location": "Desk 14", "description": "Samsung",
    }
    first = admin_client.post("/api/admin/items", item, format="multipart")
    again = admin_client.post("/api/admin/items", item, format="multipart")
    assert (first.status_code, again.status_code) == (201, 200)
    assert again.json()["id"] == first.json()["id"]
    assert FoundItem.objects.count() == 1
    assert Notification.objects.count() == 1  # the student is not told twice

    # A different item, or the same one added later, is a real new item.
    assert admin_client.post("/api/admin/items", {**item, "title": "Blue phone"}, format="multipart").status_code == 201
    FoundItem.objects.update(created_at=timezone.now() - timedelta(minutes=3))
    assert admin_client.post("/api/admin/items", item, format="multipart").status_code == 201
    assert FoundItem.objects.count() == 3


@pytest.mark.django_db
def test_S6_found_items_list_shows_what_where_and_who(student_client, make_item, admin_user):
    from datetime import date

    from lostfound.models import FoundItem

    make_item(title="Older umbrella", category="Umbrella", date_found=date(2026, 10, 1), general_area="Library")
    make_item(title="Newer bottle", category="Bottle", date_found=date(2026, 10, 9), general_area="Mess")
    make_item(title="Waiting for pickup", status=FoundItem.Status.CLAIMED)
    make_item(title="Already returned", status=FoundItem.Status.RETURNED)

    body = student_client.get("/api/items").json()
    assert [i["title"] for i in body["items"]] == ["Newer bottle", "Older umbrella"]
    first = body["items"][0]
    assert (first["category"], first["date_found"], first["general_area"]) == ("Bottle", "2026-10-09", "Mess")
    assert first["contact"] == admin_user.email
    assert body["security_contact"]
    # S7: public fields only.
    assert set(first) == {"id", "category", "title", "date_found", "general_area", "contact"}
    assert "SECRET" not in str(body)


def _big_png(megabytes):
    """A real PNG padded past `megabytes`, so only its size is wrong."""
    return SimpleUploadedFile(
        "big.png", _png().read() + b"\0" * (megabytes * 1024 * 1024), content_type="image/png"
    )


@pytest.mark.django_db
def test_S4_photo_over_5_mb_is_rejected(admin_client):
    response = admin_client.post("/api/admin/items", {**NEW_ITEM, "photo": _big_png(6)}, format="multipart")
    assert response.status_code == 400
    assert "5 MB" in str(response.json())
    assert not FoundItem.objects.exists()
