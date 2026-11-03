from app import db
from app.models import Handover, User


def return_item(admin, student, item, claim_item):
    claim = claim_item(student, item)
    admin.post(f"/admin/claims/{claim.id}/approve")
    db.session.refresh(claim)
    admin.post(f"/admin/items/{item.id}/handover", data={"code": claim.pickup_code})


def test_S21_handover_is_logged_with_item_student_admin_and_time(admin, student, add_item, claim_item):
    item = add_item(title="Logged bottle")
    return_item(admin, student, item, claim_item)

    log = Handover.query.one()
    assert log.item_id == item.id
    assert log.student_id == User.query.filter_by(email="asha@iitgn.ac.in").one().id
    assert log.admin_id == User.query.filter_by(email="guard@iitgn.ac.in").one().id
    assert log.handed_over_at is not None

    page = admin.get("/admin").get_data(as_text=True)
    table = page[page.index('id="handovers"') :]
    assert "Logged bottle" in table
    assert "asha@iitgn.ac.in" in table
    assert "guard@iitgn.ac.in" in table


def test_S22_returned_items_are_not_on_public_list(anon, admin, student, add_item, claim_item):
    item = add_item(title="Returned bottle")
    add_item(title="Still here")
    return_item(admin, student, item, claim_item)

    assert "Returned bottle" not in anon.get("/").get_data(as_text=True)
    assert [i["title"] for i in anon.get("/api/items").get_json()] == ["Still here"]
