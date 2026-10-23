from django.contrib import admin

from .models import ClinicalEvidence, ClinicalNeed, ClinicalVerification


class ClinicalVerificationInline(admin.TabularInline):
    model = ClinicalVerification
    extra = 0
    readonly_fields = ("public_id", "created_at", "updated_at")


class ClinicalEvidenceInline(admin.TabularInline):
    model = ClinicalEvidence
    extra = 1
    readonly_fields = ("public_id", "created_at", "updated_at")


@admin.register(ClinicalNeed)
class ClinicalNeedAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "condition_name",
        "icd10_code",
        "severity",
        "status",
        "diagnosed_date",
        "created_at",
    )
    list_filter = ("status", "severity")
    search_fields = (
        "condition_name",
        "icd10_code",
        "patient__first_name",
        "patient__last_name",
        "clinical_summary",
    )
    readonly_fields = ("public_id", "created_at", "updated_at")
    inlines = [ClinicalVerificationInline, ClinicalEvidenceInline]


@admin.register(ClinicalVerification)
class ClinicalVerificationAdmin(admin.ModelAdmin):
    list_display = (
        "clinical_need",
        "professional",
        "facility",
        "status",
        "verified_at",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = (
        "clinical_need__condition_name",
        "professional__user__last_name",
        "verification_notes",
    )
    readonly_fields = ("public_id", "created_at", "updated_at")


@admin.register(ClinicalEvidence)
class ClinicalEvidenceAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "clinical_need",
        "evidence_type",
        "issued_by",
        "issued_date",
        "created_at",
    )
    list_filter = ("evidence_type",)
    search_fields = ("title", "issued_by", "clinical_need__condition_name")
    readonly_fields = ("public_id", "created_at", "updated_at")
