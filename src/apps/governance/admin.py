from django.contrib import admin

from .models import AuditEvent, ConsentAuthorization


@admin.register(ConsentAuthorization)
class ConsentAuthorizationAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "scope",
        "purpose",
        "legal_basis",
        "status",
        "valid_from",
        "valid_to",
        "created_at",
    )
    list_filter = ("status", "scope", "purpose", "legal_basis")
    search_fields = (
        "patient__first_name",
        "patient__last_name",
        "granter__username",
        "withdrawal_reason",
    )
    readonly_fields = ("public_id", "consent_document_hash", "created_at", "updated_at")


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "actor",
        "action",
        "resource_type",
        "resource_id",
        "outcome",
        "ip_address",
    )
    list_filter = ("action", "outcome", "resource_type", "timestamp")
    search_fields = ("actor__username", "resource_id", "description", "ip_address")
    readonly_fields = (
        "public_id",
        "timestamp",
        "actor",
        "action",
        "outcome",
        "resource_type",
        "resource_id",
        "patient",
        "ip_address",
        "user_agent",
        "description",
        "previous_event_hash",
        "event_hash",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
