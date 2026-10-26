import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class PaymentInstruction(models.Model):
    class PayeeType(models.TextChoices):
        HEALTHCARE_FACILITY = "HEALTHCARE_FACILITY", "Healthcare facility"
        PHARMACY = "PHARMACY", "Pharmacy provider"
        DIAGNOSTIC_CENTRE = "DIAGNOSTIC_CENTRE", "Diagnostic centre"
        PATIENT_ACCOUNT = "PATIENT_ACCOUNT", "Patient verified account"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending execution"
        APPROVED = "APPROVED", "Approved for payment"
        PROCESSING = "PROCESSING", "Processing through banking gateway"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    instruction_reference = models.CharField(
        max_length=50,
        unique=True,
    )

    authorization = models.ForeignKey(
        "funding.AssistanceAuthorization",
        on_delete=models.PROTECT,
        related_name="payment_instructions",
    )

    payee_type = models.CharField(
        max_length=50,
        choices=PayeeType.choices,
        default=PayeeType.HEALTHCARE_FACILITY,
    )

    payee_facility = models.ForeignKey(
        "organizations.Facility",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="payment_instructions",
    )

    payee_name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)

    amount = models.DecimalField(
        max_digits=19,
        decimal_places=2,
    )
    currency_code = models.CharField(max_length=3, default="NGN")

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
    )

    authorized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="authorized_payment_instructions",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payment_instruction"
        ordering = ["-created_at", "id"]
        indexes = [
            models.Index(fields=["instruction_reference"]),
            models.Index(fields=["authorization", "status"]),
            models.Index(fields=["status"]),
            models.Index(fields=["authorized_by"]),
        ]

    def __str__(self):
        return f"{self.instruction_reference}: {self.currency_code} {self.amount} to {self.payee_name} ({self.status})"

    def clean(self):
        # Four-Eyes Governance Rule:
        # The user authorizing the payment instruction cannot be the same user who approved the funding decision.
        if hasattr(self, "authorization") and self.authorization:
            if hasattr(self.authorization, "decision") and self.authorization.decision:
                if self.authorized_by_id and self.authorized_by_id == self.authorization.decision.decision_maker_id:
                    raise ValidationError(
                        "Separation of duties violation: The officer authorizing the payment instruction "
                        "cannot be the same user who approved the funding decision."
                    )
            if self.amount > self.authorization.remaining_balance:
                raise ValidationError(
                    f"Instruction amount {self.amount} exceeds remaining authorization balance of "
                    f"{self.authorization.remaining_balance}."
                )


class Payment(models.Model):
    class PaymentMethod(models.TextChoices):
        BANK_TRANSFER = "BANK_TRANSFER", "Direct bank transfer"
        NIBSS_INSTANT_PAYMENT = "NIBSS_INSTANT_PAYMENT", "NIBSS Instant Payment (NIP)"
        ELECTRONIC_PAYMENT = "ELECTRONIC_PAYMENT", "Electronic payment gateway"
        MOBILE_MONEY = "MOBILE_MONEY", "Mobile money transfer"
        OTHER = "OTHER", "Other approved method"

    class Status(models.TextChoices):
        INITIATED = "INITIATED", "Initiated"
        SUCCESSFUL = "SUCCESSFUL", "Successful"
        FAILED = "FAILED", "Failed"
        REVERSED = "REVERSED", "Reversed"

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    payment_reference = models.CharField(
        max_length=64,
        unique=True,
    )

    instruction = models.ForeignKey(
        PaymentInstruction,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    amount = models.DecimalField(
        max_digits=19,
        decimal_places=2,
    )
    currency_code = models.CharField(max_length=3, default="NGN")

    payment_method = models.CharField(
        max_length=50,
        choices=PaymentMethod.choices,
        default=PaymentMethod.NIBSS_INSTANT_PAYMENT,
    )

    channel_reference = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Bank session ID / gateway reference",
    )

    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="executed_payments",
    )

    executed_at = models.DateTimeField()

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.INITIATED,
    )

    transaction_response = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payment"
        ordering = ["-executed_at", "id"]
        indexes = [
            models.Index(fields=["payment_reference"]),
            models.Index(fields=["instruction", "status"]),
            models.Index(fields=["status"]),
            models.Index(fields=["executed_at"]),
        ]

    def __str__(self):
        return f"{self.payment_reference}: {self.currency_code} {self.amount} ({self.status})"

    def clean(self):
        # Four-Eyes Governance Rule:
        # The user executing the payment transaction cannot be the same user who authorized the instruction.
        if hasattr(self, "instruction") and self.instruction:
            if self.executed_by_id and self.executed_by_id == self.instruction.authorized_by_id:
                raise ValidationError(
                    "Separation of duties violation: The officer executing the payment "
                    "cannot be the same user who authorized the payment instruction."
                )


