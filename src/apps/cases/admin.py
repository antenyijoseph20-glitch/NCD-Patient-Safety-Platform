from django.contrib import admin

from .models import CareSupportCase, CaseAssignment, MentalHealthScreening


class MentalHealthScreeningInline(admin.TabularInline):
    model = MentalHealthScreening
    extra = 0
    readonly_fields = ("public_id", "screened_at", "created_at")


class CaseAssignmentInline(admin.TabularInline):
    model = CaseAssignment
    extra = 1
    readonly_fields = ("public_id", "assigned_at", "created_at", "updated_at")


@admin.register(CareSupportCase)
class CareSupportCaseAdmin(admin.ModelAdmin):
    list_display = (
        "case_number",
        "title",
        "patient",
        "priority",
        "status",
        "opened_at",
        "closed_at",
    )
    list_filter = ("status", "priority")
    search_fields = (
        "case_number",
        "title",
        "description",
        "patient__first_name",
        "patient__last_name",
    )
    readonly_fields = ("public_id", "opened_at", "created_at", "updated_at")
    inlines = [CaseAssignmentInline, MentalHealthScreeningInline]


@admin.register(MentalHealthScreening)
class MentalHealthScreeningAdmin(admin.ModelAdmin):
    list_display = (
        "case",
        "patient",
        "screening_tool",
        "score",
        "severity",
        "suicidal_ideation_detected",
        "depression_risk_flag",
        "screened_at",
    )
    list_filter = ("screening_tool", "severity", "suicidal_ideation_detected", "depression_risk_flag")
    search_fields = ("case__case_number", "patient__first_name", "patient__last_name", "psychosocial_support_plan", "screened_by__username")
    readonly_fields = ("public_id", "created_at", "updated_at")


@admin.register(CaseAssignment)
class CaseAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "case",
        "assigned_to",
        "role",
        "is_active",
        "assigned_at",
    )
    list_filter = ("role", "is_active")
    search_fields = (
        "case__case_number",
        "assigned_to__username",
        "assigned_to__email",
    )
    readonly_fields = ("public_id", "assigned_at", "created_at", "updated_at")
