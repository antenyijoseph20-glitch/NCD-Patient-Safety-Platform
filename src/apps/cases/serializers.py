from rest_framework import serializers

from .models import CareSupportCase, CaseAssignment, MentalHealthScreening


class MentalHealthScreeningSerializer(serializers.ModelSerializer):
    screened_by_name = serializers.CharField(source="screened_by.get_full_name", read_only=True)
    screening_tool_display = serializers.CharField(source="get_screening_tool_display", read_only=True)
    severity_display = serializers.CharField(source="get_severity_display", read_only=True)

    class Meta:
        model = MentalHealthScreening
        fields = [
            "public_id",
            "screening_tool",
            "screening_tool_display",
            "score",
            "severity",
            "severity_display",
            "suicidal_ideation_detected",
            "depression_risk_flag",
            "psychosocial_support_plan",
            "screened_by",
            "screened_by_name",
            "screened_at",
        ]
        read_only_fields = ["public_id", "screened_at"]


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
    mental_health_screenings = MentalHealthScreeningSerializer(many=True, read_only=True)

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
            "mental_health_screenings",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["public_id", "case_number", "opened_at", "created_at", "updated_at"]
