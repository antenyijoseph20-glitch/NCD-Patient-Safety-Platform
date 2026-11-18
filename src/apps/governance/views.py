from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AuditEvent, ConsentAuthorization
from .serializers import AuditEventSerializer, ConsentAuthorizationSerializer
from .services import AuditLogger


class ConsentAuthorizationViewSet(viewsets.ModelViewSet):
    """
    NDPA Consent & Data Sharing Authorization Management.
    """
    queryset = (
        ConsentAuthorization.objects.all()
        .select_related("patient", "granter", "authorized_organization", "authorized_facility")
    )
    serializer_class = ConsentAuthorizationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "public_id"

    def perform_create(self, serializer):
        consent = serializer.save(granter=self.request.user)
        AuditLogger.log(
            action=AuditEvent.Action.GRANT_CONSENT,
            resource_type="ConsentAuthorization",
            resource_id=str(consent.public_id),
            request=self.request,
            actor=self.request.user,
            patient=consent.patient,
            description="Patient data-sharing consent authorized.",
        )

    @action(detail=True, methods=["post"])
    def withdraw(self, request, public_id=None):
        consent = self.get_object()
        reason = request.data.get("reason", "Withdrawn by data subject request.")
        consent.withdraw(reason=reason, user=request.user)
        
        AuditLogger.log(
            action=AuditEvent.Action.WITHDRAW_CONSENT,
            resource_type="ConsentAuthorization",
            resource_id=str(consent.public_id),
            request=request,
            actor=request.user,
            patient=consent.patient,
            description=f"Consent authorization revoked. Reason: {reason}",
        )
        return Response(
            {"status": "Consent successfully revoked.", "public_id": str(consent.public_id)},
            status=status.HTTP_200_OK,
        )


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Immutable Regulatory Audit Trail ViewSet for NDPA & Clinical Quality Reviewers.
    """
    queryset = AuditEvent.objects.all().select_related("actor", "patient")
    serializer_class = AuditEventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "public_id"
