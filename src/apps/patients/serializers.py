from rest_framework import serializers

from .models import (
    CaregiverRelationship,
    ExternalIdentifier,
    Patient,
    PatientContact,
)


class PatientContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientContact
        fields = [
            "public_id",
            "contact_type",
            "value",
            "description",
            "is_primary",
            "created_at",
        ]
        read_only_fields = ["public_id", "created_at"]


class ExternalIdentifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalIdentifier
        fields = [
            "public_id",
            "system",
            "value",
            "identifier_type",
            "issuing_authority",
            "verification_status",
            "valid_from",
            "valid_to",
            "created_at",
        ]
        read_only_fields = ["public_id", "created_at"]


class CaregiverRelationshipSerializer(serializers.ModelSerializer):
    caregiver_name = serializers.CharField(source="user.get_full_name", read_only=True)
    caregiver_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = CaregiverRelationship
        fields = [
            "public_id",
            "user",
            "caregiver_name",
            "caregiver_email",
            "relationship_type",
            "status",
            "can_view_records",
            "can_manage_care",
            "can_apply_funding",
            "created_at",
        ]
        read_only_fields = ["public_id", "created_at"]


class PatientSerializer(serializers.ModelSerializer):
    contacts = PatientContactSerializer(many=True, read_only=True)
    identifiers = ExternalIdentifierSerializer(source="external_identifiers", many=True, read_only=True)
    caregivers = CaregiverRelationshipSerializer(source="caregiver_relationships", many=True, read_only=True)

    class Meta:
        model = Patient
        fields = [
            "public_id",
            "first_name",
            "last_name",
            "other_names",
            "date_of_birth",
            "gender",
            "blood_group",
            "genotype",
            "status",
            "primary_phone",
            "email",
            "address",
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relationship",
            "contacts",
            "identifiers",
            "caregivers",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["public_id", "created_at", "updated_at"]
