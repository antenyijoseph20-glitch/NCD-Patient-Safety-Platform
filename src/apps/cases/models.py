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


class CaseAssignment(models.Model):
    class Role(models.TextChoices):
        CASE_OFFICER = "CASE_OFFICER", "Case officer"
        CLINICAL_LEAD = "CLINICAL_LEAD", "Clinical lead"
        CAREGIVER_LIAISON = "CAREGIVER_LIAISON", "Caregiver liaison"
        AUDITOR = "AUDITOR", "Auditor"

    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    case = models.ForeignKey(
        CareSupportCase,
        on_delete=models.CASCADE,
        related_name="assignments",
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="case_assignments",
    )

    role = models.CharField(
        max_length=50,
        choices=Role.choices,
        default=Role.CASE_OFFICER,
    )

    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "case_assignment"
        ordering = ["case", "-is_active", "-assigned_at", "id"]
        indexes = [
            models.Index(fields=["case", "is_active"]),
            models.Index(fields=["assigned_to", "is_active"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.case.case_number} -> {self.assigned_to} ({self.role})"


class MentalHealthScreening(models.Model):
    """
    Holistic Chronic Care: Psychological and mental health evaluation
    for people living with chronic noncommunicable diseases.
    Supports PHQ-9 (Depression) and GAD-7 (Anxiety) standard clinical instruments.
    """
    class ScreeningTool(models.TextChoices):
        PHQ9 = "PHQ9", "Patient Health Questionnaire (PHQ-9) - Depression"
        GAD7 = "GAD7", "Generalized Anxiety Disorder (GAD-7) - Anxiety"

    class Severity(models.TextChoices):
        MINIMAL = "MINIMAL", "Minimal / None (Score 0-4)"
        MILD = "MILD", "Mild (Score 5-9)"
        MODERATE = "MODERATE", "Moderate (Score 10-14)"
        MODERATELY_SEVERE = "MODERATELY_SEVERE", "Moderately Severe (Score 15-19)"
        SEVERE = "SEVERE", "Severe (Score 20+)"

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    case = models.ForeignKey(
        CareSupportCase,
        on_delete=models.CASCADE,
        related_name="mental_health_screenings",
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="mental_health_screenings",
    )

    screening_tool = models.CharField(
        max_length=20,
        choices=ScreeningTool.choices,
        default=ScreeningTool.PHQ9,
    )
    score = models.PositiveSmallIntegerField(
        help_text="Standard clinical score (0-27 for PHQ-9, 0-21 for GAD-7)",
    )
    severity = models.CharField(
        max_length=30,
        choices=Severity.choices,
    )

    suicidal_ideation_detected = models.BooleanField(
        default=False,
        help_text="Flagged if Question 9 on PHQ-9 evaluates > 0",
    )
    depression_risk_flag = models.BooleanField(default=False)

    psychosocial_support_plan = models.TextField(
        blank=True,
        default="",
        help_text="Counselling referral, peer support group, or psycho-oncology liaison",
    )

    screened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="conducted_mental_health_screenings",
    )
    screened_at = models.DateTimeField(auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "mental_health_screening"
        ordering = ["-screened_at", "id"]
        indexes = [
            models.Index(fields=["case", "screening_tool"]),
            models.Index(fields=["patient", "severity"]),
            models.Index(fields=["suicidal_ideation_detected"]),
        ]

    def __str__(self):
        return f"{self.screening_tool} ({self.severity}) for {self.patient} - Score: {self.score}"
