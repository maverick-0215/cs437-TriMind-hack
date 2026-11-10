from django.conf import settings
from django.db import models


class Category(models.TextChoices):
    # Values double as display text so keyword search can match them (S10).
    ELECTRONICS = "Electronics", "Electronics"
    ID_CARD = "ID card", "ID card"
    WALLET = "Wallet", "Wallet"
    KEYS = "Keys", "Keys"
    BOTTLE = "Bottle", "Bottle"
    BAG = "Bag", "Bag"
    UMBRELLA = "Umbrella", "Umbrella"
    CLOTHING = "Clothing", "Clothing"
    BOOKS = "Books & stationery", "Books & stationery"
    CYCLE = "Cycle", "Cycle"
    ACCESSORIES = "Jewellery & watches", "Jewellery & watches"
    OTHER = "Other", "Other"


class FoundItem(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE"
        CLAIMED = "CLAIMED"
        RETURNED = "RETURNED"

    # Public fields (S6).
    category = models.CharField(max_length=32, choices=Category.choices)
    title = models.CharField(max_length=120)
    date_found = models.DateField()
    general_area = models.CharField(max_length=120)
    # Private fields, admins only (S4, S7).
    exact_location = models.CharField(max_length=200)
    description = models.TextField()
    photo = models.ImageField(upload_to="found_photos/", blank=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.AVAILABLE)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="items_added")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_found", "-created_at"]


class LostReport(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lost_reports")
    category = models.CharField(max_length=32, choices=Category.choices)
    title = models.CharField(max_length=120)
    date_lost = models.DateField()
    place_lost = models.CharField(max_length=200)
    private_details = models.TextField()
    # S33: optional, private like private_details: only the student and admins see it.
    photo = models.ImageField(upload_to="report_photos/", blank=True)
    linked_item = models.ForeignKey(
        FoundItem, null=True, blank=True, on_delete=models.SET_NULL, related_name="linked_reports"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Claim(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING"
        APPROVED = "APPROVED"
        REJECTED = "REJECTED"

    item = models.ForeignKey(FoundItem, on_delete=models.PROTECT, related_name="claims")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="claims")
    description = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="claims_decided"
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    # S17: shown only to the claiming student. S20: works once.
    pickup_code = models.CharField(max_length=6, blank=True)
    code_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def code_is_active(self):
        return self.status == self.Status.APPROVED and self.code_used_at is None


class Handover(models.Model):
    # S21: item, student, admin, date and time.
    item = models.OneToOneField(FoundItem, on_delete=models.PROTECT, related_name="handover")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="handovers_received")
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="handovers_given")
    handed_over_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-handed_over_at"]


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=300)
    # Frontend path to open, e.g. "/claims".
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class AdminEmail(models.Model):
    """S28: an admin added from inside the app. Emails in ADMIN_EMAILS (.env) are admins too."""

    email = models.EmailField(unique=True)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="admins_added")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["email"]

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)
