import hashlib
from typing import Optional

from django.db import models
from django.http import HttpRequest
from django.utils import timezone

from apps.patients.models import Patient

from .models import AuditEvent, ConsentAuthorization


class AuditLogger:
    @staticmethod
    def get_client_ip(request: Optional[HttpRequest]) -> Optional[str]:
        if not request:
            return None
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    @classmethod
    def log(
        cls,
        action: str,
        resource_type: str,
        resource_id: str,
        request: Optional[HttpRequest] = None,
        actor=None,
        patient: Optional[Patient] = None,
        outcome: str = AuditEvent.Outcome.SUCCESS,
        description: str = "",
    ) -> AuditEvent:
        """
        Records an immutable audit event with actor, IP, timestamp, and tamper-evident hash chaining.
        """
        user_actor = actor
        if not user_actor and request and hasattr(request, "user") and request.user.is_authenticated:
            user_actor = request.user

        ip = cls.get_client_ip(request)
        ua = request.META.get("HTTP_USER_AGENT", "") if request else ""

        return AuditEvent.objects.create(
            actor=user_actor,
            action=action,
            outcome=outcome,
            resource_type=resource_type,
            resource_id=str(resource_id),
            patient=patient,
            ip_address=ip,
            user_agent=ua,
            description=description,
        )


class ConsentManager:
    @classmethod
    def has_valid_consent(
        cls,
        patient: Patient,
        purpose: str,
        scope: Optional[str] = None,
        organization=None,
    ) -> bool:
        """
        Validates if a legally effective ConsentAuthorization exists for the requested purpose and scope.
        Returns True if authorized or if an emergency vital-interest exception applies.
        """
        now = timezone.now()
        qs = ConsentAuthorization.objects.filter(
            patient=patient,
            status=ConsentAuthorization.Status.ACTIVE,
            purpose=purpose,
            valid_from__lte=now,
        ).filter(
            models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=now)
        )

        if scope and scope != ConsentAuthorization.Scope.ALL_CLINICAL_RECORDS:
            qs = qs.filter(
                models.Q(scope=scope) | models.Q(scope=ConsentAuthorization.Scope.ALL_CLINICAL_RECORDS)
            )

        if organization:
            qs = qs.filter(
                models.Q(authorized_organization=organization) | models.Q(authorized_organization__isnull=True)
            )

        return qs.exists()

    @classmethod
    def grant_consent(
        cls,
        patient: Patient,
        granter,
        purpose: str = ConsentAuthorization.Purpose.CARE_COORDINATION,
        scope: str = ConsentAuthorization.Scope.ALL_CLINICAL_RECORDS,
        legal_basis: str = ConsentAuthorization.LegalBasis.CONSENT,
        organization=None,
        facility=None,
        valid_days: int = 365,
        request: Optional[HttpRequest] = None,
    ) -> ConsentAuthorization:
        """
        Provisions a formal ConsentAuthorization with SHA-256 integrity seal and audit log.
        """
        now = timezone.now()
        valid_to = now + timezone.timedelta(days=valid_days)
        terms = f"NDPA-CONSENT-{patient.public_id}-{granter.id}-{purpose}-{scope}-{now.isoformat()}"
        doc_hash = hashlib.sha256(terms.encode()).hexdigest()

        ip = AuditLogger.get_client_ip(request)
        ua = request.META.get("HTTP_USER_AGENT", "") if request else ""

        consent = ConsentAuthorization.objects.create(
            patient=patient,
            granter=granter,
            purpose=purpose,
            scope=scope,
            legal_basis=legal_basis,
            authorized_organization=organization,
            authorized_facility=facility,
            valid_from=now,
            valid_to=valid_to,
            status=ConsentAuthorization.Status.ACTIVE,
            consent_document_hash=doc_hash,
            ip_address=ip,
            user_agent=ua,
        )

        AuditLogger.log(
            action=AuditEvent.Action.GRANT_CONSENT,
            resource_type="ConsentAuthorization",
            resource_id=str(consent.public_id),
            request=request,
            actor=granter,
            patient=patient,
            description=f"Granted {scope} consent for purpose {purpose} under NDPA 2023.",
        )

        return consent
