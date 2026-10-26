import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class FundingSource(models.Model):
    class SourceType(models.TextChoices):
        GOVERNMENT = "GOVERNMENT", "Government body"
        NGO = "NGO", "Non-governmental organization"
        DONOR = "DONOR", "Bilateral / Multilateral donor"
        FOUNDATION = "FOUNDATION", "Philanthropic foundation"
        DEVELOPMENT_PARTNER = "DEVELOPMENT_PARTNER", "Development partner"
        CORPORATE = "CORPORATE", "Corporate CSR"
        INDIVIDUAL = "INDIVIDUAL", "Individual benefactor"
        OTHER = "OTHER", "Other source"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        SUSPENDED = "SUSPENDED", "Suspended"

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    name = models.CharField(max_length=255, unique=True)
    source_type = models.CharField(
        max_length=50,
        choices=SourceType.choices,
        default=SourceType.DONOR,
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    contact_name = models.CharField(max_length=255, blank=True, default="")
    contact_email = models.EmailField(blank=True, default="")
    contact_phone = models.CharField(max_length=50, blank=True, default="")

    currency_code = models.CharField(max_length=3, default="NGN")
    total_allocation = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    allocated_amount = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    disbursed_amount = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "funding_source"
        ordering = ["name", "id"]
        indexes = [
            models.Index(fields=["source_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.source_type})"


class FundingProgramme(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        PAUSED = "PAUSED", "Paused"
        CLOSED = "CLOSED", "Closed"

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    source = models.ForeignKey(
        FundingSource,
        on_delete=models.PROTECT,
        related_name="programmes",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")

    budget_limit = models.DecimalField(
        max_digits=19,
        decimal_places=2,
    )
    allocated_amount = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    disbursed_amount = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    currency_code = models.CharField(max_length=3, default="NGN")

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "funding_programme"
        ordering = ["-created_at", "id"]
        indexes = [
            models.Index(fields=["source", "status"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.source.name}"


class ProgrammeRule(models.Model):
    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    programme = models.ForeignKey(
        FundingProgramme,
        on_delete=models.CASCADE,
        related_name="rules",
    )
    rule_name = models.CharField(max_length=255)
    max_amount_per_case = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        null=True,
        blank=True,
    )
    target_icd10_prefix = models.CharField(
        max_length=30,
        blank=True,
        default="",
        help_text="e.g. C50 for breast cancer or E10 for type 1 diabetes",
    )
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "programme_rule"
        ordering = ["programme", "rule_name", "id"]
        indexes = [
            models.Index(fields=["programme", "is_active"]),
        ]

    def __str__(self):
        return f"{self.programme.name}: {self.rule_name}"


class FundingApplication(models.Model):
    class ApplicantType(models.TextChoices):
        PATIENT = "PATIENT", "Patient self-application"
        CAREGIVER = "CAREGIVER", "Authorized caregiver"
        CASE_OFFICER = "CASE_OFFICER", "Assigned case officer"
        HEALTHCARE_PROVIDER = "HEALTHCARE_PROVIDER", "Healthcare provider"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        UNDER_REVIEW = "UNDER_REVIEW", "Under review"
        APPROVED = "APPROVED", "Approved"
        PARTIALLY_APPROVED = "PARTIALLY_APPROVED", "Partially approved"
        DECLINED = "DECLINED", "Declined"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    application_number = models.CharField(
        max_length=50,
        unique=True,
    )

    # Core interface contract with Team A:
    case = models.ForeignKey(
        "cases.CareSupportCase",
        on_delete=models.PROTECT,
        related_name="funding_applications",
    )

    programme = models.ForeignKey(
        FundingProgramme,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="applications",
    )

    applicant_type = models.CharField(
        max_length=50,
        choices=ApplicantType.choices,
        default=ApplicantType.CASE_OFFICER,
    )

    applied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_funding_applications",
    )

    requested_amount = models.DecimalField(
        max_digits=19,
        decimal_places=2,
    )
    approved_amount = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        null=True,
        blank=True,
    )
    currency_code = models.CharField(max_length=3, default="NGN")

    clinical_justification = models.TextField()

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )

    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "funding_application"
        ordering = ["-created_at", "id"]
        indexes = [
            models.Index(fields=["application_number"]),
            models.Index(fields=["case", "status"]),
            models.Index(fields=["status"]),
            models.Index(fields=["applied_by"]),
        ]

    def __str__(self):
        return f"{self.application_number} ({self.status}) - {self.currency_code} {self.requested_amount}"

    def clean(self):
        # Pre-Funding Eligibility Rule:
        # Before a FundingApplication can be submitted, case.status must be CareSupportCase.Status.FUNDING_ELIGIBLE,
        # and case.primary_clinical_need.verifications.filter(status='VERIFIED').exists() must evaluate to True.
        if self.status in [self.Status.SUBMITTED, self.Status.UNDER_REVIEW, self.Status.APPROVED]:
            if hasattr(self, "case") and self.case:
                if self.case.status != "FUNDING_ELIGIBLE":
                    raise ValidationError(
                        f"Cannot submit application for case {self.case.case_number}: "
                        f"case status must be FUNDING_ELIGIBLE, currently {self.case.status}."
                    )
                if (
                    not self.case.primary_clinical_need
                    or not self.case.primary_clinical_need.verifications.filter(status="VERIFIED").exists()
                ):
                    raise ValidationError(
                        f"Cannot submit application for case {self.case.case_number}: "
                        "primary clinical need must have at least one verified clinical verification."
                    )


class FundingReview(models.Model):
    class Recommendation(models.TextChoices):
        RECOMMEND_APPROVAL = "RECOMMEND_APPROVAL", "Recommend approval"
        RECOMMEND_PARTIAL = "RECOMMEND_PARTIAL", "Recommend partial approval"
        RECOMMEND_REJECTION = "RECOMMEND_REJECTION", "Recommend rejection"
        REQUEST_MORE_INFO = "REQUEST_MORE_INFO", "Request more information"

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    application = models.ForeignKey(
        FundingApplication,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="funding_reviews",
    )
    recommendation = models.CharField(
        max_length=50,
        choices=Recommendation.choices,
    )
    recommended_amount = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        null=True,
        blank=True,
    )
    review_notes = models.TextField()
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "funding_review"
        ordering = ["-reviewed_at", "id"]
        indexes = [
            models.Index(fields=["application", "recommendation"]),
            models.Index(fields=["reviewer"]),
        ]

    def __str__(self):
        return f"Review on {self.application.application_number} by {self.reviewer} ({self.recommendation})"


class FundingDecision(models.Model):
    class Decision(models.TextChoices):
        APPROVED = "APPROVED", "Approved"
        PARTIALLY_APPROVED = "PARTIALLY_APPROVED", "Partially approved"
        DECLINED = "DECLINED", "Declined"

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    application = models.OneToOneField(
        FundingApplication,
        on_delete=models.PROTECT,
        related_name="decision",
    )
    decision_maker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="funding_decisions",
    )
    decision = models.CharField(
        max_length=30,
        choices=Decision.choices,
    )
    approved_amount = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    currency_code = models.CharField(max_length=3, default="NGN")
    conditions = models.TextField(blank=True, default="")
    decision_notes = models.TextField()
    decided_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "funding_decision"
        ordering = ["-decided_at", "id"]
        indexes = [
            models.Index(fields=["decision"]),
            models.Index(fields=["decision_maker"]),
        ]

    def clean(self):
        # Separation of Duties (Four-Eyes Principle):
        # The decision maker must not be the person who applied for the funding.
        if hasattr(self, "application") and self.application:
            if self.decision_maker_id and self.decision_maker_id == self.application.applied_by_id:
                raise ValidationError(
                    "Separation of duties violation: The decision maker cannot be the same user who submitted the funding application."
                )

    def __str__(self):
        return f"Decision: {self.decision} ({self.currency_code} {self.approved_amount}) for {self.application.application_number}"


class AssistanceAuthorization(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        EXHAUSTED = "EXHAUSTED", "Exhausted"
        EXPIRED = "EXPIRED", "Expired"
        REVOKED = "REVOKED", "Revoked"

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    authorization_code = models.CharField(
        max_length=50,
        unique=True,
    )
    decision = models.OneToOneField(
        FundingDecision,
        on_delete=models.PROTECT,
        related_name="authorization",
    )
    case = models.ForeignKey(
        "cases.CareSupportCase",
        on_delete=models.PROTECT,
        related_name="assistance_authorizations",
    )
    facility = models.ForeignKey(
        "organizations.Facility",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="authorizations",
    )
    authorized_amount = models.DecimalField(
        max_digits=19,
        decimal_places=2,
    )
    disbursed_amount = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    currency_code = models.CharField(max_length=3, default="NGN")

    valid_from = models.DateField()
    valid_to = models.DateField()

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "assistance_authorization"
        ordering = ["-created_at", "id"]
        indexes = [
            models.Index(fields=["authorization_code"]),
            models.Index(fields=["case", "status"]),
            models.Index(fields=["status"]),
        ]

    @property
    def remaining_balance(self):
        return self.authorized_amount - self.disbursed_amount

    def __str__(self):
        return f"{self.authorization_code} ({self.status}) - Cap: {self.currency_code} {self.authorized_amount}"
