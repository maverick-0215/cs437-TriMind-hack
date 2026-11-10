from django.utils import timezone
from rest_framework import serializers

from .models import AdminEmail, Claim, FoundItem, Handover, LostReport, Notification


def not_in_future(value):
    """S31: an item cannot be lost or found after today (campus time, Asia/Kolkata)."""
    if value > timezone.localdate():
        raise serializers.ValidationError("The date cannot be in the future.")
    return value


MAX_PHOTO_MB = 5


def photo_not_too_big(photo):
    """S4, S33: photos are at most 5 MB, so uploads cannot fill the disk."""
    if photo.size > MAX_PHOTO_MB * 1024 * 1024:
        raise serializers.ValidationError(f"The photo must be {MAX_PHOTO_MB} MB or smaller.")
    return photo


class PublicItemSerializer(serializers.ModelSerializer):
    """The only item fields non-admins ever receive (S6, S7)."""

    class Meta:
        model = FoundItem
        fields = ["id", "category", "title", "date_found", "general_area"]


class AdminItemSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(write_only=True, required=False, validators=[photo_not_too_big])
    has_photo = serializers.SerializerMethodField()
    added_by = serializers.EmailField(source="added_by.email", read_only=True)

    class Meta:
        model = FoundItem
        fields = [
            "id", "category", "title", "date_found", "general_area",
            "exact_location", "description", "photo", "has_photo",
            "status", "added_by", "created_at",
        ]
        read_only_fields = ["status", "created_at"]
        extra_kwargs = {"date_found": {"validators": [not_in_future]}}

    def get_has_photo(self, item):
        return bool(item.photo)


class ReportSerializer(serializers.ModelSerializer):
    # S27: OPEN, APPROVED (waiting for pickup) or CLOSED (collected).
    status = serializers.SerializerMethodField()
    closed_at = serializers.SerializerMethodField()
    item = PublicItemSerializer(source="linked_item", read_only=True)
    # S33: an optional photo, served only by /api/reports/<id>/photo.
    photo = serializers.ImageField(write_only=True, required=False, validators=[photo_not_too_big])
    has_photo = serializers.SerializerMethodField()

    class Meta:
        model = LostReport
        fields = [
            "id", "category", "title", "date_lost", "place_lost", "private_details", "photo", "has_photo",
            "created_at", "status", "closed_at", "item",
        ]
        extra_kwargs = {"date_lost": {"validators": [not_in_future]}}

    def get_status(self, report):
        if report.linked_item is None:
            return "OPEN"
        return "CLOSED" if report.linked_item.status == FoundItem.Status.RETURNED else "APPROVED"

    def get_has_photo(self, report):
        return bool(report.photo)

    def get_closed_at(self, report):
        handover = getattr(report.linked_item, "handover", None) if report.linked_item else None
        return handover.handed_over_at if handover else None


class AdminReportSerializer(serializers.ModelSerializer):
    student = serializers.EmailField(source="student.email")
    has_photo = serializers.SerializerMethodField()

    class Meta:
        model = LostReport
        fields = ["id", "category", "title", "date_lost", "place_lost", "private_details", "has_photo", "student"]

    def get_has_photo(self, report):
        return bool(report.photo)


class MyClaimSerializer(serializers.ModelSerializer):
    item = PublicItemSerializer()
    pickup_code = serializers.SerializerMethodField()

    class Meta:
        model = Claim
        fields = ["id", "item", "status", "created_at", "pickup_code", "code_used_at"]

    def get_pickup_code(self, claim):
        # S17: only the claimant sees it, and only until it is used.
        return claim.pickup_code if claim.code_is_active else None


class AdminClaimSerializer(serializers.ModelSerializer):
    """No pickup_code here: admins must get it from the student (S17)."""

    student = serializers.EmailField(source="student.email")
    item = PublicItemSerializer()

    class Meta:
        model = Claim
        fields = ["id", "item", "student", "description", "status", "created_at"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "link", "is_read", "created_at"]


class HandoverSerializer(serializers.ModelSerializer):
    item = PublicItemSerializer()
    student = serializers.EmailField(source="student.email")
    admin = serializers.EmailField(source="admin.email")

    class Meta:
        model = Handover
        fields = ["id", "item", "student", "admin", "handed_over_at"]


class ApproveSerializer(serializers.Serializer):
    """Who the admin approves: a student from a matching report, or any IITGN email."""

    report_id = serializers.PrimaryKeyRelatedField(
        queryset=LostReport.objects.select_related("student"), source="report", required=False
    )
    email = serializers.EmailField(required=False)

    def validate(self, data):
        if ("report" in data) == ("email" in data):
            raise serializers.ValidationError("Give either a lost report or an email.")
        return data


class PickupCodeSerializer(serializers.Serializer):
    # [0-9], not \d: \d also matches non-ASCII digits, which compare_digest rejects.
    code = serializers.RegexField(r"^[0-9]{6}$", error_messages={"invalid": "Enter the 6-digit pickup code."})


class AdminEmailSerializer(serializers.ModelSerializer):
    added_by = serializers.EmailField(source="added_by.email", read_only=True)

    class Meta:
        model = AdminEmail
        fields = ["id", "email", "added_by", "created_at"]
        read_only_fields = ["created_at"]
        # Duplicates are checked in the view, which also knows about ADMIN_EMAILS.
        extra_kwargs = {"email": {"validators": []}}
