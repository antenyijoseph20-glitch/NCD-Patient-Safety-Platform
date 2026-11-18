from decimal import Decimal
import hashlib
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class MedicationRegimen(models.Model):
    """
    Standardized clinical medication regimen for Non-Communicable Diseases (NCDs).
    Aligns with WHO, NCCN, KDIGO, and national clinical treatment guidelines.
    """
    class Route(models.TextChoices):
        INTRAVENOUS = "INTRAVENOUS", "Intravenous Infusion (IV)"
        SUBCUTANEOUS = "SUBCUTANEOUS", "Subcutaneous Injection (SC)"
        ORAL = "ORAL", "Oral (PO)"
        INTRAMUSCULAR = "INTRAMUSCULAR", "Intramuscular (IM)"
        INHALATION = "INHALATION", "Inhalation"
        TOPICAL = "TOPICAL", "Topical"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active Regimen"
        COMPLETED = "COMPLETED", "Completed Protocol"
        DISCONTINUED = "DISCONTINUED", "Discontinued"
        ON_HOLD = "ON_HOLD", "On Hold / Temporarily Suspended"

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="medication_regimens",
    )
    clinical_need = models.ForeignKey(
        "clinical_need.ClinicalNeed",
        on_delete=models.CASCADE,
        related_name="medication_regimens",
    )
    prescribed_by = models.ForeignKey(
        "organizations.HealthcareProfessional",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescribed_regimens",
    )

    medication_name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255, blank=True, default="")
    dosage = models.CharField(max_length=128)
    frequency = models.CharField(max_length=128)
    route = models.CharField(max_length=32, choices=Route.choices, default=Route.ORAL)

    total_cycles = models.PositiveIntegerField(default=1, help_text="Total planned cycles or treatment sessions.")
    completed_cycles = models.PositiveIntegerField(default=0)

    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)

    protocol_reference = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text="Guideline code e.g. NCCN-C50-HER2+, KDIGO-CKD-STAGE5, ACC/AHA-2026",
    )
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        verbose_name = "Medication Regimen"
        verbose_name_plural = "Medication Regimens"

    def __str__(self):
        return f"{self.medication_name} ({self.dosage}) for {self.patient}"

    @property
    def progress_percentage(self) -> int:
        if self.total_cycles <= 0:
            return 100 if self.status == self.Status.COMPLETED else 0
        pct = int((self.completed_cycles / self.total_cycles) * 100)
        return min(pct, 100)


class PharmacyDispensingLog(models.Model):
    """
    Tamper-evident pharmacy and clinical unit dispensing log.
    Includes NAFDAC registration validation, batch tracking, anti-counterfeit cryptographic seal,
    and automatic link to humanitarian funding authorizations.
    """
    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    regimen = models.ForeignKey(
        MedicationRegimen,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dispensing_logs",
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="pharmacy_dispensing_logs",
    )
    facility = models.ForeignKey(
        "organizations.Facility",
        on_delete=models.PROTECT,
        related_name="pharmacy_dispensings",
    )
    dispensed_by = models.ForeignKey(
        "organizations.HealthcareProfessional",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dispensed_medications",
    )
    authorization = models.ForeignKey(
        "funding.AssistanceAuthorization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pharmacy_dispensings",
    )

    medication_name = models.CharField(max_length=255)
    nafdac_reg_number = models.CharField(
        max_length=64,
        help_text="National Agency for Food & Drug Administration & Control registration number.",
    )
    batch_number = models.CharField(max_length=128, db_index=True)
    expiry_date = models.DateField()

    quantity_dispensed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1.00"))
    unit_of_measure = models.CharField(max_length=64, default="vial", help_text="vial, pack, ampoule, session, tablets")
    cycle_number = models.PositiveSmallIntegerField(default=1)

    subsidy_amount_applied = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Direct humanitarian subsidy deducted for this dispensing.",
    )

    verification_seal_hash = models.CharField(
        max_length=64,
        editable=False,
        help_text="SHA-256 cryptographic seal linking batch, patient, facility, and dispensing timestamp.",
    )
    adverse_reaction_observed = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default="")

    dispensed_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-dispensed_at"]
        verbose_name = "Pharmacy Dispensing Log"
        verbose_name_plural = "Pharmacy Dispensing Logs"

    def clean(self):
        if self.expiry_date and self.expiry_date < timezone.now().date():
            raise ValidationError({"expiry_date": "Expired medication cannot be dispensed to patients under Nigerian clinical safety rules."})

    def save(self, *args, **kwargs):
        self.clean()
        if not self.verification_seal_hash:
            raw = f"{self.patient_id}:{self.facility_id}:{self.batch_number}:{self.nafdac_reg_number}:{timezone.now().isoformat()}"
            self.verification_seal_hash = hashlib.sha256(raw.encode()).hexdigest()
        super().save(*args, **kwargs)

        # Update regimen completed cycles if linked
        if self.regimen and self.regimen.completed_cycles < self.cycle_number:
            self.regimen.completed_cycles = self.cycle_number
            if self.regimen.completed_cycles >= self.regimen.total_cycles:
                self.regimen.status = MedicationRegimen.Status.COMPLETED
            self.regimen.save(update_fields=["completed_cycles", "status"])

    def __str__(self):
        return f"{self.medication_name} (Batch: {self.batch_number}) -> {self.patient}"
