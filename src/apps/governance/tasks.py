from datetime import timedelta
import logging

from celery import shared_task
from django.utils import timezone

from .models import AuditEvent, ConsentAuthorization
from .services import AuditLogger

logger = logging.getLogger(__name__)


@shared_task(name="governance.audit_expiring_consents")
def audit_expiring_consents():
    """
    NDPA 2023 Periodic Compliance Audit:
    Flags patient data consent authorizations expiring within 14 days,
    and transitions past-due authorizations to EXPIRED with cryptographic audit event.
    """
    now = timezone.now()
    cutoff_14d = now + timedelta(days=14)

    expiring_soon = ConsentAuthorization.objects.filter(
        status=ConsentAuthorization.Status.ACTIVE,
        valid_to__isnull=False,
        valid_to__lte=cutoff_14d,
        valid_to__gte=now,
    )

    past_due = ConsentAuthorization.objects.filter(
        status=ConsentAuthorization.Status.ACTIVE,
        valid_to__isnull=False,
        valid_to__lt=now,
    )

    expired_count = 0
    for consent in past_due:
        consent.status = ConsentAuthorization.Status.EXPIRED
        consent.save(update_fields=["status"])
        AuditLogger.log(
            action=AuditEvent.Action.WITHDRAW_CONSENT,
            resource_type="ConsentAuthorization",
            resource_id=consent.public_id,
            patient=consent.patient,
            description="Consent authorization automatically expired by governance audit scheduler.",
        )
        expired_count += 1

    logger.info(
        f"[NDPA_AUDIT] Expiring consent authorizations: {expiring_soon.count()} flagged. "
        f"Past-due consents expired: {expired_count}."
    )
    return {
        "expiring_soon_count": expiring_soon.count(),
        "expired_count": expired_count,
    }
