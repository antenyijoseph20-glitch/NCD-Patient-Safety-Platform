import uuid

from django.db import models


class ClinicalNeed(models.Model):
    class Severity(models.TextChoices):
        MILD = "MILD", "Mild"
        MODERATE = "MODERATE", "Moderate"
        SEVERE = "SEVERE", "Severe"
        CRITICAL = "CRITICAL", "Critical"

    class Status(models.TextChoices):
        IDENTIFIED = "IDENTIFIED", "Identified"
        UNDER_EVALUATION = "UNDER_EVALUATION", "Under evaluation"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"
        RESOLVED = "RESOLVED", "Resolved"

    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="clinical_needs",
    )

    condition_name = models.CharField(max_length=255)
    icd10_code = models.CharField(max_length=30, blank=True, default="")

    severity = models.CharField(
        max_length=30,
        choices=Severity.choices,
        default=Severity.MODERATE,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.IDENTIFIED,
    )

    clinical_summary = models.TextField()
    diagnosed_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clinical_need"
        ordering = ["-created_at", "id"]
        indexes = [
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["severity"]),
            models.Index(fields=["condition_name"]),
        ]

    def __str__(self):
        return f"{self.patient}: {self.condition_name} ({self.severity})"


class ClinicalVerification(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending review"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"
        REQUIRES_FURTHER_TESTS = (
            "REQUIRES_FURTHER_TESTS",
            "Requires further tests",
        )

    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    clinical_need = models.ForeignKey(
        ClinicalNeed,
        on_delete=models.PROTECT,
        related_name="verifications",
    )

    professional = models.ForeignKey(
        "organizations.HealthcareProfessional",
        on_delete=models.PROTECT,
        related_name="verifications",
    )

    facility = models.ForeignKey(
        "organizations.Facility",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="clinical_verifications",
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
    )

    verification_notes = models.TextField()
    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clinical_verification"
        ordering = ["-created_at", "id"]
        indexes = [
            models.Index(fields=["clinical_need", "status"]),
            models.Index(fields=["professional", "status"]),
        ]

    def __str__(self):
        return f"Verification for {self.clinical_need} by {self.professional} ({self.status})"
