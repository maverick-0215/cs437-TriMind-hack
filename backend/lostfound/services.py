import logging
import re
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import Claim, FoundItem, Handover, LostReport, Notification

logger = logging.getLogger(__name__)


class ClaimError(Exception):
    pass


def _six_digit_code():
    return f"{secrets.randbelow(10**6):06d}"


def notify(user, message, link=""):
    Notification.objects.create(user=user, message=message, link=link)


def email_after_save(user, subject, body):
    """Email someone once the current transaction is saved. Sending waits for the mail server,
    so it must not hold the database open, and it must not go out for a change that was
    rolled back. A failed email is logged; the change itself stays."""

    def send():
        try:
            send_mail(subject, body, None, [user.email])
        except OSError:
            logger.exception("Could not send %r to %s", subject, user.email)

    transaction.on_commit(send)


# --- Duplicate submissions (S32) ---

# A double click, or a retry on a slow connection, sends the same form again within moments.
DUPLICATE_WINDOW = timedelta(minutes=2)
REPORT_FIELDS = ("category", "title", "date_lost", "place_lost", "private_details")
ITEM_FIELDS = ("category", "title", "date_found", "general_area", "exact_location", "description")


def lock_user(user):
    """Make one person's simultaneous submissions take turns, so a double click arriving in
    parallel cannot slip past the duplicate check. Call inside transaction.atomic().
    PostgreSQL locks the user's row; SQLite (no row locks) already serialises writes."""
    get_user_model().objects.select_for_update().filter(pk=user.pk).first()


def recent_duplicate_report(student, data):
    """S32: the same lost report from the same student in the last two minutes, if any."""
    return LostReport.objects.filter(
        student=student,
        created_at__gte=timezone.now() - DUPLICATE_WINDOW,
        **{field: data[field] for field in REPORT_FIELDS},
    ).first()


def recent_duplicate_item(admin, data):
    """S32: the same found item from the same admin in the last two minutes, if any."""
    return FoundItem.objects.filter(
        added_by=admin,
        created_at__gte=timezone.now() - DUPLICATE_WINDOW,
        **{field: data[field] for field in ITEM_FIELDS},
    ).first()


# --- Matching (S13, S25, S26) ---

MATCH_THRESHOLD = 60  # percent

# Words that say nothing about the item itself.
_STOPWORDS = {
    "a", "an", "the", "my", "i", "lost", "found", "of", "in", "on", "at", "near", "with", "and", "or",
    "is", "it", "to", "for", "from", "by", "some", "one", "new", "old",
}


def _words(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOPWORDS and len(w) > 1}


def _overlap(a, b):
    """Share of the smaller word set that also appears in the other, 0 to 1."""
    a, b = _words(a), _words(b)
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def match_score(report, item):
    """S13: how well a found item fits a lost report, 0 to 100. Uses only public item fields,
    so a student cannot learn private details by probing with reports."""
    score = 40 if report.category == item.category else 0
    # The item's category counts as a word too, so "Umbrella" matches a "Blue brolly" in Umbrella.
    # Not on both sides, or every same-category pair would share a word for free.
    score += 30 * _overlap(report.title, f"{item.title} {item.category}")
    score += 15 * _overlap(report.place_lost, item.general_area)
    days = (item.date_found - report.date_lost).days
    if 0 <= days <= 7:
        score += 15
    elif 0 <= days <= 30:
        score += 8
    elif days > 30:
        score += 3
    # Found before it was lost (more than a day early) earns nothing for date.
    return round(min(score, 100))


def available_items():
    """S6: every found item still at the security office, newest first."""
    return FoundItem.objects.filter(status=FoundItem.Status.AVAILABLE).select_related("added_by").order_by(
        "-date_found", "-created_at"
    )


def matching_items(report):
    """S25: AVAILABLE items matching the report by at least MATCH_THRESHOLD, best first."""
    items = FoundItem.objects.filter(status=FoundItem.Status.AVAILABLE).select_related("added_by")
    scored = [(item, match_score(report, item)) for item in items]
    return sorted([m for m in scored if m[1] >= MATCH_THRESHOLD], key=lambda m: (-m[1], -m[0].pk))


