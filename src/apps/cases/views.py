from rest_framework import permissions, viewsets

from .models import CareSupportCase, CaseAssignment
from .serializers import (
    CareSupportCaseSerializer,
    CaseAssignmentSerializer,
)


class CareSupportCaseViewSet(viewsets.ModelViewSet):
    queryset = (
        CareSupportCase.objects.all()
        .select_related("patient", "primary_clinical_need")
        .prefetch_related("assignments")
    )
    serializer_class = CareSupportCaseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "public_id"


class CaseAssignmentViewSet(viewsets.ModelViewSet):
    queryset = CaseAssignment.objects.all().select_related("case", "assigned_to")
    serializer_class = CaseAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "public_id"
