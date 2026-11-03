from app import db
from app.models import Notification, User


def suggestions_section(admin, item):
    page = admin.get(f"/admin/items/{item.id}").get_data(as_text=True)
    start = page.index('<section id="suggestions">')
    return page[start : page.index("</section>", start)]


def test_S13_suggests_unlinked_reports_with_same_category_lost_on_or_before_found_date(
    admin, student, other, add_report, add_item
):
    add_report(student, title="Match earlier", date_lost="2026-10-01")
    add_report(other, title="Match same day", date_lost="2026-10-03")
    add_report(student, title="Lost after found", date_lost="2026-10-04")
    add_report(student, title="Wrong category", category="Umbrella", date_lost="2026-10-01")
    already = add_report(other, title="Already linked", date_lost="2026-10-01")
    first = add_item(title="Earlier item")
    admin.post(f"/admin/items/{first.id}/link", data={"report_id": already.id})

    item = add_item(date_found="2026-10-03")
    section = suggestions_section(admin, item)
    assert "Match earlier" in section
    assert "Match same day" in section
    assert "Lost after found" not in section
    assert "Wrong category" not in section
    assert "Already linked" not in section


def test_S13_adding_an_item_leads_admin_to_its_suggestions(admin, student, add_report):
    from conftest import ITEM_DEFAULTS

    add_report(student, title="Asha bottle")
    resp = admin.post("/admin/items/new", data=ITEM_DEFAULTS, follow_redirects=True)
    assert 'id="suggestions"' in resp.get_data(as_text=True)
    assert "Asha bottle" in resp.get_data(as_text=True)


def test_S14_admin_can_link_any_report_even_across_categories(admin, student, add_report, add_item):
    report = add_report(student, category="Bag", date_lost="2026-10-20")
    item = add_item(category="Bottle", date_found="2026-10-03")
    admin.post(f"/admin/items/{item.id}/link", data={"report_id": report.id})
    db.session.refresh(report)
    assert report.linked_item_id == item.id


def test_S15_only_the_filer_is_notified_when_report_is_linked(admin, student, other, add_report, add_item):
    report = add_report(student)
    add_report(other)  # another matching report that is NOT linked
    item = add_item()
    admin.post(f"/admin/items/{item.id}/link", data={"report_id": report.id})

    def count(email):
        user = User.query.filter_by(email=email).one()
        return Notification.query.filter_by(user_id=user.id).count()

    assert count("asha@iitgn.ac.in") == 1
    assert count("ravi@iitgn.ac.in") == 0
    assert count("guard@iitgn.ac.in") == 0
    assert Notification.query.count() == 1

    assert "My blue bottle" in student.get("/notifications").get_data(as_text=True)
    assert "My blue bottle" not in other.get("/notifications").get_data(as_text=True)
