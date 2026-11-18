from rest_framework import permissions, viewsets

from .models import Facility, HealthcareProfessional, Organization
from .serializers import (
    FacilitySerializer,
    HealthcareProfessionalSerializer,
    OrganizationSerializer,
)


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all().prefetch_related("facilities")
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "public_id"


class FacilityViewSet(viewsets.ModelViewSet):
    queryset = Facility.objects.all().select_related("organization")
    serializer_class = FacilitySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "public_id"


class HealthcareProfessionalViewSet(viewsets.ModelViewSet):
    queryset = HealthcareProfessional.objects.all().select_related("user")
    serializer_class = HealthcareProfessionalSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "public_id"
