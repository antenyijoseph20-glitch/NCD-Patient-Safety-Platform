from rest_framework import permissions, viewsets

from .models import (
    CaregiverRelationship,
    ExternalIdentifier,
    Patient,
    PatientContact,
)
from .serializers import (
    CaregiverRelationshipSerializer,
    ExternalIdentifierSerializer,
    PatientContactSerializer,
    PatientSerializer,
)


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all().prefetch_related("contacts", "external_identifiers", "caregiver_relationships")
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "public_id"


class PatientContactViewSet(viewsets.ModelViewSet):
    queryset = PatientContact.objects.all().select_related("patient")
    serializer_class = PatientContactSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "public_id"


class CaregiverRelationshipViewSet(viewsets.ModelViewSet):
    queryset = CaregiverRelationship.objects.all().select_related("patient", "user")
    serializer_class = CaregiverRelationshipSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "public_id"


class ExternalIdentifierViewSet(viewsets.ModelViewSet):
    queryset = ExternalIdentifier.objects.all().select_related("patient")
    serializer_class = ExternalIdentifierSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "public_id"
