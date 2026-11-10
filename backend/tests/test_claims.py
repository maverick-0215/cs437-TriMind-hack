import pytest

from django.core import mail
from django.utils import timezone

from lostfound.models import Claim, FoundItem, Handover, Notification

from .conftest import ADMIN_EMAIL

CODE = "482915"


@pytest.fixture(autouse=True)
def fixed_code(monkeypatch):
    monkeypatch.setattr("lostfound.services._six_digit_code", lambda: CODE)


def _approve(admin_client, item, **who):
    return admin_client.post(f"/api/admin/items/{item.pk}/approve", who, format="json")


def _hand_over(admin_client, item, code):
    return admin_client.post(f"/api/admin/items/{item.pk}/handover", {"code": code}, format="json")


@pytest.fixture
def approved_item(make_item, make_report, admin_client):
    item = make_item()
    _approve(admin_client, item, report_id=make_report().pk)
    return item


@pytest.mark.django_db
def test_S14_students_cannot_claim_in_the_app(make_item, student_client):
    item = make_item()
    assert student_client.post(f"/api/items/{item.pk}/claim", {"description": "mine"}, format="json").status_code == 404
    assert student_client.post(f"/api/admin/items/{item.pk}/approve", {"email": "asha@iitgn.ac.in"}).status_code == 403
    assert not Claim.objects.exists()


@pytest.mark.django_db
def test_S16_admin_approves_student_from_matching_report(make_item, make_report, admin_client, student):
    item, report = make_item(), make_report()
    detail = admin_client.get(f"/api/admin/items/{item.pk}").json()
    assert detail["item"]["exact_location"] == "SECRET-LOCATION desk 14"
    assert [c["id"] for c in detail["candidates"]] == [report.pk]
    assert _approve(admin_client, item, report_id=report.pk).status_code == 204
    item.refresh_from_db()
    assert item.status == FoundItem.Status.CLAIMED
    claim = item.claims.get()
    assert (claim.student, claim.status) == (student, Claim.Status.APPROVED)


@pytest.mark.django_db
def test_S16_admin_can_approve_by_email(make_item, admin_client):
    item = make_item()
    assert _approve(admin_client, item, email="Walk.In@iitgn.ac.in").status_code == 204
    assert item.claims.get().student.email == "walk.in@iitgn.ac.in"
    assert _approve(admin_client, make_item(), email="x@gmail.com").status_code == 400
    assert _approve(admin_client, make_item(), email=ADMIN_EMAIL).status_code == 400


@pytest.mark.django_db
def test_S16_only_available_items_can_be_approved(approved_item, admin_client):
    assert _approve(admin_client, approved_item, email="ravi@iitgn.ac.in").status_code == 409
    assert Claim.objects.count() == 1


@pytest.mark.django_db
def test_S17_approval_creates_code_only_that_student_sees(approved_item, student_client, other_client, admin_client, student):
    assert student_client.get("/api/claims").json()[0]["pickup_code"] == CODE
    assert other_client.get("/api/claims").json() == []
    assert CODE not in admin_client.get(f"/api/admin/items/{approved_item.pk}").content.decode()
    assert CODE not in admin_client.get("/api/admin/pickups").content.decode()
    assert Notification.objects.filter(user=student, link="/claims").exists()
    assert not Notification.objects.filter(message__contains=CODE).exists()


@pytest.mark.django_db
def test_S18_cancelling_approval_makes_item_available(approved_item, admin_client, student, student_client):
    claim = approved_item.claims.get()
    assert admin_client.post(f"/api/admin/claims/{claim.pk}/cancel").status_code == 204
    approved_item.refresh_from_db()
    assert approved_item.status == FoundItem.Status.AVAILABLE
    assert student_client.get("/api/claims").json()[0]["pickup_code"] is None
    assert Notification.objects.filter(user=student, message__contains="cancelled").exists()


