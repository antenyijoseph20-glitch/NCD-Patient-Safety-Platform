from rest_framework import permissions, viewsets

from .models import (
    AssistanceAuthorization,
    FundingApplication,
    FundingProgramme,
    FundingSource,
)
from .serializers import (
    AssistanceAuthorizationSerializer,
    FundingApplicationSerializer,
    FundingProgrammeSerializer,
    FundingSourceSerializer,
)


class FundingSourceViewSet(viewsets.ModelViewSet):
    queryset = FundingSource.objects.all().prefetch_related("programmes")
    serializer_class = FundingSourceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "public_id"


class FundingProgrammeViewSet(viewsets.ModelViewSet):
    queryset = FundingProgramme.objects.all().prefetch_related("rules")
    serializer_class = FundingProgrammeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "public_id"


class FundingApplicationViewSet(viewsets.ModelViewSet):
    queryset = (
        FundingApplication.objects.all()
        .select_related("case", "programme", "applied_by", "decision")
        .prefetch_related("reviews")
    )
    serializer_class = FundingApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "public_id"

    def perform_create(self, serializer):
        application = serializer.save(applied_by=self.request.user)
        application.full_clean()


class AssistanceAuthorizationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AssistanceAuthorization.objects.all().select_related("decision", "case", "facility")
    serializer_class = AssistanceAuthorizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "public_id"
