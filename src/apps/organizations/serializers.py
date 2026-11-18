from rest_framework import serializers

from .models import Facility, HealthcareProfessional, Organization


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "public_id",
            "name",
            "organization_type",
            "status",
            "registration_number",
            "email",
            "phone",
            "website",
            "address",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["public_id", "created_at", "updated_at"]


class FacilitySerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = Facility
        fields = [
            "public_id",
            "organization",
            "organization_name",
            "name",
            "facility_type",
            "status",
            "email",
            "phone",
            "address",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["public_id", "created_at", "updated_at"]


class HealthcareProfessionalSerializer(serializers.ModelSerializer):
    user_full_name = serializers.CharField(source="user.get_full_name", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = HealthcareProfessional
        fields = [
            "public_id",
            "user",
            "user_full_name",
            "user_email",
            "profession",
            "license_number",
            "license_status",
            "status",
            "phone",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["public_id", "created_at", "updated_at"]
