from datetime import date, timedelta
from decimal import Decimal
import logging
import uuid

from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import Payment, PaymentInstruction, Reconciliation, ServiceEvidence

logger = logging.getLogger(__name__)


@shared_task(name="payments.execute_batch_payment_instructions")
def execute_batch_payment_instructions():
    """
    Asynchronously processes pending payment instructions through the mock NIBSS
    settlement gateway, generates payment references, and executes payouts.
    """
    pending = PaymentInstruction.objects.filter(status=PaymentInstruction.Status.PENDING).select_related(
        "authorization", "authorized_by"
    )
    User = get_user_model()
    system_executor = User.objects.filter(is_staff=True).exclude(id__in=[p.authorized_by_id for p in pending]).first()
    if not system_executor:
        system_executor = User.objects.first()

    processed_count = 0
    total_amount = Decimal("0.00")

    for instruction in pending:
        # Four-Eyes check: executor != authorizer
        if system_executor and system_executor.id == instruction.authorized_by_id:
            continue

        with transaction.atomic():
            payment_ref = f"PAY-AUTO-{uuid.uuid4().hex[:8].upper()}"
            channel_ref = f"NIP-BATCH-{uuid.uuid4().hex[:10].upper()}"

            payment = Payment.objects.create(
                payment_reference=payment_ref,
                instruction=instruction,
                amount=instruction.amount,
                currency_code=instruction.currency_code,
                payment_method=Payment.PaymentMethod.NIBSS_INSTANT_PAYMENT,
                channel_reference=channel_ref,
                executed_by=system_executor,
                executed_at=timezone.now(),
                status=Payment.Status.SUCCESSFUL,
                transaction_response="Batch settlement executed successfully via NIBSS Clearing Gateway.",
            )

            instruction.status = PaymentInstruction.Status.COMPLETED
            instruction.save(update_fields=["status"])

            auth = instruction.authorization
            auth.disbursed_amount += payment.amount
            if auth.remaining_balance <= Decimal("0.00"):
                auth.status = auth.Status.EXHAUSTED
            auth.save(update_fields=["disbursed_amount", "status"])

            processed_count += 1
            total_amount += payment.amount

    logger.info(f"[SETTLEMENT] Auto-processed {processed_count} instructions totaling NGN {total_amount:,.2f}.")
    return {"processed_count": processed_count, "total_amount": str(total_amount)}


@shared_task(name="payments.run_periodic_reconciliation")
def run_periodic_reconciliation(period_days: int = 30):
    """
    Automated periodic reconciliation comparing total payment instructions
    against executed settlements and ledger balances.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=period_days)

    instructions_total = (
        PaymentInstruction.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date).aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    executed_total = (
        Payment.objects.filter(
            status=Payment.Status.SUCCESSFUL, executed_at__date__gte=start_date, executed_at__date__lte=end_date
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    discrepancy = instructions_total - executed_total
    status = Reconciliation.Status.BALANCED if discrepancy == Decimal("0.00") else Reconciliation.Status.DISCREPANCY_FLAGGED

    User = get_user_model()
    auditor = User.objects.filter(is_staff=True).first() or User.objects.first()

    rec = Reconciliation.objects.create(
        reconciliation_period_start=start_date,
        reconciliation_period_end=end_date,
        total_instruction_amount=instructions_total,
        total_executed_amount=executed_total,
        total_adjusted_amount=Decimal("0.00"),
        discrepancy_amount=discrepancy,
        status=status,
        reconciled_by=auditor,
        notes=f"Automated Celery periodic audit for period {start_date} to {end_date}.",
    )

    logger.info(f"[RECONCILIATION] Completed reconciliation ID {rec.id}: Status {status}.")
    return {
        "reconciliation_id": rec.id,
        "status": status,
        "discrepancy": str(discrepancy),
    }
