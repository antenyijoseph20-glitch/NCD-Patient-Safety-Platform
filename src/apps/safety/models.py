import uuid

from django.conf import settings
from django.db import models


class SafetyEvent(models.Model):
    class Severity(models.TextChoices):
        NEAR_MISS = "NEAR_MISS", "Near miss"
        MILD_HARM = "MILD_HARM", "Mild harm"
        MODERATE_HARM = "MODERATE_HARM", "Moderate harm"
        SEVERE_HARM = "SEVERE_HARM", "Severe harm"
        CRITICAL = "CRITICAL", "Critical / Life-threatening"

    class Status(models.TextChoices):
        REPORTED = "REPORTED", "Reported"
        UNDER_INVESTIGATION = (
            "UNDER_INVESTIGATION",
            "Under investigation",
        )
        ESCALATED = "ESCALATED", "Escalated"
        REMEDIATION_PLANNED = (
            "REMEDIATION_PLANNED",
            "Remediation planned",
        )
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"

    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    reference_code = models.CharField(
        max_length=50,
        unique=True,
    )

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="safety_events",
    )

    case = models.ForeignKey(
        "cases.CareSupportCase",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="safety_events",
    )

    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reported_safety_events",
    )

    facility = models.ForeignKey(
        "organizations.Facility",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="safety_events",
    )

    severity = models.CharField(
        max_length=30,
        choices=Severity.choices,
        default=Severity.MODERATE_HARM,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.REPORTED,
    )

    event_description = models.TextField()
    immediate_action_taken = models.TextField(blank=True, default="")

    occurred_at = models.DateTimeField()
    reported_at = models.DateTimeField(auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "safety_event"
        ordering = ["-occurred_at", "id"]
        indexes = [
            models.Index(fields=["reference_code"]),
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["severity"]),
            models.Index(fields=["occurred_at"]),
        ]

    def __str__(self):
        return f"{self.reference_code}: {self.patient} - {self.severity} ({self.status})"
