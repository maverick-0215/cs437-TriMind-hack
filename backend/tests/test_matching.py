from datetime import date

import pytest

from lostfound.models import Notification

NEW_ITEM = {
    "category": "Electronics",
    "title": "Black phone",
    "date_found": "2026-10-10",
    "general_area": "Library",
    "exact_location": "Desk 14",
    "description": "Samsung",
}


@pytest.mark.django_db
def test_S13_adding_item_suggests_matching_unlinked_reports(admin_client, make_report, make_item, other_student):
    make_report(title="Lost earlier", date_lost=date(2026, 10, 1))
    make_report(title="Lost same day", date_lost=date(2026, 10, 10), student=other_student)
    make_report(title="Lost after found date", date_lost=date(2026, 10, 11))
    make_report(title="Wrong category", category="Wallet", date_lost=date(2026, 10, 1))
    make_report(title="Already linked", date_lost=date(2026, 10, 1), linked_item=make_item(title="Other"))

    item_id = admin_client.post("/api/admin/items", NEW_ITEM, format="multipart").json()["id"]
    suggestions = admin_client.get(f"/api/admin/items/{item_id}").json()["suggestions"]
    assert sorted(r["title"] for r in suggestions) == ["Lost earlier", "Lost same day"]


@pytest.mark.django_db
def test_S14_admin_links_any_report_even_across_categories(admin_client, make_report, make_item):
    item = make_item(category="Electronics")
    report = make_report(category="Wallet")
    response = admin_client.post(f"/api/admin/items/{item.pk}/link", {"report_id": report.pk}, format="json")
    assert response.status_code == 204
    report.refresh_from_db()
    assert report.linked_item == item


@pytest.mark.django_db
def test_S14_already_linked_report_can_be_moved_to_another_item(admin_client, make_report, make_item):
    wrong, right = make_item(title="Wrong"), make_item(title="Right")
    report = make_report(linked_item=wrong)
    admin_client.post(f"/api/admin/items/{right.pk}/link", {"report_id": report.pk}, format="json")
    report.refresh_from_db()
    assert report.linked_item == right


@pytest.mark.django_db
def test_S15_only_the_filing_student_is_notified(
    admin_client, student_client, make_report, make_item, student, other_student, admin_user
):
    item, report = make_item(), make_report()
    admin_client.post(f"/api/admin/items/{item.pk}/link", {"report_id": report.pk}, format="json")
    assert list(Notification.objects.values_list("user", flat=True)) == [student.pk]
    assert len(student_client.get("/api/notifications").json()) == 1
