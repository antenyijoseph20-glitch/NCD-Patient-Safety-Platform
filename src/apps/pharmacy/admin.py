from django.contrib import admin

from .models import MedicationRegimen, PharmacyDispensingLog


@admin.register(MedicationRegimen)
class MedicationRegimenAdmin(admin.ModelAdmin):
    list_display = (
        "medication_name",
        "patient",
        "dosage",
        "route",
        "completed_cycles",
        "total_cycles",
        "status",
        "start_date",
    )
    list_filter = ("status", "route", "start_date")
    search_fields = ("medication_name", "generic_name", "patient__first_name", "patient__last_name", "protocol_reference")
    readonly_fields = ("public_id", "created_at", "updated_at")


@admin.register(PharmacyDispensingLog)
class PharmacyDispensingLogAdmin(admin.ModelAdmin):
    list_display = (
        "medication_name",
        "batch_number",
        "nafdac_reg_number",
        "patient",
        "facility",
        "cycle_number",
        "subsidy_amount_applied",
        "dispensed_at",
    )
    list_filter = ("facility", "adverse_reaction_observed", "dispensed_at")
    search_fields = (
        "medication_name",
        "batch_number",
        "nafdac_reg_number",
        "verification_seal_hash",
        "patient__first_name",
        "patient__last_name",
    )
    readonly_fields = ("public_id", "verification_seal_hash", "created_at")
