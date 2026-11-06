import secrets

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import Claim, FoundItem, Handover, LostReport, Notification


class ClaimError(Exception):
    pass


def _six_digit_code():
    return f"{secrets.randbelow(10**6):06d}"


def notify(user, message, link=""):
    Notification.objects.create(user=user, message=message, link=link)


# --- Found-items list (S6, S8-S10, S22) ---


def available_items(category="", date_from=None, date_to=None, q=""):
    items = FoundItem.objects.filter(status=FoundItem.Status.AVAILABLE)
    if category:
        items = items.filter(category=category)
    if date_from:
        items = items.filter(date_found__gte=date_from)
    if date_to:
        items = items.filter(date_found__lte=date_to)
    if q:
        items = items.filter(Q(title__icontains=q) | Q(category__icontains=q))
    return items.order_by("-date_found", "-created_at")


# --- Matching (S13-S15) ---


def suggest_reports(item):
    return LostReport.objects.filter(
        linked_item__isnull=True,
        category=item.category,
        date_lost__lte=item.date_found,
    ).select_related("student")


def link_report(report, item):
    # S14: any report, including one already linked elsewhere, so a wrong link can be fixed.
    report.linked_item = item
    report.save(update_fields=["linked_item"])
    notify(
        report.student,
        f'A found item may match your lost report "{report.title}". Claim it if it is yours.',
        f"/reports/{report.pk}",
    )


# --- Claims and handover (S16-S21) ---


@transaction.atomic
def create_claim(item, student, description):
    item = FoundItem.objects.select_for_update().get(pk=item.pk)
    if item.status != FoundItem.Status.AVAILABLE:
        raise ClaimError("This item is no longer available to claim.")
    claim = Claim.objects.create(item=item, student=student, description=description)
    item.status = FoundItem.Status.CLAIMED
    item.save(update_fields=["status"])
    return claim


def _decide(claim, admin, status):
    claim = Claim.objects.select_for_update().select_related("item").get(pk=claim.pk)
    if claim.status != Claim.Status.PENDING:
        raise ClaimError("This claim was already reviewed.")
    claim.status = status
    claim.decided_by = admin
    claim.decided_at = timezone.now()
    return claim


@transaction.atomic
def approve_claim(claim, admin):
    claim = _decide(claim, admin, Claim.Status.APPROVED)
    claim.pickup_code = _six_digit_code()
    claim.save()
    notify(
        claim.student,
        f'Your claim for "{claim.item.title}" was approved. Your pickup code is on My claims.',
        "/claims",
    )


@transaction.atomic
def reject_claim(claim, admin):
    claim = _decide(claim, admin, Claim.Status.REJECTED)
    claim.save()
    claim.item.status = FoundItem.Status.AVAILABLE
    claim.item.save(update_fields=["status"])
    notify(claim.student, f'Your claim for "{claim.item.title}" was rejected.', "/claims")


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
