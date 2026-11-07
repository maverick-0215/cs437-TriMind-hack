from django.conf import settings
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from . import services
from .auth_views import get_or_create_user
from .models import AdminEmail, Claim, FoundItem, Handover
from .permissions import IsAdmin, IsStudent, email_allowed, is_admin, is_admin_email
from .serializers import (
    AdminClaimSerializer,
    AdminEmailSerializer,
    AdminItemSerializer,
    AdminReportSerializer,
    ApproveSerializer,
    HandoverSerializer,
    MatchItemSerializer,
    MyClaimSerializer,
    NotificationSerializer,
    PickupCodeSerializer,
    ReportSerializer,
)


def _error(exc, code=status.HTTP_409_CONFLICT):
    return Response({"detail": str(exc)}, status=code)


# --- Any logged-in user (S23: everything here needs login) ---


@api_view(["GET"])
def notifications(request):
    return Response(NotificationSerializer(request.user.notifications.all(), many=True).data)


@api_view(["POST"])
def notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return Response(status=status.HTTP_204_NO_CONTENT)


# --- Students ---


@api_view(["GET", "POST"])
@permission_classes([IsStudent])
def reports(request):
    if request.method == "POST":
        serializer = ReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            services.lock_user(request.user)
            # S32: sent twice by mistake? Return the report already saved instead of a copy.
            if existing := services.recent_duplicate_report(request.user, serializer.validated_data):
                return Response(ReportSerializer(existing).data, status=status.HTTP_200_OK)
            serializer.save(student=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    # S12: only the student's own reports.
    return Response(ReportSerializer(request.user.lost_reports.select_related("linked_item__handover"), many=True).data)


@api_view(["GET"])
@permission_classes([IsStudent])
def report_detail(request, pk):
    # S12: another student's report is a 404.
    report = get_object_or_404(request.user.lost_reports.select_related("linked_item__handover"), pk=pk)
    return Response(
        {
            **ReportSerializer(report).data,
            # S25: found items that may be theirs, with who to contact.
            # S27: a closed or approved report needs no more matches.
            "matches": []
            if report.linked_item_id
            else [{**MatchItemSerializer(item).data, "score": score} for item, score in services.matching_items(report)],
            "security_contact": settings.SECURITY_CONTACT,
        }
    )


@api_view(["GET"])
@permission_classes([IsStudent])
def my_claims(request):
    return Response(MyClaimSerializer(request.user.claims.select_related("item"), many=True).data)


# --- Admins (S3) ---


@api_view(["GET", "POST"])
@permission_classes([IsAdmin])
def admin_items(request):
    if request.method == "POST":
        serializer = AdminItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            services.lock_user(request.user)
            # S32: sent twice by mistake? Return the item already saved, and notify no one again.
            if existing := services.recent_duplicate_item(request.user, serializer.validated_data):
                return Response(AdminItemSerializer(existing).data, status=status.HTTP_200_OK)
            item = serializer.save(added_by=request.user)  # S5: status defaults to AVAILABLE
        services.notify_matching_reports(item)  # S26
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(AdminItemSerializer(FoundItem.objects.select_related("added_by"), many=True).data)


@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_item_detail(request, pk):
    item = get_object_or_404(FoundItem.objects.select_related("added_by"), pk=pk)
    awaiting = item.claims.filter(status=Claim.Status.APPROVED, code_used_at__isnull=True).first()
    handover = Handover.objects.filter(item=item).select_related("item", "student", "admin").first()
    return Response(
        {
            "item": AdminItemSerializer(item).data,
            "claims": AdminClaimSerializer(item.claims.select_related("student", "item"), many=True).data,
            "awaiting_pickup_by": awaiting.student.email if awaiting else None,
            "handover": HandoverSerializer(handover).data if handover else None,
            # S13: students whose lost reports match, for the admin to check in person.
            "candidates": []
            if item.status != FoundItem.Status.AVAILABLE
            else [{**AdminReportSerializer(r).data, "score": score} for r, score in services.matching_reports(item)],
        }
    )


@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_item_photo(request, pk):
    # S7: photos are only served through this admin endpoint.
    item = get_object_or_404(FoundItem, pk=pk)
    if not item.photo:
        raise Http404
    return FileResponse(item.photo.open("rb"))


@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_item_approve(request, pk):
    """S16: approve the person the admin checked in person; they get a pickup code."""
    item = get_object_or_404(FoundItem, pk=pk)
    serializer = ApproveSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if "report" in serializer.validated_data:
        student = serializer.validated_data["report"].student
    else:
        email = serializer.validated_data["email"].strip().lower()
        if not email_allowed(email):
            return _error("Only @iitgn.ac.in emails can be approved.", status.HTTP_400_BAD_REQUEST)
        # Same account the person gets when they sign in.
        student = get_or_create_user(email)
    if is_admin(student):
        return _error("Security office accounts cannot collect items.", status.HTTP_400_BAD_REQUEST)
    try:
        services.approve_owner(item, student, request.user, serializer.validated_data.get("report"))
    except services.ClaimError as e:
        return _error(e)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_item_handover(request, pk):
    item = get_object_or_404(FoundItem, pk=pk)
    serializer = PickupCodeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        handover = services.hand_over(item, serializer.validated_data["code"], request.user)
    except services.ClaimError as e:
        return _error(e, status.HTTP_400_BAD_REQUEST)
    return Response(HandoverSerializer(handover).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_pickups(request):
    """Approved people who have not collected yet."""
    waiting = Claim.objects.filter(status=Claim.Status.APPROVED, code_used_at__isnull=True).select_related(
        "item", "student"
    )
    return Response(AdminClaimSerializer(waiting, many=True).data)


@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_claim_cancel(request, pk):
    try:
        services.cancel_approval(get_object_or_404(Claim, pk=pk), request.user)
    except services.ClaimError as e:
        return _error(e)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_handovers(request):
    log = Handover.objects.select_related("item", "student", "admin")
    return Response(HandoverSerializer(log, many=True).data)


@api_view(["GET", "POST"])
@permission_classes([IsAdmin])
def admin_admins(request):
    """S28: list admins, or add one by email."""
    if request.method == "POST":
        serializer = AdminEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        if not email_allowed(email):
            return _error("Only @iitgn.ac.in emails can be admins.", status.HTTP_400_BAD_REQUEST)
        if is_admin_email(email):
            return _error(f"{email} is already an admin.")
        admin = serializer.save(email=email, added_by=request.user)
        return Response(AdminEmailSerializer(admin).data, status=status.HTTP_201_CREATED)
    return Response(
        {
            # From .env: permanent, so the office can never be locked out.
            "permanent": sorted(settings.ADMIN_EMAILS),
            "added": AdminEmailSerializer(AdminEmail.objects.select_related("added_by"), many=True).data,
        }
    )


@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_admin_remove(request, pk):
    """S28: remove an admin added in the app. ADMIN_EMAILS can only be changed in .env."""
    admin = get_object_or_404(AdminEmail, pk=pk)
    if admin.email == request.user.email.lower():
        return _error("You cannot remove yourself. Ask another admin.", status.HTTP_400_BAD_REQUEST)
    admin.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
