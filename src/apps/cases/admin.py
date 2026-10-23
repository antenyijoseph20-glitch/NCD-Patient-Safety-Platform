from django.contrib import admin

from .models import CareSupportCase, CaseAssignment


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
    inlines = [CaseAssignmentInline]


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
