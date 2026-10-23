import uuid

from django.conf import settings
from django.db import models


class Patient(models.Model):
    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"
        PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", "Prefer not to say"

    class BloodGroup(models.TextChoices):
        A_POSITIVE = "A+", "A Positive"
        A_NEGATIVE = "A-", "A Negative"
        B_POSITIVE = "B+", "B Positive"
        B_NEGATIVE = "B-", "B Negative"
        AB_POSITIVE = "AB+", "AB Positive"
        AB_NEGATIVE = "AB-", "AB Negative"
        O_POSITIVE = "O+", "O Positive"
        O_NEGATIVE = "O-", "O Negative"
        UNKNOWN = "UNKNOWN", "Unknown"

    class Genotype(models.TextChoices):
        AA = "AA", "AA"
        AS = "AS", "AS"
        SS = "SS", "SS"
        AC = "AC", "AC"
        SC = "SC", "SC"
        UNKNOWN = "UNKNOWN", "Unknown"

    class Status(models.TextChoices):
        PENDING_VERIFICATION = (
            "PENDING_VERIFICATION",
            "Pending verification",
        )
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"
        DECEASED = "DECEASED", "Deceased"
        INACTIVE = "INACTIVE", "Inactive"

    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patient_profiles",
    )

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    other_names = models.CharField(max_length=150, blank=True, default="")
    date_of_birth = models.DateField()

    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
    )

    blood_group = models.CharField(
        max_length=10,
        choices=BloodGroup.choices,
        default=BloodGroup.UNKNOWN,
    )

    genotype = models.CharField(
        max_length=10,
        choices=Genotype.choices,
        default=Genotype.UNKNOWN,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING_VERIFICATION,
    )

    primary_phone = models.CharField(max_length=50, blank=True, default="")
    email = models.EmailField(max_length=254, blank=True, default="")
    address = models.TextField(blank=True, default="")

    emergency_contact_name = models.CharField(max_length=255, blank=True, default="")
    emergency_contact_phone = models.CharField(max_length=50, blank=True, default="")
    emergency_contact_relationship = models.CharField(max_length=100, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "patient"
        ordering = ["last_name", "first_name", "id"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["gender"]),
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["date_of_birth"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        if self.other_names:
            return f"{self.first_name} {self.other_names} {self.last_name}"
        return f"{self.first_name} {self.last_name}"


class PatientContact(models.Model):
    class ContactType(models.TextChoices):
        PHONE = "PHONE", "Phone number"
        EMAIL = "EMAIL", "Email address"
        PHYSICAL_ADDRESS = "PHYSICAL_ADDRESS", "Physical address"
        NEXT_OF_KIN = "NEXT_OF_KIN", "Next of kin"
        EMERGENCY = "EMERGENCY", "Emergency contact"

    id = models.BigAutoField(primary_key=True)

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="contacts",
    )

    contact_type = models.CharField(
        max_length=30,
        choices=ContactType.choices,
    )

    value = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default="")
    is_primary = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "patient_contact"
        ordering = ["patient", "-is_primary", "id"]
        indexes = [
            models.Index(fields=["patient", "contact_type"]),
            models.Index(fields=["patient", "is_primary"]),
        ]

    def __str__(self):
        return f"{self.patient} - {self.contact_type}: {self.value}"
