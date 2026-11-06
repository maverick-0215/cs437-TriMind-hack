import pytest

from lostfound.models import Claim, FoundItem, Handover, Notification

CODE = "482915"


@pytest.fixture(autouse=True)
def fixed_code(monkeypatch):
    monkeypatch.setattr("lostfound.services._six_digit_code", lambda: CODE)


def _claim(client, item, description="Totoro sticker on the back"):
    return client.post(f"/api/items/{item.pk}/claim", {"description": description}, format="json")


def _hand_over(admin_client, item, code):
    return admin_client.post(f"/api/admin/items/{item.pk}/handover", {"code": code}, format="json")


@pytest.fixture
def approved_item(make_item, student_client, admin_client):
    item = make_item()
    _claim(student_client, item)
    admin_client.post(f"/api/admin/claims/{item.claims.get().pk}/approve")
    return item


@pytest.mark.django_db
def test_S16_student_claims_available_item(make_item, student_client, admin_client, student):
    item = make_item()
    assert _claim(student_client, item, "My phone has a Totoro sticker").status_code == 201
    item.refresh_from_db()
    assert item.status == FoundItem.Status.CLAIMED
    assert item.claims.get().student == student
    # The admin sees the claim next to the item's private details.
    detail = admin_client.get(f"/api/admin/items/{item.pk}").json()
    assert detail["claims"][0]["description"] == "My phone has a Totoro sticker"
    assert detail["item"]["exact_location"] == "SECRET-LOCATION desk 14"
    assert detail["item"]["description"] == "SECRET-DESCRIPTION cracked corner"


@pytest.mark.django_db
def test_S16_only_available_items_can_be_claimed(make_item, student_client, other_client):
    item = make_item()
    _claim(student_client, item)
    assert _claim(other_client, item).status_code == 409
    assert Claim.objects.count() == 1


@pytest.mark.django_db
def test_S16_admins_cannot_claim(make_item, admin_client):
    assert _claim(admin_client, make_item()).status_code == 403
    assert not Claim.objects.exists()


@pytest.mark.django_db
def test_S17_approval_creates_code_only_claimant_can_see(approved_item, student_client, other_client, admin_client):
    claim = approved_item.claims.get()
    assert claim.status == Claim.Status.APPROVED and claim.pickup_code == CODE
    assert student_client.get("/api/claims").json()[0]["pickup_code"] == CODE
    assert other_client.get("/api/claims").json() == []
    assert CODE not in admin_client.get(f"/api/admin/items/{approved_item.pk}").content.decode()
    assert CODE not in admin_client.get("/api/admin/claims/pending").content.decode()
    assert not Notification.objects.filter(message__contains=CODE).exists()


@pytest.mark.django_db
def test_S18_rejecting_claim_makes_item_available_and_notifies(make_item, student_client, admin_client, student):
    item = make_item()
    _claim(student_client, item)
    claim = item.claims.get()
    assert admin_client.post(f"/api/admin/claims/{claim.pk}/reject").status_code == 204
    item.refresh_from_db()
    claim.refresh_from_db()
    assert item.status == FoundItem.Status.AVAILABLE
    assert claim.status == Claim.Status.REJECTED
    assert Notification.objects.filter(user=student, message__contains="rejected").exists()


@pytest.mark.django_db
@pytest.mark.parametrize("wrong", ["111111", "48291", "abcdef", "٤٨٢٩١٥"])
def test_S19_wrong_code_is_rejected_and_status_unchanged(approved_item, admin_client, wrong):
    assert _hand_over(admin_client, approved_item, wrong).status_code == 400
    approved_item.refresh_from_db()
    assert approved_item.status == FoundItem.Status.CLAIMED
    assert not Handover.objects.exists()


@pytest.mark.django_db
def test_S19_correct_code_marks_item_returned(approved_item, admin_client):
    assert _hand_over(admin_client, approved_item, CODE).status_code == 201
    approved_item.refresh_from_db()
    assert approved_item.status == FoundItem.Status.RETURNED


@pytest.mark.django_db
def test_S19_code_does_not_work_before_approval(make_item, student_client, admin_client):
    item = make_item()
    _claim(student_client, item)
    assert _hand_over(admin_client, item, CODE).status_code == 400
    item.refresh_from_db()
    assert item.status == FoundItem.Status.CLAIMED


@pytest.mark.django_db
def test_S20_pickup_code_works_only_once(approved_item, admin_client, student_client):
    _hand_over(admin_client, approved_item, CODE)
    assert _hand_over(admin_client, approved_item, CODE).status_code == 400
    assert Handover.objects.count() == 1
    assert student_client.get("/api/claims").json()[0]["pickup_code"] is None


@pytest.mark.django_db
def test_S21_handover_is_logged(approved_item, admin_client, admin_user, student):
    _hand_over(admin_client, approved_item, CODE)
    handover = Handover.objects.get()
    assert (handover.item, handover.student, handover.admin) == (approved_item, student, admin_user)
    assert handover.handed_over_at is not None
    log = admin_client.get("/api/admin/handovers").json()
    assert (log[0]["student"], log[0]["admin"]) == (student.email, admin_user.email)


@pytest.mark.django_db
def test_S22_handed_over_item_leaves_the_list(approved_item, admin_client, student_client):
    _hand_over(admin_client, approved_item, CODE)
    assert student_client.get("/api/items").json() == []
