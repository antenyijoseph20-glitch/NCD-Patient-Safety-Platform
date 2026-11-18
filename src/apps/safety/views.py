import uuid

from django.utils import timezone
from rest_framework import permissions, viewsets

from .models import SafetyEvent
from .serializers import SafetyEventSerializer


class SafetyEventViewSet(viewsets.ModelViewSet):
    queryset = SafetyEvent.objects.all().select_related("patient", "case", "reported_by", "facility")
    serializer_class = SafetyEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "public_id"

    def perform_create(self, serializer):
        ref = f"SAF-2026-{uuid.uuid4().hex[:6].upper()}"
        serializer.save(
            reported_by=self.request.user,
            reference_code=ref,
            occurred_at=serializer.validated_data.get("occurred_at", timezone.now()),
        )
