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
