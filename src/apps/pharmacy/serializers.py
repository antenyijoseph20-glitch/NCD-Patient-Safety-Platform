from rest_framework import serializers

from .models import MedicationRegimen, PharmacyDispensingLog


class MedicationRegimenSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField(source="patient.full_name")
    condition_name = serializers.ReadOnlyField(source="clinical_need.condition_name")
    progress_percentage = serializers.ReadOnlyField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    route_display = serializers.CharField(source="get_route_display", read_only=True)

    class Meta:
        model = MedicationRegimen
        fields = [
            "id",
            "public_id",
            "patient",
            "patient_name",
            "clinical_need",
            "condition_name",
            "prescribed_by",
            "medication_name",
            "generic_name",
            "dosage",
            "frequency",
            "route",
            "route_display",
            "total_cycles",
            "completed_cycles",
            "progress_percentage",
            "status",
            "status_display",
            "start_date",
            "end_date",
            "protocol_reference",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "public_id", "created_at", "updated_at"]


class PharmacyDispensingLogSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField(source="patient.full_name")
    facility_name = serializers.ReadOnlyField(source="facility.name")
    dispensed_by_name = serializers.ReadOnlyField(source="dispensed_by.user.get_full_name")

    class Meta:
        model = PharmacyDispensingLog
        fields = [
            "id",
            "public_id",
            "regimen",
            "patient",
            "patient_name",
            "facility",
            "facility_name",
            "dispensed_by",
            "dispensed_by_name",
            "authorization",
            "medication_name",
            "nafdac_reg_number",
            "batch_number",
            "expiry_date",
            "quantity_dispensed",
            "unit_of_measure",
            "cycle_number",
            "subsidy_amount_applied",
            "verification_seal_hash",
            "adverse_reaction_observed",
            "notes",
            "dispensed_at",
            "created_at",
        ]
        read_only_fields = ["id", "public_id", "verification_seal_hash", "created_at"]
