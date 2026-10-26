from rest_framework import permissions, viewsets

from .models import (
    Payment,
    PaymentInstruction,
    Reconciliation,
    ServiceEvidence,
)
from .serializers import (
    PaymentInstructionSerializer,
    PaymentSerializer,
    ReconciliationSerializer,
    ServiceEvidenceSerializer,
)


class PaymentInstructionViewSet(viewsets.ModelViewSet):
    queryset = PaymentInstruction.objects.all().select_related("authorization", "payee_facility", "authorized_by")
    serializer_class = PaymentInstructionSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "public_id"

    def perform_create(self, serializer):
        instruction = serializer.save(authorized_by=self.request.user)
        instruction.full_clean()


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().select_related("instruction", "executed_by")
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "public_id"

    def perform_create(self, serializer):
        payment = serializer.save(executed_by=self.request.user)
        payment.full_clean()


class ServiceEvidenceViewSet(viewsets.ModelViewSet):
    queryset = ServiceEvidence.objects.all().select_related("case", "payment", "facility", "verified_by")
    serializer_class = ServiceEvidenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "public_id"


class ReconciliationViewSet(viewsets.ModelViewSet):
    queryset = Reconciliation.objects.all().select_related("reconciled_by")
    serializer_class = ReconciliationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "public_id"
