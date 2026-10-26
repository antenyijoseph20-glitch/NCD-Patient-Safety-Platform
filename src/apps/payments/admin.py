from django.contrib import admin

from .models import (
    Payment,
    PaymentAdjustment,
    PaymentInstruction,
    Reconciliation,
    ServiceEvidence,
)


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("public_id", "executed_at", "created_at", "updated_at")


class PaymentAdjustmentInline(admin.TabularInline):
    model = PaymentAdjustment
    extra = 0
    readonly_fields = ("public_id", "created_at", "updated_at")


@admin.register(PaymentInstruction)
class PaymentInstructionAdmin(admin.ModelAdmin):
    list_display = (
        "instruction_reference",
        "authorization",
        "payee_type",
        "payee_name",
        "bank_name",
        "amount",
        "currency_code",
        "status",
        "authorized_by",
        "created_at",
    )
    list_filter = ("status", "payee_type")
    search_fields = (
        "instruction_reference",
        "payee_name",
        "account_number",
        "bank_name",
        "authorization__authorization_code",
    )
    readonly_fields = ("public_id", "created_at", "updated_at")
    inlines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "payment_reference",
        "instruction",
        "amount",
        "currency_code",
        "payment_method",
        "status",
        "executed_by",
        "executed_at",
    )
    list_filter = ("status", "payment_method")
    search_fields = (
        "payment_reference",
        "channel_reference",
        "instruction__instruction_reference",
        "executed_by__username",
    )
    readonly_fields = ("public_id", "created_at", "updated_at")
    inlines = [PaymentAdjustmentInline]


@admin.register(PaymentAdjustment)
class PaymentAdjustmentAdmin(admin.ModelAdmin):
    list_display = (
        "adjustment_reference",
        "payment",
        "adjustment_type",
        "amount",
        "currency_code",
        "authorized_by",
        "created_at",
    )
    list_filter = ("adjustment_type",)
    search_fields = (
        "adjustment_reference",
        "payment__payment_reference",
        "reason",
        "authorized_by__username",
    )
    readonly_fields = ("public_id", "created_at", "updated_at")


@admin.register(ServiceEvidence)
class ServiceEvidenceAdmin(admin.ModelAdmin):
    list_display = (
        "reference_number",
        "case",
        "facility",
        "evidence_type",
        "amount_claimed",
        "currency_code",
        "verified",
        "verified_by",
        "verified_at",
    )
    list_filter = ("evidence_type", "verified", "facility")
    search_fields = (
        "reference_number",
        "case__case_number",
        "facility__name",
        "sha256_checksum",
    )
    readonly_fields = ("public_id", "created_at", "updated_at")


@admin.register(Reconciliation)
class ReconciliationAdmin(admin.ModelAdmin):
    list_display = (
        "reconciliation_period_start",
        "reconciliation_period_end",
        "total_instruction_amount",
        "total_executed_amount",
        "total_adjusted_amount",
        "discrepancy_amount",
        "currency_code",
        "status",
        "reconciled_by",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = (
        "notes",
        "reconciled_by__username",
    )
    readonly_fields = ("public_id", "created_at", "updated_at")
