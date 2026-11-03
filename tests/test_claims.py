import re

from app import db
from app.models import Claim, Handover, Notification


def approve(admin, claim):
    admin.post(f"/admin/claims/{claim.id}/approve")
    db.session.refresh(claim)
    return claim.pickup_code


def handover(admin, item, code):
    admin.post(f"/admin/items/{item.id}/handover", data={"code": code})
    db.session.refresh(item)


def test_S16_student_can_claim_available_item(admin, student, add_item, claim_item):
    item = add_item()
    claim = claim_item(student, item, features="CLAIM-FEATURES red keychain")
    db.session.refresh(item)
    assert item.status == "CLAIMED"
    assert claim.student.email == "asha@iitgn.ac.in"

    page = admin.get(f"/admin/items/{item.id}").get_data(as_text=True)
    assert "CLAIM-FEATURES red keychain" in page
    assert item.description in page and item.exact_location in page


def test_S16_cannot_claim_item_that_is_not_available(student, other, add_item, claim_item):
    item = add_item()
    claim_item(student, item)
    claim_item(other, item)  # item is now CLAIMED
    assert Claim.query.count() == 1


def test_S16_claim_needs_features_and_login(anon, student, add_item):
    item = add_item()
    assert student.post(f"/items/{item.id}/claim", data={"features": ""}).status_code == 400
    assert anon.post(f"/items/{item.id}/claim", data={"features": "x"}).status_code == 302
    assert Claim.query.count() == 0


def test_S17_approval_creates_6_digit_code_only_the_claimant_sees(admin, student, other, add_item, claim_item):
    item = add_item()
    code = approve(admin, claim_item(student, item))
    assert re.fullmatch(r"\d{6}", code)

    assert code in student.get("/claims").get_data(as_text=True)
    for client, url in [(other, "/claims"), (other, "/notifications"), (admin, f"/admin/items/{item.id}"),
                        (admin, "/admin"), (student, "/notifications")]:
        assert code not in client.get(url).get_data(as_text=True), url


def test_S18_rejecting_claim_makes_item_available_and_notifies_student(admin, student, add_item, claim_item):
    item = add_item(title="Rejected bottle")
    claim = claim_item(student, item)
    admin.post(f"/admin/claims/{claim.id}/reject")
    db.session.refresh(item)
    db.session.refresh(claim)

    assert claim.status == "REJECTED"
    assert item.status == "AVAILABLE"
    assert "Rejected bottle" in student.get("/").get_data(as_text=True)
    assert Notification.query.filter_by(user_id=claim.student_id).count() == 1
    assert "rejected" in student.get("/notifications").get_data(as_text=True)


def test_S19_wrong_code_is_rejected_and_status_unchanged(admin, student, add_item, claim_item):
    item = add_item()
    code = approve(admin, claim_item(student, item))
    wrong = f"{(int(code) + 1) % 10**6:06d}"
    for bad in [wrong, "", "abcdef"]:
        handover(admin, item, bad)
        assert item.status == "CLAIMED"
    assert Handover.query.count() == 0


def test_S19_correct_code_marks_item_returned(admin, student, add_item, claim_item):
    item = add_item()
    handover(admin, item, approve(admin, claim_item(student, item)))
    assert item.status == "RETURNED"


def test_S19_code_does_not_work_before_approval(admin, student, add_item, claim_item):
    item = add_item()
    claim = claim_item(student, item)
    handover(admin, item, "000000")
    assert item.status == "CLAIMED"
    assert claim.pickup_code is None


def test_S20_pickup_code_works_only_once(admin, student, add_item, claim_item):
    item = add_item()
    claim = claim_item(student, item)
    code = approve(admin, claim)
    handover(admin, item, code)
    handover(admin, item, code)
    db.session.refresh(claim)
    assert claim.code_used_at is not None
    assert Handover.query.count() == 1
