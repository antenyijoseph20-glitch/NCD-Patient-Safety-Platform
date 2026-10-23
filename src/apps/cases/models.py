import uuid

from django.conf import settings
from django.db import models


class CareSupportCase(models.Model):
    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        EMERGENCY = "EMERGENCY", "Emergency"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLINICAL_REVIEW = "CLINICAL_REVIEW", "Clinical review"
        FUNDING_ELIGIBLE = "FUNDING_ELIGIBLE", "Funding eligible"
        ASSISTANCE_ACTIVE = "ASSISTANCE_ACTIVE", "Assistance active"
        SUSPENDED = "SUSPENDED", "Suspended"
        CLOSED = "CLOSED", "Closed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    case_number = models.CharField(
        max_length=50,
        unique=True,
    )

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="care_cases",
    )

    primary_clinical_need = models.ForeignKey(
        "clinical_need.ClinicalNeed",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="care_cases",
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")

    priority = models.CharField(
        max_length=30,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.OPEN,
    )

    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "care_support_case"
        ordering = ["-opened_at", "id"]
        indexes = [
            models.Index(fields=["case_number"]),
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["priority"]),
        ]

    def __str__(self):
        return f"{self.case_number}: {self.title} ({self.status})"
