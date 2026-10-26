from django.contrib import admin

from .models import (
    AssistanceAuthorization,
    FundingApplication,
    FundingDecision,
    FundingProgramme,
    FundingReview,
    FundingSource,
    ProgrammeRule,
)


class ProgrammeRuleInline(admin.TabularInline):
    model = ProgrammeRule
    extra = 1
    readonly_fields = ("public_id", "created_at", "updated_at")


class FundingReviewInline(admin.TabularInline):
    model = FundingReview
    extra = 0
    readonly_fields = ("public_id", "reviewed_at")


class FundingDecisionInline(admin.StackedInline):
    model = FundingDecision
    extra = 0
    readonly_fields = ("public_id", "decided_at")


@admin.register(FundingSource)
class FundingSourceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "source_type",
        "status",
        "currency_code",
        "total_allocation",
        "allocated_amount",
        "disbursed_amount",
        "created_at",
    )
    list_filter = ("source_type", "status")
    search_fields = ("name", "contact_name", "contact_email")
    readonly_fields = ("public_id", "created_at", "updated_at")


@admin.register(FundingProgramme)
class FundingProgrammeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "source",
        "budget_limit",
        "allocated_amount",
        "disbursed_amount",
        "currency_code",
        "status",
        "start_date",
        "end_date",
    )
    list_filter = ("status", "source")
    search_fields = ("name", "description", "source__name")
    readonly_fields = ("public_id", "created_at", "updated_at")
    inlines = [ProgrammeRuleInline]


@admin.register(FundingApplication)
class FundingApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "application_number",
        "case",
        "programme",
        "applicant_type",
        "applied_by",
        "requested_amount",
        "approved_amount",
        "currency_code",
        "status",
        "submitted_at",
    )
    list_filter = ("status", "applicant_type", "programme")
    search_fields = (
        "application_number",
        "case__case_number",
        "case__patient__first_name",
        "case__patient__last_name",
        "applied_by__username",
    )
    readonly_fields = ("public_id", "created_at", "updated_at")
    inlines = [FundingReviewInline, FundingDecisionInline]


@admin.register(FundingReview)
class FundingReviewAdmin(admin.ModelAdmin):
    list_display = (
        "application",
        "reviewer",
        "recommendation",
        "recommended_amount",
        "reviewed_at",
    )
    list_filter = ("recommendation",)
    search_fields = (
        "application__application_number",
        "reviewer__username",
        "review_notes",
    )
    readonly_fields = ("public_id", "reviewed_at")


@admin.register(FundingDecision)
class FundingDecisionAdmin(admin.ModelAdmin):
    list_display = (
        "application",
        "decision_maker",
        "decision",
        "approved_amount",
        "currency_code",
        "decided_at",
    )
    list_filter = ("decision",)
    search_fields = (
        "application__application_number",
        "decision_maker__username",
        "decision_notes",
    )
    readonly_fields = ("public_id", "decided_at")


@admin.register(AssistanceAuthorization)
class AssistanceAuthorizationAdmin(admin.ModelAdmin):
    list_display = (
        "authorization_code",
        "case",
        "facility",
        "authorized_amount",
        "disbursed_amount",
        "currency_code",
        "valid_from",
        "valid_to",
        "status",
    )
    list_filter = ("status", "facility")
    search_fields = (
        "authorization_code",
        "case__case_number",
        "case__patient__first_name",
        "case__patient__last_name",
    )
    readonly_fields = ("public_id", "created_at", "updated_at")
