from rest_framework import serializers

from .models import (
    ClinicalEvidence,
    ClinicalNeed,
    ClinicalVerification,
)


class ClinicalEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalEvidence
        fields = [
            "public_id",
            "evidence_type",
            "title",
            "document_reference",
            "sha256_checksum",
            "issued_by",
            "issued_date",
            "created_at",
        ]
        read_only_fields = ["public_id", "created_at"]


class ClinicalVerificationSerializer(serializers.ModelSerializer):
    professional_name = serializers.CharField(source="professional.user.get_full_name", read_only=True)
    facility_name = serializers.CharField(source="facility.name", read_only=True)

    class Meta:
        model = ClinicalVerification
        fields = [
            "public_id",
            "professional",
            "professional_name",
            "facility",
            "facility_name",
            "status",
            "verification_notes",
            "verified_at",
            "created_at",
        ]
        read_only_fields = ["public_id", "created_at"]


class ClinicalNeedSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    verifications = ClinicalVerificationSerializer(many=True, read_only=True)
    evidence_records = ClinicalEvidenceSerializer(many=True, read_only=True)

    class Meta:
        model = ClinicalNeed
        fields = [
            "public_id",
            "patient",
            "patient_name",
            "condition_name",
            "icd10_code",
            "severity",
            "status",
            "clinical_summary",
            "diagnosed_date",
            "verifications",
            "evidence_records",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["public_id", "created_at", "updated_at"]
