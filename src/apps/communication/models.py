from decimal import Decimal
import uuid

from django.db import models
from django.utils import timezone


class Notification(models.Model):
    """
    Multichannel patient notification and alerts (SMS, USSD Push, Email, WhatsApp).
    Supports low-bandwidth, offline patient communication across multiple national languages.
    """
    class Channel(models.TextChoices):
        SMS = "SMS", "SMS Text Message"
        USSD_PUSH = "USSD_PUSH", "Interactive USSD Push"
        EMAIL = "EMAIL", "Electronic Mail"
        WHATSAPP = "WHATSAPP", "WhatsApp Healthcare Notification"

    class Language(models.TextChoices):
        EN = "EN", "English"
        HA = "HA", "Hausa (Harshen Hausa)"
        YO = "YO", "Yorùbá (Èdè Yorùbá)"
        IG = "IG", "Igbo (Asụsụ Igbo)"

    class Status(models.TextChoices):
        QUEUED = "QUEUED", "Queued for Dispatch"
        DISPATCHED = "DISPATCHED", "Dispatched to Telco Gateway"
        DELIVERED = "DELIVERED", "Delivered to Handset"
        FAILED = "FAILED", "Delivery Failed"

    id = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    case = models.ForeignKey(
        "cases.CareSupportCase",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )

    recipient_phone = models.CharField(max_length=32, db_index=True)
    recipient_email = models.EmailField(blank=True, default="")
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.SMS)
    language = models.CharField(max_length=10, choices=Language.choices, default=Language.EN)

    message_title = models.CharField(max_length=255, blank=True, default="")
    message_body = models.TextField()

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED, db_index=True)
    gateway_provider = models.CharField(max_length=64, default="SIMULATED")
    gateway_reference = models.CharField(max_length=128, blank=True, default="", db_index=True)
    cost_ngn = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal("0.0000"))
    delivery_attempts = models.PositiveSmallIntegerField(default=0)
    error_message = models.TextField(blank=True, default="")

    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"[{self.channel}] to {self.recipient_phone} ({self.status})"

    def mark_dispatched(self, gateway_reference: str, provider: str = "SIMULATED", cost: Decimal = Decimal("4.0000")):
        self.status = self.Status.DISPATCHED
        self.gateway_reference = gateway_reference
        self.gateway_provider = provider
        self.cost_ngn = cost
        self.delivery_attempts += 1
        self.sent_at = timezone.now()
        self.save(update_fields=["status", "gateway_reference", "gateway_provider", "cost_ngn", "delivery_attempts", "sent_at", "updated_at"])

    def mark_delivered(self):
        self.status = self.Status.DELIVERED
        self.delivered_at = timezone.now()
        self.save(update_fields=["status", "delivered_at", "updated_at"])

    def mark_failed(self, error: str):
        self.status = self.Status.FAILED
        self.error_message = error
        self.delivery_attempts += 1
        self.save(update_fields=["status", "error_message", "delivery_attempts", "updated_at"])


class USSDSession(models.Model):
    """
    Session state tracking for live telecommunication USSD gateway requests (*384*2026#).
    Enables low-bandwidth offline patient inquiries, subsidy tracking, and emergency alerts.
    """
    id = models.BigAutoField(primary_key=True)
    session_id = models.CharField(max_length=128, unique=True, db_index=True)
    phone_number = models.CharField(max_length=32, db_index=True)
    service_code = models.CharField(max_length=32, default="*384*2026#")

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ussd_sessions",
    )

    current_step = models.CharField(max_length=64, default="MAIN_MENU")
    language = models.CharField(max_length=10, default="EN")
    session_data = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_interaction_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_interaction_at"]
        verbose_name = "USSD Session"
        verbose_name_plural = "USSD Sessions"

    def __str__(self):
        return f"USSD {self.session_id} ({self.phone_number}) - Step: {self.current_step}"
