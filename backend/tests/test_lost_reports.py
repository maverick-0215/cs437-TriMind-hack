import pytest

from lostfound.models import LostReport

NEW_REPORT = {
    "category": "Wallet",
    "title": "Brown wallet",
    "date_lost": "2026-10-05",
    "place_lost": "Mess",
    "private_details": "Metro card in the name of Asha",
}


@pytest.mark.django_db
def test_S11_student_files_lost_report(student_client, student):
    response = student_client.post("/api/reports", NEW_REPORT, format="json")
    assert response.status_code == 201
    report = LostReport.objects.get()
    assert report.student == student
    assert (report.category, report.title, str(report.date_lost), report.place_lost, report.private_details) == (
        "Wallet", "Brown wallet", "2026-10-05", "Mess", "Metro card in the name of Asha",
    )


@pytest.mark.django_db
def test_S11_missing_field_is_rejected(student_client):
    assert student_client.post("/api/reports", {**NEW_REPORT, "title": ""}, format="json").status_code == 400
    assert not LostReport.objects.exists()


@pytest.mark.django_db
def test_S12_student_sees_only_own_reports(student_client, make_report, other_student):
    make_report(title="Asha's wallet")
    make_report(title="Ravi's keys", student=other_student, private_details="RAVI-SECRET")
    response = student_client.get("/api/reports")
    assert [r["title"] for r in response.json()] == ["Asha's wallet"]
    assert "RAVI-SECRET" not in response.content.decode()


@pytest.mark.django_db
def test_S12_opening_another_students_report_is_404(student_client, other_client, make_report):
    report = make_report()
    assert student_client.get(f"/api/reports/{report.pk}").status_code == 200
    response = other_client.get(f"/api/reports/{report.pk}")
    assert response.status_code == 404
    assert "PRIVATE-REPORT" not in response.content.decode()


@pytest.mark.django_db
def test_S25_report_shows_items_matching_60_percent_with_contact(student_client, make_report, make_item, admin_user):
    from datetime import date

    from lostfound.models import FoundItem

    report = make_report(category="Electronics", title="Lost my phone", place_lost="Library", date_lost=date(2026, 10, 9))
    make_item(title="Black phone", general_area="Library", date_found=date(2026, 10, 10))
    make_item(title="Phone", general_area="Mess", date_found=date(2026, 10, 12))
    make_item(title="Laptop charger", general_area="Hostel")
    make_item(title="Claimed phone", status=FoundItem.Status.CLAIMED)

    body = student_client.get(f"/api/reports/{report.pk}").json()
    assert [(m["title"], m["score"]) for m in body["matches"]] == [("Black phone", 100), ("Phone", 85)]
    match = body["matches"][0]
    assert match["general_area"] == "Library"
    assert body["security_contact"]
    assert admin_user.email not in str(body)
    # S7 still holds: no private item details.
    assert "SECRET" not in str(body)


@pytest.mark.django_db
def test_S25_report_with_no_matches_has_empty_list(student_client, make_report):
    report = make_report()
    assert student_client.get(f"/api/reports/{report.pk}").json()["matches"] == []



@pytest.mark.django_db
def test_S32_double_submitted_report_is_saved_once(student_client, other_client):
    first = student_client.post("/api/reports", NEW_REPORT, format="json")
    again = student_client.post("/api/reports", NEW_REPORT, format="json")
    assert (first.status_code, again.status_code) == (201, 200)
    assert again.json()["id"] == first.json()["id"]
    assert LostReport.objects.count() == 1
    # Another student filing the same details is their own report.
    assert other_client.post("/api/reports", NEW_REPORT, format="json").status_code == 201
    assert LostReport.objects.count() == 2


def _report_png(padding=0):
    from io import BytesIO

    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", (4, 4), "blue").save(buf, "PNG")
    return SimpleUploadedFile("bag.png", buf.getvalue() + b"\0" * padding, content_type="image/png")


S33_REPORT = {
    "category": "Bag",
    "title": "Blue backpack",
    "date_lost": "2026-10-09",
    "place_lost": "Library",
    "private_details": "Keychain with a red bus",
}


