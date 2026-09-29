import uuid

from django.conf import settings
from django.db import models

class Organization(models.Model):
    class OrganizationType(models.TextChoices):
        GOVERNMENT = "GOVERNMENT", "Government"
        NGO = "NGO", "Non-governmental organization"
        DONOR = "DONOR", "Donor"
        FOUNDATION = "FOUNDATION", "Foundation"
        HEALTHCARE_PROVIDER = (
            "HEALTHCARE_PROVIDER",
            "Healthcare provider",
        )
        INSURER = "INSURER", "Insurer"
        PAYMENT_PROVIDER = "PAYMENT_PROVIDER", "Payment provider"
        DEVELOPMENT_PARTNER = (
            "DEVELOPMENT_PARTNER",
            "Development partner",
        )
        PROFESSIONAL_BODY = (
            "PROFESSIONAL_BODY",
            "Professional body",
        )
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        PENDING_VERIFICATION = (
            "PENDING_VERIFICATION",
            "Pending verification",
        )
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"
        INACTIVE = "INACTIVE", "Inactive"

    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    name = models.CharField(max_length=255)

    organization_type = models.CharField(
        max_length=50,
        choices=OrganizationType.choices,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING_VERIFICATION,
    )

    registration_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    email = models.EmailField(
        max_length=254,
        null=True,
        blank=True,
    )

    phone = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )

    website = models.URLField(
        max_length=500,
        null=True,
        blank=True,
    )

    address = models.TextField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "organization"
        ordering = ["name", "id"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["organization_type"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class Facility(models.Model):
    class FacilityType(models.TextChoices):
        HOSPITAL = "HOSPITAL", "Hospital"
        PRIMARY_HEALTH_CENTRE = (
            "PRIMARY_HEALTH_CENTRE",
            "Primary health centre",
        )
        CLINIC = "CLINIC", "Clinic"
        SPECIALIST_CENTRE = (
            "SPECIALIST_CENTRE",
            "Specialist centre",
        )
        DIAGNOSTIC_CENTRE = (
            "DIAGNOSTIC_CENTRE",
            "Diagnostic centre",
        )
        PHARMACY = "PHARMACY", "Pharmacy"
        OTHER = "OTHER", "Other"


    class Status(models.TextChoices):
        PENDING_VERIFICATION = (
            "PENDING_VERIFICATION",
            "Pending verification",
        )
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"
        INACTIVE = "INACTIVE", "Inactive"

    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="facilities",
    )

    name = models.CharField(max_length=255)

    facility_type = models.CharField(
        max_length=50,
        choices=FacilityType.choices,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING_VERIFICATION,
    )

    email = models.EmailField(
        max_length=254,
        null=True,
        blank=True,
    )

    phone = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )

    address = models.TextField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "facility"
        ordering = ["name", "id"]
        indexes = [
            models.Index(fields=["organization"]),
            models.Index(fields=["status"]),
            models.Index(fields=["facility_type"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class HealthcareProfessional(models.Model):
    class Profession(models.TextChoices):
        DOCTOR = "DOCTOR", "Doctor"
        NURSE = "NURSE", "Nurse"
        MIDWIFE = "MIDWIFE", "Midwife"
        PHARMACIST = "PHARMACIST", "Pharmacist"
        LABORATORY_SCIENTIST = (
            "LABORATORY_SCIENTIST",
            "Laboratory scientist",
        )
        RADIOGRAPHER = "RADIOGRAPHER", "Radiographer"
        PHYSIOTHERAPIST = "PHYSIOTHERAPIST", "Physiotherapist"
        DENTIST = "DENTIST", "Dentist"
        HEALTH_INFORMATION_MANAGER = (
            "HEALTH_INFORMATION_MANAGER",
            "Health information manager",
        )
        COMMUNITY_HEALTH_PRACTITIONER = (
            "COMMUNITY_HEALTH_PRACTITIONER",
            "Community health practitioner",
        )
        OTHER = "OTHER", "Other"

    class LicenseStatus(models.TextChoices):
        PENDING_VERIFICATION = (
            "PENDING_VERIFICATION",
            "Pending verification",
        )
        VERIFIED = "VERIFIED", "Verified"
        EXPIRED = "EXPIRED", "Expired"
        SUSPENDED = "SUSPENDED", "Suspended"
        REVOKED = "REVOKED", "Revoked"

    class Status(models.TextChoices):
        PENDING_VERIFICATION = (
            "PENDING_VERIFICATION",
            "Pending verification",
        )
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"
        INACTIVE = "INACTIVE", "Inactive"

    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="healthcare_professional",
    )

    profession = models.CharField(
        max_length=50,
        choices=Profession.choices,
    )

    license_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    license_status = models.CharField(
        max_length=30,
        choices=LicenseStatus.choices,
        default=LicenseStatus.PENDING_VERIFICATION,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING_VERIFICATION,
    )

    phone = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "healthcare_professional"
        ordering = ["user__last_name", "user__first_name", "id"]
        indexes = [
            models.Index(fields=["profession"]),
            models.Index(fields=["license_status"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.profession}"