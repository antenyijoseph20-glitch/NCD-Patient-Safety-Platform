from datetime import date, timedelta
from decimal import Decimal
import logging

from celery import shared_task
from django.db.models import Sum

from .models import AssistanceAuthorization, FundingApplication, FundingProgramme

logger = logging.getLogger(__name__)


@shared_task(name="funding.notify_application_decision")
def notify_application_decision(application_id: int):
    """
    Asynchronous notification task dispatched upon committee decision.
    Alerts case officers, patient liaison, and healthcare facility.
    """
    try:
        app = FundingApplication.objects.select_related("case__patient", "applied_by", "decision").get(id=application_id)
        decision = getattr(app, "decision", None)
        decision_label = decision.get_decision_display() if decision else app.get_status_display()
        
        logger.info(
            f"[NOTIFICATION] Funding Application {app.application_number} for {app.case.patient} "
            f"has been marked {decision_label}. Applicant {app.applied_by.username} notified."
        )
        return {
            "status": "notified",
            "application_number": app.application_number,
            "decision": decision_label,
        }
    except FundingApplication.DoesNotExist:
        logger.error(f"Funding application with ID {application_id} does not exist.")
        return {"status": "error", "message": "Application not found"}


@shared_task(name="funding.audit_expiring_authorizations")
def audit_expiring_authorizations():
    """
    Scheduled governance audit: Flags authorizations expiring within 7 days
    and transitions past-due active authorizations to EXPIRED.
    """
    today = date.today()
    expiring_soon = AssistanceAuthorization.objects.filter(
        status=AssistanceAuthorization.Status.ACTIVE,
        valid_to__lte=today + timedelta(days=7),
        valid_to__gte=today,
    )

    expired_updated = AssistanceAuthorization.objects.filter(
        status=AssistanceAuthorization.Status.ACTIVE,
        valid_to__lt=today,
    ).update(status=AssistanceAuthorization.Status.EXPIRED)

    logger.info(
        f"[AUDIT] Expiring authorizations: {expiring_soon.count()} flagged. "
        f"Past-due authorizations marked expired: {expired_updated}."
    )
    return {
        "expiring_soon_count": expiring_soon.count(),
        "expired_updated_count": expired_updated,
    }


@shared_task(name="funding.recompute_programme_allocations")
def recompute_programme_allocations(programme_id: int):
    """
    Background recalculation of allocated and disbursed amounts for a funding programme.
    """
    try:
        programme = FundingProgramme.objects.get(id=programme_id)
        alloc = (
            programme.applications.filter(status=FundingApplication.Status.APPROVED).aggregate(
                total=Sum("approved_amount")
            )["total"]
            or Decimal("0.00")
        )
        programme.allocated_amount = alloc
        programme.save(update_fields=["allocated_amount"])
        return {"programme": programme.name, "recomputed_allocation": str(alloc)}
    except FundingProgramme.DoesNotExist:
        return {"error": "Programme not found"}
