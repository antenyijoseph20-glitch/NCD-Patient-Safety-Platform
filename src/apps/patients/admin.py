from django.contrib import admin

from .models import (
    CaregiverRelationship,
    ExternalIdentifier,
    Patient,
    PatientContact,
)


class PatientContactInline(admin.TabularInline):
    model = PatientContact
    extra = 1
    readonly_fields = ("public_id", "created_at", "updated_at")


class CaregiverRelationshipInline(admin.TabularInline):
    model = CaregiverRelationship
    extra = 0
    readonly_fields = ("public_id", "created_at", "updated_at")


class ExternalIdentifierInline(admin.TabularInline):
    model = ExternalIdentifier
    extra = 1
    readonly_fields = ("public_id", "created_at", "updated_at")


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "date_of_birth",
        "gender",
        "blood_group",
        "genotype",
        "status",
        "primary_phone",
        "created_at",
    )
    list_filter = ("status", "gender", "blood_group", "genotype")
    search_fields = (
        "first_name",
        "last_name",
        "other_names",
        "primary_phone",
        "email",
        "public_id",
    )
    readonly_fields = ("public_id", "created_at", "updated_at")
    inlines = [
        PatientContactInline,
        CaregiverRelationshipInline,
        ExternalIdentifierInline,
    ]


@admin.register(PatientContact)
class PatientContactAdmin(admin.ModelAdmin):
    list_display = ("patient", "contact_type", "value", "is_primary", "created_at")
    list_filter = ("contact_type", "is_primary")
    search_fields = ("patient__first_name", "patient__last_name", "value")
    readonly_fields = ("public_id", "created_at", "updated_at")


@admin.register(CaregiverRelationship)
class CaregiverRelationshipAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "patient",
        "relationship_type",
        "status",
        "can_view_records",
        "can_manage_care",
        "can_apply_funding",
        "created_at",
    )
    list_filter = ("relationship_type", "status", "can_manage_care", "can_apply_funding")
    search_fields = (
        "user__username",
        "user__email",
        "patient__first_name",
        "patient__last_name",
    )
    readonly_fields = ("public_id", "created_at", "updated_at")


@admin.register(ExternalIdentifier)
class ExternalIdentifierAdmin(admin.ModelAdmin):
    list_display = (
        "system",
        "value",
        "patient",
        "identifier_type",
        "verification_status",
        "created_at",
    )
    list_filter = ("system", "identifier_type", "verification_status")
    search_fields = ("system", "value", "patient__first_name", "patient__last_name")
    readonly_fields = ("public_id", "created_at", "updated_at")
