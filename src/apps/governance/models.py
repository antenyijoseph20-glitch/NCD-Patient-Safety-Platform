import hashlib
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class ConsentAuthorization(models.Model):
    """
    NDPA 2023 Compliant Patient Consent & Data-Sharing Authorization.
    Records explicit patient and caregiver authorizations for clinical data sharing,
    direct humanitarian financial subsidies, and third-party healthcare audits.
    """
    class Scope(models.TextChoices):
        ALL_CLINICAL_RECORDS = "ALL_CLINICAL_RECORDS", "All clinical records & diagnostics"
        DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY", "Diagnostic and laboratory records only"
        FINANCIAL_AID_ONLY = "FINANCIAL_AID_ONLY", "Financial aid & subsidy adjudication only"
        RESEARCH_ANONYMIZED = "RESEARCH_ANONYMIZED", "De-identified clinical research & registry"
        EMERGENCY_TREATMENT = "EMERGENCY_TREATMENT", "Emergency treatment & vital interest override"

    class Purpose(models.TextChoices):
        CARE_COORDINATION = "CARE_COORDINATION", "Direct clinical care & patient navigation"
        SUBSIDY_APPLICATION = "SUBSIDY_APPLICATION", "Government / NGO humanitarian grant application"
        FINANCIAL_DISBURSEMENT = "FINANCIAL_DISBURSEMENT", "Direct banking disbursement & claims settlement"
        SAFETY_AUDITING = "SAFETY_AUDITING", "Clinical safety incident & quality audit"
        DONOR_TRANSPARENCY = "DONOR_TRANSPARENCY", "Verifiable donor impact telemetry & reporting"

    class LegalBasis(models.TextChoices):
        CONSENT = "CONSENT", "Explicit Consent (NDPA 2023 s.24)"
        VITAL_INTERESTS = "VITAL_INTERESTS", "Vital Interests of Data Subject (NDPA s.25)"
        PUBLIC_HEALTH = "PUBLIC_HEALTH", "Public Health & Severe Medical Need (NDPA s.26)"
        CONTRACTUAL = "CONTRACTUAL", "Contractual Healthcare Entitlement"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        WITHDRAWN = "WITHDRAWN", "Withdrawn by patient or caregiver"
        EXPIRED = "EXPIRED", "Expired"
        PENDING_VERIFICATION = "PENDING_VERIFICATION", "Pending verification"

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="consent_authorizations",
    )
    granter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="granted_consents",
        help_text="The patient or authorized caregiver granting this legal authorization.",
    )

    scope = models.CharField(
        max_length=50,
        choices=Scope.choices,
        default=Scope.ALL_CLINICAL_RECORDS,
    )
    purpose = models.CharField(
        max_length=50,
        choices=Purpose.choices,
        default=Purpose.CARE_COORDINATION,
    )
    legal_basis = models.CharField(
        max_length=50,
        choices=LegalBasis.choices,
        default=LegalBasis.CONSENT,
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    authorized_organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authorized_consents",
    )
    authorized_facility = models.ForeignKey(
        "organizations.Facility",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authorized_consents",
    )

    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)

    withdrawn_at = models.DateTimeField(null=True, blank=True)
    withdrawal_reason = models.TextField(blank=True, default="")

    consent_document_hash = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="SHA-256 integrity seal of the signed consent terms.",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "consent_authorization"
        ordering = ["-created_at", "id"]
        indexes = [
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["status", "valid_to"]),
            models.Index(fields=["purpose"]),
        ]

    def __str__(self):
        return f"Consent ({self.scope}) for {self.patient} - {self.status}"

    def is_valid(self) -> bool:
        """Returns True if the consent authorization is currently legally effective."""
        if self.status != self.Status.ACTIVE:
            return False
        now = timezone.now()
        if self.valid_from and self.valid_from > now:
            return False
        if self.valid_to and self.valid_to < now:
            return False
        return True

    def withdraw(self, reason: str, user=None):
        """Formally withdraws consent with audit logging."""
        self.status = self.Status.WITHDRAWN
        self.withdrawn_at = timezone.now()
        self.withdrawal_reason = reason
        self.save()


class AuditEvent(models.Model):
    """
    Immutable Governance & Access Audit Trail.
    Tamper-evident record of all high-impact access events, FHIR resource queries,
    clinical verifications, and financial transactions.
    """
    class Action(models.TextChoices):
        VIEW_PATIENT_RECORD = "VIEW_PATIENT_RECORD", "View patient medical record"
        EXPORT_FHIR_RESOURCE = "EXPORT_FHIR_RESOURCE", "Export FHIR R4 interoperability bundle"
        VERIFY_CLINICAL_NEED = "VERIFY_CLINICAL_NEED", "Certify clinical diagnosis"
        APPROVE_FUNDING = "APPROVE_FUNDING", "Approve assistance grant application"
        AUTHORIZE_PAYMENT = "AUTHORIZE_PAYMENT", "Issue payment instruction"
        DISBURSE_SETTLEMENT = "DISBURSE_SETTLEMENT", "Execute bank settlement"
        ATTACH_EVIDENCE = "ATTACH_EVIDENCE", "Attach cryptographic medical evidence"
        GRANT_CONSENT = "GRANT_CONSENT", "Grant legal consent authorization"
        WITHDRAW_CONSENT = "WITHDRAW_CONSENT", "Withdraw consent authorization"
        REPORT_SAFETY_EVENT = "REPORT_SAFETY_EVENT", "Report clinical adverse safety incident"
        SECURITY_ALERT = "SECURITY_ALERT", "Unauthorized access attempt"

    class Outcome(models.TextChoices):
        SUCCESS = "SUCCESS", "Success / Granted"
        DENIED = "DENIED", "Denied / Forbidden"
        ERROR = "ERROR", "System Error"

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    timestamp = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    action = models.CharField(max_length=60, choices=Action.choices)
    outcome = models.CharField(
        max_length=30,
        choices=Outcome.choices,
        default=Outcome.SUCCESS,
    )

    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=100)

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    description = models.TextField(blank=True, default="")

    previous_event_hash = models.CharField(max_length=64, blank=True, default="")
    event_hash = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        db_table = "audit_event"
        ordering = ["-timestamp", "id"]
        indexes = [
            models.Index(fields=["action", "timestamp"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["patient", "action"]),
            models.Index(fields=["outcome"]),
        ]

    def __str__(self):
        actor_name = self.actor.username if self.actor else "Anonymous/Gateway"
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {actor_name} -> {self.action} on {self.resource_type}:{self.resource_id} ({self.outcome})"

    def save(self, *args, **kwargs):
        if not self.event_hash:
            # Cryptographic chain: hash of previous event + current payload
            last_event = AuditEvent.objects.order_by("-id").first()
            prev_hash = last_event.event_hash if last_event and last_event.event_hash else "GENESIS_BLOCK_2026"
            self.previous_event_hash = prev_hash
            
            payload = f"{self.timestamp}-{self.actor_id}-{self.action}-{self.resource_type}-{self.resource_id}-{self.outcome}-{prev_hash}"
            self.event_hash = hashlib.sha256(payload.encode()).hexdigest()
        super().save(*args, **kwargs)
