from rest_framework import serializers

from .models import Category, Claim, FoundItem, Handover, LostReport, Notification


class PublicItemSerializer(serializers.ModelSerializer):
    """The only item fields non-admins ever receive (S6, S7)."""

    class Meta:
        model = FoundItem
        fields = ["id", "category", "title", "date_found", "general_area"]


class AdminItemSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(write_only=True, required=False)
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

    def get_has_photo(self, item):
        return bool(item.photo)


class ReportSerializer(serializers.ModelSerializer):
    linked_item = PublicItemSerializer(read_only=True)

    class Meta:
        model = LostReport
        fields = ["id", "category", "title", "date_lost", "place_lost", "private_details", "linked_item", "created_at"]


class AdminReportSerializer(serializers.ModelSerializer):
    student = serializers.EmailField(source="student.email")

    class Meta:
        model = LostReport
        fields = ["id", "category", "title", "date_lost", "place_lost", "private_details", "student", "linked_item"]


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


class ItemFilterSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=Category.choices, required=False, allow_blank=True)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    q = serializers.CharField(required=False, allow_blank=True, max_length=100)


class ClaimCreateSerializer(serializers.Serializer):
    description = serializers.CharField()


class LinkSerializer(serializers.Serializer):
    report_id = serializers.PrimaryKeyRelatedField(queryset=LostReport.objects.all(), source="report")


class PickupCodeSerializer(serializers.Serializer):
    # [0-9], not \d: \d also matches non-ASCII digits, which compare_digest rejects.
    code = serializers.RegexField(r"^[0-9]{6}$", error_messages={"invalid": "Enter the 6-digit pickup code."})
