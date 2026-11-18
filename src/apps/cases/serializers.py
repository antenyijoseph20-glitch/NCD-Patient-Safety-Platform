from rest_framework import serializers

from .models import CareSupportCase, CaseAssignment


class CaseAssignmentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="assigned_to.get_full_name", read_only=True)

    class Meta:
        model = CaseAssignment
        fields = [
            "public_id",
            "assigned_to",
            "user_name",
            "role",
            "is_active",
            "assigned_at",
            "notes",
        ]
        read_only_fields = ["public_id", "assigned_at"]


class CareSupportCaseSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    condition_name = serializers.CharField(source="primary_clinical_need.condition_name", read_only=True)
    assignments = CaseAssignmentSerializer(many=True, read_only=True)

    class Meta:
        model = CareSupportCase
        fields = [
            "public_id",
            "case_number",
            "patient",
            "patient_name",
            "primary_clinical_need",
            "condition_name",
            "title",
            "description",
            "priority",
            "status",
            "opened_at",
            "closed_at",
            "assignments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["public_id", "case_number", "opened_at", "created_at", "updated_at"]