@pytest.mark.django_db
def test_S18_used_code_cannot_be_cancelled(approved_item, admin_client):
    _hand_over(admin_client, approved_item, CODE)
    assert admin_client.post(f"/api/admin/claims/{approved_item.claims.get().pk}/cancel").status_code == 409


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
def test_S19_code_does_not_work_before_approval(make_item, admin_client):
    item = make_item()
    assert _hand_over(admin_client, item, CODE).status_code == 400
    item.refresh_from_db()
    assert item.status == FoundItem.Status.AVAILABLE


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
def test_S22_returned_item_is_no_longer_a_match(approved_item, admin_client, other_client, other_student, make_report):
    other_report = make_report(student=other_student)
    _hand_over(admin_client, approved_item, CODE)
    assert other_client.get(f"/api/reports/{other_report.pk}").json()["matches"] == []
    assert admin_client.get(f"/api/admin/items/{approved_item.pk}").json()["candidates"] == []


def _report_status(student_client, report):
    return student_client.get(f"/api/reports/{report.pk}").json()


@pytest.mark.django_db
def test_S27_report_closes_when_item_is_collected(make_item, make_report, admin_client, student_client):
    item, report = make_item(), make_report()
    assert _report_status(student_client, report)["status"] == "OPEN"
    _approve(admin_client, item, report_id=report.pk)
    body = _report_status(student_client, report)
    assert body["status"] == "APPROVED" and body["matches"] == []
    _hand_over(admin_client, item, CODE)
    body = _report_status(student_client, report)
    assert body["status"] == "CLOSED" and body["closed_at"] and body["item"]["title"] == "Black phone"
    assert student_client.get("/api/reports").json()[0]["status"] == "CLOSED"


@pytest.mark.django_db
def test_S27_approval_by_email_uses_best_matching_report(make_item, make_report, admin_client, student_client, student):
    item = make_item()
    report = make_report()
    unrelated = make_report(title="Brown wallet", category="Wallet", place_lost="Mess")
    _approve(admin_client, item, email=student.email)
    assert _report_status(student_client, report)["status"] == "APPROVED"
    assert _report_status(student_client, unrelated)["status"] == "OPEN"


@pytest.mark.django_db
def test_S27_cancelling_reopens_report_and_closed_reports_stop_matching(
    make_item, make_report, admin_client, student_client
):
    item, report = make_item(), make_report()
    _approve(admin_client, item, report_id=report.pk)
    admin_client.post(f"/api/admin/claims/{item.claims.get().pk}/cancel")
    assert _report_status(student_client, report)["status"] == "OPEN"
    _approve(admin_client, item, report_id=report.pk)
    _hand_over(admin_client, item, CODE)
    # A closed report is not suggested for a new item, and cannot be approved again.
    other = make_item(title="Black phone again")
    assert admin_client.get(f"/api/admin/items/{other.pk}").json()["candidates"] == []
    assert _approve(admin_client, other, report_id=report.pk).status_code == 409


@pytest.mark.django_db
def test_S17_pickup_code_is_emailed_only_to_that_student(
    make_item, make_report, admin_client, student, admin_user, django_capture_on_commit_callbacks
):
    item, report = make_item(), make_report()
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        _approve(admin_client, item, report_id=report.pk)
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == [student.email]
    assert CODE in message.body and "Black phone" in message.subject
    assert admin_user.email not in message.to + message.cc + message.bcc


@pytest.mark.django_db
def test_S17_person_approved_by_email_gets_the_code_without_signing_in(
    make_item, admin_client, django_capture_on_commit_callbacks
):
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        assert _approve(admin_client, make_item(), email="walk.in@iitgn.ac.in").status_code == 204
    assert [m.to for m in mail.outbox] == [["walk.in@iitgn.ac.in"]]
    assert CODE in mail.outbox[0].body


@pytest.mark.django_db
def test_S17_approval_stands_even_if_the_email_fails(
    make_item, make_report, admin_client, student_client, monkeypatch, django_capture_on_commit_callbacks
):
    import smtplib

    def broken(*args, **kwargs):
        raise smtplib.SMTPServerDisconnected("Connection unexpectedly closed")

    monkeypatch.setattr("lostfound.services.send_mail", broken)
    item = make_item()
    with django_capture_on_commit_callbacks(execute=True):
        assert _approve(admin_client, item, report_id=make_report().pk).status_code == 204
    item.refresh_from_db()
    assert item.status == FoundItem.Status.CLAIMED
    assert student_client.get("/api/claims").json()[0]["pickup_code"] == CODE


