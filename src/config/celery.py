import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("ncd_platform")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Celery Beat Periodic Schedulers for Autonomous Governance, Settlements & Patient Safety
app.conf.beat_schedule = {
    "payments-execute-batch-settlements": {
        "task": "payments.execute_batch_payment_instructions",
        "schedule": 900.0,  # Every 15 minutes
    },
    "payments-midnight-reconciliation": {
        "task": "payments.run_periodic_reconciliation",
        "schedule": crontab(hour=0, minute=0),  # Daily at midnight
    },
    "funding-audit-expiring-authorizations": {
        "task": "funding.audit_expiring_authorizations",
        "schedule": crontab(hour=1, minute=0),  # Daily at 01:00 AM
    },
    "governance-audit-expiring-consents": {
        "task": "governance.audit_expiring_consents",
        "schedule": crontab(hour=2, minute=0),  # Daily at 02:00 AM
    },
    "communication-dispatch-pending-notifications": {
        "task": "communication.dispatch_pending_notifications",
        "schedule": 60.0,  # Every 60 seconds
    },
    "communication-cleanup-stale-ussd-sessions": {
        "task": "communication.cleanup_stale_ussd_sessions",
        "schedule": 1800.0,  # Every 30 minutes
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