class PaymentAdjustment(models.Model):
    class AdjustmentType(models.TextChoices):
        CLAWBACK = "CLAWBACK", "Clawback of unspent funds"
        REFUND = "REFUND", "Refund from healthcare facility"
        OVERPAYMENT_REVERSAL = "OVERPAYMENT_REVERSAL", "Reversal of overpayment"
        FEE_CORRECTION = "FEE_CORRECTION", "Fee or billing correction"

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    adjustment_reference = models.CharField(
        max_length=64,
        unique=True,
    )

    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name="adjustments",
    )

    adjustment_type = models.CharField(
        max_length=50,
        choices=AdjustmentType.choices,
    )

    amount = models.DecimalField(
        max_digits=19,
        decimal_places=2,
    )
    currency_code = models.CharField(max_length=3, default="NGN")

    reason = models.TextField()

    authorized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payment_adjustments",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payment_adjustment"
        ordering = ["-created_at", "id"]
        indexes = [
            models.Index(fields=["adjustment_reference"]),
            models.Index(fields=["payment", "adjustment_type"]),
        ]

    def __str__(self):
        return f"{self.adjustment_reference}: {self.adjustment_type} - {self.currency_code} {self.amount}"


class ServiceEvidence(models.Model):
    class EvidenceType(models.TextChoices):
        INVOICE = "INVOICE", "Itemized hospital / pharmacy invoice"
        DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY", "Clinical discharge summary"
        DRUG_DISPENSING_LOG = "DRUG_DISPENSING_LOG", "Pharmacy dispensing verification log"
        LAB_RESULT = "LAB_RESULT", "Diagnostic / Pathology test result"
        RECEIPT = "RECEIPT", "Official receipt of payment"

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    case = models.ForeignKey(
        "cases.CareSupportCase",
        on_delete=models.PROTECT,
        related_name="service_evidences",
    )

    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="service_evidences",
    )

    facility = models.ForeignKey(
        "organizations.Facility",
        on_delete=models.PROTECT,
        related_name="service_evidences",
    )

    evidence_type = models.CharField(
        max_length=50,
        choices=EvidenceType.choices,
    )

    reference_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    amount_claimed = models.DecimalField(
        max_digits=19,
        decimal_places=2,
    )
    currency_code = models.CharField(max_length=3, default="NGN")

    document_url = models.CharField(
        max_length=500,
        blank=True,
        default="",
    )
    sha256_checksum = models.CharField(
        max_length=64,
        blank=True,
        default="",
    )

    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_service_evidences",
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "service_evidence"
        ordering = ["-created_at", "id"]
        indexes = [
            models.Index(fields=["case", "evidence_type"]),
            models.Index(fields=["facility", "verified"]),
            models.Index(fields=["sha256_checksum"]),
        ]

    def __str__(self):
        return f"{self.evidence_type} ({self.reference_number}) - {self.currency_code} {self.amount_claimed}"


class Reconciliation(models.Model):
    class Status(models.TextChoices):
        BALANCED = "BALANCED", "Balanced"
        DISCREPANCY_FLAGGED = "DISCREPANCY_FLAGGED", "Discrepancy flagged"
        RESOLVED = "RESOLVED", "Discrepancy resolved"

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    reconciliation_period_start = models.DateField()
    reconciliation_period_end = models.DateField()

    total_instruction_amount = models.DecimalField(
        max_digits=19,
        decimal_places=2,
    )
    total_executed_amount = models.DecimalField(
        max_digits=19,
        decimal_places=2,
    )
    total_adjusted_amount = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    discrepancy_amount = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    currency_code = models.CharField(max_length=3, default="NGN")

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.BALANCED,
    )

    reconciled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reconciliations",
    )

    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reconciliation"
        ordering = ["-reconciliation_period_end", "id"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["reconciliation_period_start", "reconciliation_period_end"]),
        ]

    def __str__(self):
        return f"Reconciliation {self.reconciliation_period_start} to {self.reconciliation_period_end} ({self.status})"
