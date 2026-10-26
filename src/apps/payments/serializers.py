from rest_framework import serializers

from .models import (
    Payment,
    PaymentAdjustment,
    PaymentInstruction,
    Reconciliation,
    ServiceEvidence,
)


class PaymentAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentAdjustment
        fields = [
            "id",
            "public_id",
            "adjustment_reference",
            "payment",
            "adjustment_type",
            "amount",
            "currency_code",
            "reason",
            "authorized_by",
            "created_at",
        ]
        read_only_fields = ["id", "public_id", "created_at"]


class PaymentSerializer(serializers.ModelSerializer):
    adjustments = PaymentAdjustmentSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "public_id",
            "payment_reference",
            "instruction",
            "amount",
            "currency_code",
            "payment_method",
            "channel_reference",
            "executed_by",
            "executed_at",
            "status",
            "transaction_response",
            "adjustments",
            "created_at",
        ]
        read_only_fields = ["id", "public_id", "created_at", "adjustments"]


class PaymentInstructionSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = PaymentInstruction
        fields = [
            "id",
            "public_id",
            "instruction_reference",
            "authorization",
            "payee_type",
            "payee_facility",
            "payee_name",
            "bank_name",
            "account_number",
            "amount",
            "currency_code",
            "status",
            "authorized_by",
            "payments",
            "created_at",
        ]
        read_only_fields = ["id", "public_id", "created_at", "payments"]


class ServiceEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceEvidence
        fields = [
            "id",
            "public_id",
            "case",
            "payment",
            "facility",
            "evidence_type",
            "reference_number",
            "amount_claimed",
            "currency_code",
            "document_url",
            "sha256_checksum",
            "verified",
            "verified_by",
            "verified_at",
            "created_at",
        ]
        read_only_fields = ["id", "public_id", "created_at"]


class ReconciliationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reconciliation
        fields = [
            "id",
            "public_id",
            "reconciliation_period_start",
            "reconciliation_period_end",
            "total_instruction_amount",
            "total_executed_amount",
            "total_adjusted_amount",
            "discrepancy_amount",
            "currency_code",
            "status",
            "reconciled_by",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "public_id", "created_at"]
