from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from . import services
from .models import Claim, FoundItem, Handover, LostReport
from .permissions import IsAdmin, IsStudent
from .serializers import (
    AdminClaimSerializer,
    AdminItemSerializer,
    AdminReportSerializer,
    ClaimCreateSerializer,
    HandoverSerializer,
    ItemFilterSerializer,
    LinkSerializer,
    MyClaimSerializer,
    NotificationSerializer,
    PickupCodeSerializer,
    PublicItemSerializer,
    ReportSerializer,
)


def _error(exc, code=status.HTTP_409_CONFLICT):
    return Response({"detail": str(exc)}, status=code)


# --- Any logged-in user (S23: everything here needs login) ---


@api_view(["GET"])
def items(request):
    """S6-S10: AVAILABLE items, public fields only, newest first."""
    filters = ItemFilterSerializer(data=request.query_params)
    filters.is_valid(raise_exception=True)
    return Response(PublicItemSerializer(services.available_items(**filters.validated_data), many=True).data)


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
        serializer.save(student=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    # S12: only the student's own reports.
    return Response(ReportSerializer(request.user.lost_reports.select_related("linked_item"), many=True).data)


@api_view(["GET"])
@permission_classes([IsStudent])
def report_detail(request, pk):
    # S12: another student's report is a 404.
    return Response(ReportSerializer(get_object_or_404(request.user.lost_reports, pk=pk)).data)


@api_view(["POST"])
@permission_classes([IsStudent])
def claim_item(request, pk):
    item = get_object_or_404(FoundItem, pk=pk)
    serializer = ClaimCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        claim = services.create_claim(item, request.user, serializer.validated_data["description"])
    except services.ClaimError as e:
        return _error(e)
    return Response(MyClaimSerializer(claim).data, status=status.HTTP_201_CREATED)


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
        serializer.save(added_by=request.user)  # S5: status defaults to AVAILABLE
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(AdminItemSerializer(FoundItem.objects.select_related("added_by"), many=True).data)


@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_item_detail(request, pk):
    item = get_object_or_404(FoundItem.objects.select_related("added_by"), pk=pk)
    awaiting = item.claims.filter(status=Claim.Status.APPROVED, code_used_at__isnull=True).first()
    handover = Handover.objects.filter(item=item).select_related("item", "student", "admin").first()
    returned = item.status == FoundItem.Status.RETURNED
    return Response(
        {
            "item": AdminItemSerializer(item).data,
            "claims": AdminClaimSerializer(item.claims.select_related("student", "item"), many=True).data,
            "awaiting_pickup_by": awaiting.student.email if awaiting else None,
            "handover": HandoverSerializer(handover).data if handover else None,
            # S13: suggestions are shown as soon as the item exists.
            "suggestions": [] if returned else AdminReportSerializer(services.suggest_reports(item), many=True).data,
            "linked_reports": AdminReportSerializer(item.linked_reports.select_related("student"), many=True).data,
            "link_options": AdminReportSerializer(
                LostReport.objects.exclude(linked_item=item).select_related("student"), many=True
            ).data,
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
def admin_item_link(request, pk):
    item = get_object_or_404(FoundItem, pk=pk)
    serializer = LinkSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    services.link_report(serializer.validated_data["report"], item)
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
def admin_pending_claims(request):
    pending = Claim.objects.filter(status=Claim.Status.PENDING).select_related("item", "student")
    return Response(AdminClaimSerializer(pending, many=True).data)


@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_claim_approve(request, pk):
    try:
        services.approve_claim(get_object_or_404(Claim, pk=pk), request.user)
    except services.ClaimError as e:
        return _error(e)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_claim_reject(request, pk):
    try:
        services.reject_claim(get_object_or_404(Claim, pk=pk), request.user)
    except services.ClaimError as e:
        return _error(e)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_handovers(request):
    log = Handover.objects.select_related("item", "student", "admin")
    return Response(HandoverSerializer(log, many=True).data)
