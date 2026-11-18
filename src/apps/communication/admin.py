from django.contrib import admin

from .models import Notification, USSDSession


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "recipient_phone",
        "patient",
        "channel",
        "language",
        "status",
        "gateway_provider",
        "cost_ngn",
        "created_at",
    )
    list_filter = ("channel", "language", "status", "gateway_provider", "created_at")
    search_fields = (
        "recipient_phone",
        "recipient_email",
        "gateway_reference",
        "message_body",
        "patient__first_name",
        "patient__last_name",
    )
    readonly_fields = (
        "public_id",
        "sent_at",
        "delivered_at",
        "created_at",
        "updated_at",
        "gateway_reference",
    )


@admin.register(USSDSession)
class USSDSessionAdmin(admin.ModelAdmin):
    list_display = (
        "session_id",
        "phone_number",
        "service_code",
        "patient",
        "language",
        "current_step",
        "is_active",
        "last_interaction_at",
    )
    list_filter = ("language", "is_active", "service_code")
    search_fields = ("session_id", "phone_number", "patient__first_name", "patient__last_name")
    readonly_fields = ("created_at", "last_interaction_at")
