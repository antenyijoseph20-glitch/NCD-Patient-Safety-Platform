from rest_framework import serializers

from .models import AuditEvent, ConsentAuthorization


class ConsentAuthorizationSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.get_full_name", read_only=True)
    granter_name = serializers.CharField(source="granter.get_full_name", read_only=True)
    scope_display = serializers.CharField(source="get_scope_display", read_only=True)
    purpose_display = serializers.CharField(source="get_purpose_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    is_legally_valid = serializers.BooleanField(source="is_valid", read_only=True)

    class Meta:
        model = ConsentAuthorization
        fields = [
            "public_id",
            "patient",
            "patient_name",
            "granter",
            "granter_name",
            "scope",
            "scope_display",
            "purpose",
            "purpose_display",
            "legal_basis",
            "status",
            "status_display",
            "authorized_organization",
            "authorized_facility",
            "valid_from",
            "valid_to",
            "is_legally_valid",
            "withdrawn_at",
            "withdrawal_reason",
            "consent_document_hash",
            "created_at",
        ]
        read_only_fields = ["public_id", "consent_document_hash", "created_at"]


class AuditEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.get_full_name", read_only=True)
    action_display = serializers.CharField(source="get_action_display", read_only=True)
    outcome_display = serializers.CharField(source="get_outcome_display", read_only=True)

    class Meta:
        model = AuditEvent
        fields = [
            "public_id",
            "timestamp",
            "actor",
            "actor_name",
            "action",
            "action_display",
            "outcome",
            "outcome_display",
            "resource_type",
            "resource_id",
            "patient",
            "ip_address",
            "description",
            "previous_event_hash",
            "event_hash",
        ]
        read_only_fields = fields
