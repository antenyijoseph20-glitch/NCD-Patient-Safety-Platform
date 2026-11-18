from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.safety.models import SafetyEvent

from .models import MedicationRegimen, PharmacyDispensingLog
from .serializers import MedicationRegimenSerializer, PharmacyDispensingLogSerializer


class MedicationRegimenViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing clinical patient medication regimens.
    """
    queryset = MedicationRegimen.objects.select_related("patient", "clinical_need", "prescribed_by__user").all()
    serializer_class = MedicationRegimenSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["patient", "clinical_need", "status"]
    search_fields = ["medication_name", "generic_name", "protocol_reference"]

    @action(detail=True, methods=["post"], url_path="advance-cycle")
    def advance_cycle(self, request, pk=None):
        regimen = self.get_object()
        if regimen.completed_cycles < regimen.total_cycles:
            regimen.completed_cycles += 1
            if regimen.completed_cycles >= regimen.total_cycles:
                regimen.status = MedicationRegimen.Status.COMPLETED
                regimen.end_date = timezone.now().date()
            regimen.save(update_fields=["completed_cycles", "status", "end_date", "updated_at"])
            return Response(
                {
                    "message": f"Regimen advanced to cycle {regimen.completed_cycles} of {regimen.total_cycles}.",
                    "completed_cycles": regimen.completed_cycles,
                    "status": regimen.status,
                    "progress_percentage": regimen.progress_percentage,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": "All planned cycles have already been completed."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PharmacyDispensingLogViewSet(viewsets.ModelViewSet):
    """
    API endpoint for logging and verifying anti-counterfeit pharmacy dispensations.
    """
    queryset = PharmacyDispensingLog.objects.select_related(
        "patient", "facility", "dispensed_by__user", "regimen", "authorization"
    ).all()
    serializer_class = PharmacyDispensingLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["patient", "facility", "batch_number"]
    search_fields = ["medication_name", "batch_number", "nafdac_reg_number", "verification_seal_hash"]

    def perform_create(self, serializer):
        dispensing = serializer.save()
        # If an adverse reaction was observed during dispensing, automatically log a safety event
        if dispensing.adverse_reaction_observed:
            SafetyEvent.objects.create(
                patient=dispensing.patient,
                facility=dispensing.facility,
                reported_by=self.request.user,
                severity=SafetyEvent.Severity.MODERATE_HARM,
                status=SafetyEvent.Status.REPORTED,
                event_description=(
                    f"Adverse reaction observed during pharmacy dispensing of {dispensing.medication_name} "
                    f"(Batch: {dispensing.batch_number}, NAFDAC: {dispensing.nafdac_reg_number}). Notes: {dispensing.notes}"
                ),
                immediate_action_taken="Dispensing flagged; clinical evaluation and adverse event protocol initiated.",
                occurred_at=timezone.now(),
            )

    @action(detail=False, methods=["get"], url_path="verify-seal")
    def verify_seal(self, request):
        seal_hash = request.query_params.get("seal", "").strip()
        if not seal_hash:
            return Response({"error": "Query parameter 'seal' is required."}, status=status.HTTP_400_BAD_REQUEST)

        dispensing = PharmacyDispensingLog.objects.filter(verification_seal_hash=seal_hash).first()
        if not dispensing:
            return Response(
                {"verified": False, "message": "Cryptographic seal not found in National NCD Platform registry."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "verified": True,
                "verification_seal_hash": dispensing.verification_seal_hash,
                "medication_name": dispensing.medication_name,
                "nafdac_reg_number": dispensing.nafdac_reg_number,
                "batch_number": dispensing.batch_number,
                "expiry_date": dispensing.expiry_date,
                "facility_name": dispensing.facility.name,
                "patient_name": dispensing.patient.full_name,
                "dispensed_at": dispensing.dispensed_at,
            },
            status=status.HTTP_200_OK,
        )