def matching_reports(item):
    """S13: open lost reports matching the item by at least MATCH_THRESHOLD, best first.
    A report linked to an item is approved or closed (S27), so it is left out."""
    reports = LostReport.objects.filter(linked_item__isnull=True).select_related("student")
    scored = [(report, match_score(report, item)) for report in reports]
    return sorted([m for m in scored if m[1] >= MATCH_THRESHOLD], key=lambda m: (-m[1], -m[0].pk))


def notify_matching_reports(item):
    """S26: tell each student whose report matches a newly added item."""
    for report, score in matching_reports(item):
        notify(
            report.student,
            f'A found item "{item.title}" matches your lost report "{report.title}" ({score}%). '
            "Open the report to see where to collect it.",
            f"/reports/{report.pk}",
        )


# --- Approval and handover (S16-S21) ---


@transaction.atomic
def approve_owner(item, student, admin, report=None):
    """S16, S17: after checking the student in person, the admin approves them as the owner.
    S27: the approval is tied to the student's lost report, so it closes on handover. Without a
    report given, their best open matching report is used, if they have one."""
    item = FoundItem.objects.select_for_update().get(pk=item.pk)
    if item.status != FoundItem.Status.AVAILABLE:
        raise ClaimError("This item is already approved for someone or returned.")
    if report is None:
        own = [(r, s) for r, s in matching_reports(item) if r.student_id == student.pk]
        report = own[0][0] if own else None
    elif report.linked_item_id is not None:
        raise ClaimError("That lost report is already approved for another item or closed.")
    if report is not None:
        report.linked_item = item
        report.save(update_fields=["linked_item"])
    claim = Claim.objects.create(
        item=item,
        student=student,
        description="Checked in person by the security office.",
        status=Claim.Status.APPROVED,
        decided_by=admin,
        decided_at=timezone.now(),
        pickup_code=_six_digit_code(),
    )
    item.status = FoundItem.Status.CLAIMED
    item.save(update_fields=["status"])
    notify(
        student,
        f'You were approved to collect "{item.title}". Your pickup code is on Pickup codes. Tell it to the guard.',
        "/claims",
    )
    # S17: the code also goes to the student's own inbox, so someone approved by email who has
    # not signed in yet still gets it. Never to admins, never in a notification.
    email_after_save(
        student,
        f'Your pickup code for "{item.title}"',
        f'You have been approved to collect "{item.title}" from the IITGN security office.\n\n'
        f"Your pickup code: {claim.pickup_code}\n\n"
        "Tell this code to the guard when you collect the item. It works only once.\n"
        f"You can also see it on the Pickup codes page: {settings.SITE_URL}/claims\n\n"
        "If you did not lose this item, ignore this email.",
    )
    return claim


@transaction.atomic
def cancel_approval(claim, admin):
    """S18: an approval made by mistake can be cancelled until the code is used."""
    claim = Claim.objects.select_for_update().select_related("item").get(pk=claim.pk)
    if not claim.code_is_active:
        raise ClaimError("This approval can no longer be cancelled.")
    claim.status = Claim.Status.REJECTED
    claim.decided_by = admin
    claim.decided_at = timezone.now()
    claim.save()
    claim.item.status = FoundItem.Status.AVAILABLE
    claim.item.save(update_fields=["status"])
    # S27: the report is open again.
    LostReport.objects.filter(linked_item=claim.item, student=claim.student).update(linked_item=None)
    notify(claim.student, f'Your approval to collect "{claim.item.title}" was cancelled.', "/claims")
    email_after_save(
        claim.student,
        f'Approval cancelled for "{claim.item.title}"',
        f'The security office cancelled your approval to collect "{claim.item.title}". '
        "The pickup code you were sent no longer works.\n\n"
        "If you think this is a mistake, contact the security office.",
    )


@transaction.atomic
def hand_over(item, code, admin):
    item = FoundItem.objects.select_for_update().get(pk=item.pk)
    claim = item.claims.filter(status=Claim.Status.APPROVED, code_used_at__isnull=True).first()
    if (
        item.status != FoundItem.Status.CLAIMED
        or claim is None
        or not secrets.compare_digest(claim.pickup_code, code)
    ):
        raise ClaimError("Wrong or already used pickup code.")
    claim.code_used_at = timezone.now()
    claim.save(update_fields=["code_used_at"])
    item.status = FoundItem.Status.RETURNED
    item.save(update_fields=["status"])
    return Handover.objects.create(item=item, student=claim.student, admin=admin)