@pytest.mark.django_db
def test_S18_cancelled_approval_is_emailed(approved_item, admin_client, student, django_capture_on_commit_callbacks):
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        admin_client.post(f"/api/admin/claims/{approved_item.claims.get().pk}/cancel")
    assert [m.to for m in mail.outbox] == [[student.email]]
    assert "cancelled" in mail.outbox[0].subject.lower()
    assert CODE not in mail.outbox[0].body


@pytest.mark.django_db
def test_collection_is_notified_and_emailed_with_date_and_link(
    approved_item, admin_client, student, settings, django_capture_on_commit_callbacks
):
    settings.SITE_URL = "https://lostfound.example"
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        assert _hand_over(admin_client, approved_item, CODE).status_code == 201
    collected_at = timezone.localtime(approved_item.claims.get().code_used_at).strftime("%d %b %Y, %I:%M %p")
    note = Notification.objects.filter(user=student).latest("id")
    assert collected_at in note.message and note.link == "/reports"
    assert [m.to for m in mail.outbox] == [[student.email]]
    assert collected_at in mail.outbox[0].body
    assert "https://lostfound.example/reports" in mail.outbox[0].body
    assert CODE not in mail.outbox[0].body


@pytest.mark.django_db
def test_wrong_code_sends_no_collection_email(approved_item, admin_client, django_capture_on_commit_callbacks):
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        assert _hand_over(admin_client, approved_item, "000000").status_code == 400
    assert mail.outbox == []


@pytest.mark.django_db(transaction=True)
def test_S27_one_report_cannot_be_approved_for_two_items_at_once(
    make_item, make_report, admin_user, student, monkeypatch
):
    """Issue #19: two admins approve the same report for different items at the same moment."""
    import threading

    from django.db import connection

    from lostfound.models import LostReport
    from lostfound.serializers import ApproveSerializer

    from .conftest import _client

    first, second = make_item(), make_item(title="Black phone again")
    report = make_report()

    # Both requests read the report before either approval is saved.
    both_read = threading.Barrier(2, timeout=10)
    validate = ApproveSerializer.validate

    def validate_then_wait(self, data):
        data = validate(self, data)
        both_read.wait()
        return data

    monkeypatch.setattr(ApproveSerializer, "validate", validate_then_wait)

    codes = []

    def approve(item):
        try:
            codes.append(_approve(_client(admin_user), item, report_id=report.pk).status_code)
        finally:
            connection.close()

    threads = [threading.Thread(target=approve, args=(item,)) for item in (first, second)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(codes) == [204, 409]
    assert Claim.objects.filter(student=student, status=Claim.Status.APPROVED).count() == 1
    approved = Claim.objects.get(student=student).item
    assert LostReport.objects.get(pk=report.pk).linked_item == approved
    assert FoundItem.objects.exclude(pk=approved.pk).get().status == FoundItem.Status.AVAILABLE


@pytest.mark.django_db
def test_S19_sixth_wrong_code_is_refused_even_if_the_next_is_right(approved_item, admin_client):
    for _ in range(5):
        assert _hand_over(admin_client, approved_item, "111111").status_code == 400
    sixth = _hand_over(admin_client, approved_item, "222222")
    assert sixth.status_code == 400 and "Too many wrong codes" in sixth.json()["detail"]
    assert _hand_over(admin_client, approved_item, CODE).status_code == 400
    approved_item.refresh_from_db()
    assert approved_item.status == FoundItem.Status.CLAIMED
    assert not Handover.objects.exists()


@pytest.mark.django_db
def test_S19_right_code_after_a_few_wrong_ones_still_works(approved_item, admin_client):
    for _ in range(4):
        _hand_over(admin_client, approved_item, "111111")
    assert _hand_over(admin_client, approved_item, CODE).status_code == 201


@pytest.mark.django_db
def test_S19_cancel_and_approve_again_gives_fresh_tries(approved_item, admin_client, student):
    for _ in range(5):
        _hand_over(admin_client, approved_item, "111111")
    claim = approved_item.claims.get()
    assert admin_client.post(f"/api/admin/claims/{claim.pk}/cancel").status_code == 204
    _approve(admin_client, approved_item, email=student.email)
    assert _hand_over(admin_client, approved_item, CODE).status_code == 201
