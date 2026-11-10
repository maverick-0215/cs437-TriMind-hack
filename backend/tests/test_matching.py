from datetime import date

import pytest

from lostfound.models import Notification
from lostfound.services import MATCH_THRESHOLD, match_score

NEW_ITEM = {
    "category": "Electronics",
    "title": "Black phone",
    "date_found": "2026-10-10",
    "general_area": "Library",
    "exact_location": "Desk 14",
    "description": "Samsung",
}


@pytest.mark.django_db
def test_S13_score_rewards_category_words_place_and_date(make_report, make_item):
    item = make_item(category="Electronics", title="Black phone", general_area="Library", date_found=date(2026, 10, 10))
    perfect = make_report(category="Electronics", title="Lost my phone", place_lost="Library", date_lost=date(2026, 10, 9))
    assert match_score(perfect, item) == 100
    # Same category and date but nothing else in common: below 60%.
    vague = make_report(category="Electronics", title="Laptop charger", place_lost="Hostel", date_lost=date(2026, 10, 9))
    assert match_score(vague, item) < MATCH_THRESHOLD
    # Wrong category can still match when the words and place agree strongly.
    cross = make_report(category="Other", title="Black phone", place_lost="Library", date_lost=date(2026, 10, 9))
    assert match_score(cross, item) >= MATCH_THRESHOLD
    # Found long before it was lost: no date points.
    early = make_report(title="Lost my phone", place_lost="Library", date_lost=date(2026, 11, 30))
    assert match_score(early, item) == 85


@pytest.mark.django_db
def test_S13_item_found_one_day_before_the_lost_date_still_gets_date_points(make_report, make_item):
    item = make_item(category="Electronics", title="Black phone", general_area="Library", date_found=date(2026, 10, 10))
    # Students often get the date off by one.
    one_day_early = make_report(title="Lost my phone", place_lost="Library", date_lost=date(2026, 10, 11))
    assert match_score(one_day_early, item) == 100
    two_days_early = make_report(title="Lost my phone", place_lost="Library", date_lost=date(2026, 10, 12))
    assert match_score(two_days_early, item) == 85


@pytest.mark.django_db
def test_S13_admin_sees_matching_reports_best_first(admin_client, make_report, make_item, other_student):
    item = make_item(title="Black phone", general_area="Library")
    make_report(title="Lost my phone", place_lost="Library")
    make_report(title="Phone", place_lost="Mess", student=other_student)
    make_report(title="Laptop charger", place_lost="Hostel")
    candidates = admin_client.get(f"/api/admin/items/{item.pk}").json()["candidates"]
    assert [(c["title"], c["score"]) for c in candidates] == [("Lost my phone", 100), ("Phone", 85)]
    assert candidates[0]["private_details"] == "PRIVATE-REPORT Totoro sticker"
    assert candidates[1]["student"] == other_student.email


@pytest.mark.django_db
def test_S26_adding_item_notifies_students_with_matching_reports(admin_client, make_report, other_student):
    match = make_report(title="Lost my phone", place_lost="Library", date_lost=date(2026, 10, 1))
    make_report(title="Laptop charger", place_lost="Hostel", student=other_student)
    make_report(title="Brown wallet", category="Wallet", place_lost="Mess", student=other_student)

    admin_client.post("/api/admin/items", NEW_ITEM, format="multipart")
    notes = list(Notification.objects.all())
    assert [(n.user, n.link) for n in notes] == [(match.student, f"/reports/{match.pk}")]
    assert "Lost my phone" in notes[0].message