@pytest.mark.django_db
def test_S33_student_adds_a_photo_that_only_they_and_admins_see(student_client, other_client, admin_client, anon):
    response = student_client.post("/api/reports", {**S33_REPORT, "photo": _report_png()}, format="multipart")
    assert response.status_code == 201
    report_id = response.json()["id"]
    assert response.json()["has_photo"] is True
    url = f"/api/reports/{report_id}/photo"
    for client in (student_client, admin_client):
        photo = client.get(url)
        assert photo.status_code == 200
        assert b"".join(photo.streaming_content).startswith(b"\x89PNG")
    assert other_client.get(url).status_code == 404  # S12: not another student's
    assert anon.get(url).status_code == 401


@pytest.mark.django_db
def test_S33_report_photo_is_optional(student_client):
    response = student_client.post("/api/reports", S33_REPORT, format="multipart")
    assert response.status_code == 201 and response.json()["has_photo"] is False
    assert student_client.get(f"/api/reports/{response.json()['id']}/photo").status_code == 404


@pytest.mark.django_db
def test_S33_report_photo_must_be_an_image_of_at_most_5_mb(student_client):
    from django.core.files.uploadedfile import SimpleUploadedFile

    from lostfound.models import LostReport

    fake = SimpleUploadedFile("evil.png", b"<script>alert(1)</script>", content_type="image/png")
    big = _report_png(padding=6 * 1024 * 1024)
    for photo in (fake, big):
        assert student_client.post("/api/reports", {**S33_REPORT, "photo": photo}, format="multipart").status_code == 400
    assert not LostReport.objects.exists()


@pytest.mark.django_db
def test_S33_admin_sees_the_report_photo_next_to_a_matching_item(student_client, admin_client, make_item):
    item = make_item(category="Bag", title="Blue backpack", general_area="Library", date_found="2026-10-10")
    student_client.post("/api/reports", {**S33_REPORT, "photo": _report_png()}, format="multipart")
    candidate = admin_client.get(f"/api/admin/items/{item.pk}").json()["candidates"][0]
    assert candidate["has_photo"] is True


@pytest.mark.django_db
@pytest.mark.parametrize("place", [None, ""])
def test_S11_place_lost_is_optional(student_client, place):
    data = {k: v for k, v in NEW_REPORT.items() if k != "place_lost"}
    if place is not None:
        data["place_lost"] = place
    response = student_client.post("/api/reports", data, format="json")
    assert response.status_code == 201
    assert LostReport.objects.get().place_lost == ""
    # S32: sending it again still returns the one already saved.
    assert student_client.post("/api/reports", data, format="json").status_code == 200
    assert LostReport.objects.count() == 1


# --- S34: admins see every lost report ---


@pytest.mark.django_db
def test_S34_admin_sees_every_lost_report_with_its_matches(
    admin_client, make_report, make_item, student, other_student
):
    from datetime import date

    item = make_item(title="Black phone", category="Electronics", general_area="Library", date_found=date(2026, 10, 10))
    older = make_report(title="Lost my phone", place_lost="Library", date_lost=date(2026, 10, 9))
    newer = make_report(
        student=other_student, category="Wallet", title="Brown wallet", place_lost="", date_lost=date(2026, 10, 1)
    )
    newer.photo.save("w.png", _report_png(), save=True)

    body = admin_client.get("/api/admin/reports").json()
    assert [r["id"] for r in body] == [newer.pk, older.pk]  # newest first
    first, second = body
    assert (first["student"], first["place_lost"], first["has_photo"], first["status"]) == (
        other_student.email, "", True, "OPEN",
    )
    assert first["private_details"] == newer.private_details
    assert first["matches"] == []
    assert second["student"] == student.email
    assert [(m["id"], m["title"]) for m in second["matches"]] == [(item.pk, "Black phone")]
    assert second["matches"][0]["score"] >= 60


