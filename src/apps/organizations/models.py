import uuid

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
