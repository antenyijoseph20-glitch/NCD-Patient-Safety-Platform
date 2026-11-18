from datetime import timedelta
import logging

from celery import shared_task
from django.utils import timezone

from .models import Notification, USSDSession
from .services import NotificationService

logger = logging.getLogger(__name__)


@shared_task(name="communication.dispatch_pending_notifications")
def dispatch_pending_notifications(limit: int = 50):
    """
    Periodically processes notifications queued in the outbound queue.
    """
    pending = Notification.objects.filter(status=Notification.Status.QUEUED)[:limit]
    dispatched_count = 0
    failed_count = 0

    for notif in pending:
        success = NotificationService.dispatch_notification(notif)
        if success:
            dispatched_count += 1
        else:
            failed_count += 1

    logger.info(f"[OUTBOUND_COMM] Dispatched {dispatched_count} notifications, {failed_count} failed.")
    return {"dispatched": dispatched_count, "failed": failed_count}


@shared_task(name="communication.cleanup_stale_ussd_sessions")
def cleanup_stale_ussd_sessions():
    """
    Closes USSD sessions older than 30 minutes.
    """
    cutoff = timezone.now() - timedelta(minutes=30)
    updated = USSDSession.objects.filter(is_active=True, last_interaction_at__lt=cutoff).update(is_active=False)
    logger.info(f"[USSD] Closed {updated} stale USSD sessions.")
    return {"closed_sessions": updated}
