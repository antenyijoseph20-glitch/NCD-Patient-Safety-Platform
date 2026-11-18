from rest_framework import serializers

from .models import SafetyEvent


class SafetyEventSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    facility_name = serializers.CharField(source="facility.name", read_only=True)
    reporter_name = serializers.CharField(source="reported_by.get_full_name", read_only=True)

    class Meta:
        model = SafetyEvent
        fields = [
            "public_id",
            "reference_code",
            "patient",
            "patient_name",
            "case",
            "reported_by",
            "reporter_name",
            "facility",
            "facility_name",
            "severity",
            "status",
            "event_description",
            "immediate_action_taken",
            "occurred_at",
            "reported_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["public_id", "reference_code", "reported_at", "created_at", "updated_at"]
