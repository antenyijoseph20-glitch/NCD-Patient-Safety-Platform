from django.contrib import admin

from .models import SafetyEvent


@admin.register(SafetyEvent)
class SafetyEventAdmin(admin.ModelAdmin):
    list_display = (
        "reference_code",
        "patient",
        "severity",
        "status",
        "reported_by",
        "occurred_at",
        "reported_at",
    )
    list_filter = ("status", "severity")
    search_fields = (
        "reference_code",
        "patient__first_name",
        "patient__last_name",
        "event_description",
        "immediate_action_taken",
    )
    readonly_fields = ("public_id", "reported_at", "created_at", "updated_at")
