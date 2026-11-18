from rest_framework import permissions, viewsets

from .models import CareSupportCase, CaseAssignment, MentalHealthScreening
from .serializers import (
    CareSupportCaseSerializer,
    CaseAssignmentSerializer,
    MentalHealthScreeningSerializer,
)


class CareSupportCaseViewSet(viewsets.ModelViewSet):
    queryset = (
        CareSupportCase.objects.all()
        .select_related("patient", "primary_clinical_need")
        .prefetch_related("assignments", "mental_health_screenings")
    )
    serializer_class = CareSupportCaseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "public_id"


class CaseAssignmentViewSet(viewsets.ModelViewSet):
    queryset = CaseAssignment.objects.all().select_related("case", "assigned_to")
    serializer_class = CaseAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "public_id"


class MentalHealthScreeningViewSet(viewsets.ModelViewSet):
    queryset = MentalHealthScreening.objects.all().select_related("case", "patient", "screened_by")
    serializer_class = MentalHealthScreeningSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "public_id"

    def perform_create(self, serializer):
        serializer.save(screened_by=self.request.user)