@pytest.mark.django_db
def test_S34_approved_and_closed_reports_show_their_status_and_item(admin_client, make_report, make_item, admin_user):
    from lostfound.models import FoundItem, Handover

    waiting = make_item(title="Black phone", status=FoundItem.Status.CLAIMED)
    returned = make_item(title="Red bottle", status=FoundItem.Status.RETURNED)
    make_report(title="Lost my phone", linked_item=waiting)
    closed = make_report(title="Lost my bottle", linked_item=returned)
    Handover.objects.create(item=returned, student=closed.student, admin=admin_user)

    by_title = {r["title"]: r for r in admin_client.get("/api/admin/reports").json()}
    assert by_title["Lost my phone"]["status"] == "APPROVED"
    assert by_title["Lost my phone"]["item"]["id"] == waiting.pk
    assert by_title["Lost my bottle"]["status"] == "CLOSED" and by_title["Lost my bottle"]["closed_at"]
    assert by_title["Lost my phone"]["matches"] == by_title["Lost my bottle"]["matches"] == []


@pytest.mark.django_db
def test_S34_students_cannot_list_lost_reports(student_client, anon):
    assert student_client.get("/api/admin/reports").status_code == 403
    assert anon.get("/api/admin/reports").status_code == 401


# --- S35: closed reports are deleted 60 days after collection ---


def _closed(make_item, make_report, admin_user, days_ago):
    from datetime import timedelta

    from django.utils import timezone

    from lostfound.models import FoundItem, Handover

    item = make_item(title=f"Item {days_ago}", status=FoundItem.Status.RETURNED)
    item.photo.save("item.png", _report_png(), save=True)
    report = make_report(title=f"Report {days_ago}", linked_item=item)
    report.photo.save("report.png", _report_png(), save=True)
    handover = Handover.objects.create(item=item, student=report.student, admin=admin_user)
    Handover.objects.filter(pk=handover.pk).update(handed_over_at=timezone.now() - timedelta(days=days_ago))
    return item, report


@pytest.mark.django_db
def test_S35_reports_closed_over_60_days_ago_are_deleted_with_photos(make_item, make_report, admin_user):
    from pathlib import Path

    from django.core.management import call_command

    from lostfound.models import FoundItem, Handover

    old_item, old_report = _closed(make_item, make_report, admin_user, days_ago=61)
    new_item, new_report = _closed(make_item, make_report, admin_user, days_ago=59)
    files = [Path(old_item.photo.path), Path(old_report.photo.path)]

    call_command("delete_old_closed_reports")

    assert not LostReport.objects.filter(pk=old_report.pk).exists()
    assert not any(f.exists() for f in files)
    old_item.refresh_from_db()
    assert old_item.photo.name == "" and old_item.status == FoundItem.Status.RETURNED
    # The handover log (S21) is the summary that stays.
    assert Handover.objects.filter(item=old_item).exists()
    # Closed only 59 days ago: untouched.
    assert LostReport.objects.filter(pk=new_report.pk).exists()
    new_item.refresh_from_db()
    assert new_item.photo.name != ""


@pytest.mark.django_db
def test_S35_open_and_approved_reports_are_never_deleted(make_item, make_report):
    from datetime import timedelta

    from django.core.management import call_command
    from django.utils import timezone

    from lostfound.models import FoundItem

    open_report = make_report(title="Old open report")
    approved = make_report(title="Waiting", linked_item=make_item(status=FoundItem.Status.CLAIMED))
    LostReport.objects.update(created_at=timezone.now() - timedelta(days=400))
    call_command("delete_old_closed_reports")
    assert set(LostReport.objects.values_list("pk", flat=True)) == {open_report.pk, approved.pk}


@pytest.mark.django_db
def test_S35_opening_the_lost_reports_tab_also_cleans_up(admin_client, make_item, make_report, admin_user):
    _, old_report = _closed(make_item, make_report, admin_user, days_ago=90)
    assert old_report.pk not in [r["id"] for r in admin_client.get("/api/admin/reports").json()]
    assert not LostReport.objects.filter(pk=old_report.pk).exists()
