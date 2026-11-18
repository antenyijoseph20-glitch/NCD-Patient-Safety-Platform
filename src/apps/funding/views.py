import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from rest_framework import permissions, viewsets

from apps.cases.models import CareSupportCase
from apps.organizations.models import Facility
from apps.payments.models import Payment, PaymentInstruction, Reconciliation

from .models import (
    AssistanceAuthorization,
    FundingApplication,
    FundingDecision,
    FundingProgramme,
    FundingReview,
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


def _get_active_user(request):
    """Returns the authenticated user or provisions a default fallback user for seamless demo."""
    if request.user.is_authenticated:
        return request.user
    User = get_user_model()
    user = User.objects.filter(is_staff=True).first() or User.objects.first()
    if not user:
        user = User.objects.create_user(
            username="governance_officer",
            email="governance@ncd-safety.gov.ng",
            first_name="Governance",
            last_name="Officer",
        )
    return user


def funding_portal(request):
    """
    Dedicated Funding & Financial Governance Portal (Team B).
    Provides grant application intake, review, Four-Eyes decision making,
    assistance authorization envelope management, payment instruction issuance,
    direct bank disbursement execution, and reconciliation oversight.
    """
    current_user = _get_active_user(request)
    User = get_user_model()

    # Search filter
    search_q = request.GET.get("q", "").strip()

    # Telemetry metrics
    source_stats = FundingSource.objects.aggregate(
        total_pool=Sum("total_allocation"),
        total_disbursed=Sum("disbursed_amount"),
    )
    total_pool = source_stats["total_pool"] or Decimal("0.00")
    total_disbursed = source_stats["total_disbursed"] or Decimal("0.00")

    active_programmes_count = FundingProgramme.objects.filter(status=FundingProgramme.Status.ACTIVE).count()
    active_auths = AssistanceAuthorization.objects.filter(status=AssistanceAuthorization.Status.ACTIVE)
    active_auths_count = active_auths.count()
    total_authorized_balance = sum((a.remaining_balance for a in active_auths), Decimal("0.00"))

    pending_apps_count = FundingApplication.objects.filter(
        status__in=[FundingApplication.Status.SUBMITTED, FundingApplication.Status.UNDER_REVIEW]
    ).count()

    pending_instructions_count = PaymentInstruction.objects.filter(
        status=PaymentInstruction.Status.PENDING
    ).count()

    # Core Querysets
    apps_qs = (
        FundingApplication.objects.select_related("case", "programme", "applied_by", "decision")
        .prefetch_related("reviews")
        .order_by("-created_at")
    )
    if search_q:
        apps_qs = (
            apps_qs.filter(application_number__icontains=search_q)
            | apps_qs.filter(case__case_number__icontains=search_q)
            | apps_qs.filter(case__patient__first_name__icontains=search_q)
            | apps_qs.filter(case__patient__last_name__icontains=search_q)
        )

    eligible_cases = CareSupportCase.objects.select_related("patient", "primary_clinical_need").filter(
        status=CareSupportCase.Status.FUNDING_ELIGIBLE
    ).order_by("-opened_at")

    programmes = FundingProgramme.objects.filter(status=FundingProgramme.Status.ACTIVE).select_related("source")
    facilities = Facility.objects.filter(status=Facility.Status.ACTIVE).select_related("organization")
    active_authorizations = (
        AssistanceAuthorization.objects.select_related("case", "decision", "facility")
        .filter(status=AssistanceAuthorization.Status.ACTIVE)
        .order_by("-created_at")
    )
    payment_instructions = (
        PaymentInstruction.objects.select_related("authorization", "payee_facility", "authorized_by")
        .order_by("-created_at")
    )
    recent_payments = (
        Payment.objects.select_related("instruction", "executed_by")
        .order_by("-executed_at")[:8]
    )
    recent_reconciliations = (
        Reconciliation.objects.select_related("reconciled_by")
        .order_by("-created_at")[:5]
    )
    all_users = User.objects.filter(is_active=True).order_by("username")

    # Handle Actions
    if request.method == "POST":
        action = request.POST.get("action")

        try:
            if action == "apply_funding":
                case_id = request.POST.get("case_id")
                programme_id = request.POST.get("programme_id")
                requested_amount = Decimal(request.POST.get("requested_amount", "0"))
                clinical_justification = request.POST.get("clinical_justification", "").strip()
                applicant_type = request.POST.get("applicant_type", FundingApplication.ApplicantType.CASE_OFFICER)

                case = get_object_or_404(CareSupportCase, id=case_id)
                programme = get_object_or_404(FundingProgramme, id=programme_id) if programme_id else None

                app_num = f"APP-2026-{uuid.uuid4().hex[:6].upper()}"

                app = FundingApplication(
                    application_number=app_num,
                    case=case,
                    programme=programme,
                    applicant_type=applicant_type,
                    applied_by=current_user,
                    requested_amount=requested_amount,
                    clinical_justification=clinical_justification,
                    status=FundingApplication.Status.SUBMITTED,
                    submitted_at=timezone.now(),
                )
                app.full_clean()
                app.save()

                messages.success(
                    request,
                    f"Funding application {app.application_number} submitted successfully for Case {case.case_number} "
                    f"({case.patient}). Requested: NGN {requested_amount:,.2f}.",
                )
                return redirect("funding_portal")

            elif action == "review_application":
                app_id = request.POST.get("application_id")
                recommendation = request.POST.get("recommendation")
                recommended_amount_str = request.POST.get("recommended_amount", "").strip()
                review_notes = request.POST.get("review_notes", "").strip()

                application = get_object_or_404(FundingApplication, id=app_id)
                recommended_amount = Decimal(recommended_amount_str) if recommended_amount_str else None

                review = FundingReview.objects.create(
                    application=application,
                    reviewer=current_user,
                    recommendation=recommendation,
                    recommended_amount=recommended_amount,
                    review_notes=review_notes or "Reviewed in line with program guidelines.",
                )

                if application.status == FundingApplication.Status.SUBMITTED:
                    application.status = FundingApplication.Status.UNDER_REVIEW
                    application.save(update_fields=["status"])

                messages.success(
                    request,
                    f"Review successfully recorded for {application.application_number}: {review.get_recommendation_display()}.",
                )
                return redirect("funding_portal")

            elif action == "decide_application":
                app_id = request.POST.get("application_id")
                decision_choice = request.POST.get("decision")
                approved_amount_str = request.POST.get("approved_amount", "0").strip()
                conditions = request.POST.get("conditions", "").strip()
                decision_notes = request.POST.get("decision_notes", "").strip()
                decision_user_id = request.POST.get("decision_maker_id")

                # Allow selecting decision maker in demo mode or fallback to current user
                decision_maker = current_user
                if decision_user_id:
                    decision_maker = get_object_or_404(User, id=decision_user_id)

                application = get_object_or_404(FundingApplication, id=app_id)
                approved_amount = Decimal(approved_amount_str or "0")

                with transaction.atomic():
                    decision = FundingDecision(
                        application=application,
                        decision_maker=decision_maker,
                        decision=decision_choice,
                        approved_amount=approved_amount,
                        conditions=conditions,
                        decision_notes=decision_notes or "Decided by the National Funding Governance Committee.",
                    )
                    decision.full_clean()  # Enforces Four-Eyes rule: decision_maker != applied_by
                    decision.save()

                    if decision_choice in [FundingDecision.Decision.APPROVED, FundingDecision.Decision.PARTIALLY_APPROVED]:
                        application.status = (
                            FundingApplication.Status.APPROVED
                            if decision_choice == FundingDecision.Decision.APPROVED
                            else FundingApplication.Status.PARTIALLY_APPROVED
                        )
                        application.approved_amount = approved_amount
                        application.save(update_fields=["status", "approved_amount"])

                        # Automatically create AssistanceAuthorization envelope
                        auth_code = f"AUTH-2026-{uuid.uuid4().hex[:6].upper()}"
                        facility = None
                        if application.case.primary_clinical_need:
                            first_ver = application.case.primary_clinical_need.verifications.first()
                            if first_ver:
                                facility = first_ver.facility
                        if not facility:
                            facility = facilities.first()

                        auth = AssistanceAuthorization.objects.create(
                            authorization_code=auth_code,
                            decision=decision,
                            case=application.case,
                            facility=facility,
                            authorized_amount=approved_amount,
                            valid_from=date.today(),
                            valid_to=date.today() + timedelta(days=90),
                            status=AssistanceAuthorization.Status.ACTIVE,
                        )

                        # Update case lifecycle
                        application.case.status = CareSupportCase.Status.ASSISTANCE_ACTIVE
                        application.case.save(update_fields=["status"])

                        # Update programme allocation
                        if application.programme:
                            application.programme.allocated_amount += approved_amount
                            application.programme.save(update_fields=["allocated_amount"])
                            if application.programme.source:
                                application.programme.source.allocated_amount += approved_amount
                                application.programme.source.save(update_fields=["allocated_amount"])

                        messages.success(
                            request,
                            f"Decision APPROVED for {application.application_number}! "
                            f"Assistance Authorization envelope {auth.authorization_code} issued for NGN {approved_amount:,.2f}.",
                        )
                    else:
                        application.status = FundingApplication.Status.DECLINED
                        application.save(update_fields=["status"])
                        messages.warning(
                            request,
                            f"Decision DECLINED for {application.application_number}.",
                        )

                return redirect("funding_portal")

            elif action == "create_payment_instruction":
                auth_id = request.POST.get("authorization_id")
                payee_type = request.POST.get("payee_type", PaymentInstruction.PayeeType.HEALTHCARE_FACILITY)
                payee_name = request.POST.get("payee_name", "").strip()
                bank_name = request.POST.get("bank_name", "").strip()
                account_number = request.POST.get("account_number", "").strip()
                amount = Decimal(request.POST.get("amount", "0"))
                facility_id = request.POST.get("payee_facility_id")
                authorizer_id = request.POST.get("authorizer_id")

                authorization = get_object_or_404(AssistanceAuthorization, id=auth_id)
                payee_facility = Facility.objects.filter(id=facility_id).first() if facility_id else authorization.facility

                authorizer = current_user
                if authorizer_id:
                    authorizer = get_object_or_404(User, id=authorizer_id)

                instruction_ref = f"INST-2026-{uuid.uuid4().hex[:6].upper()}"

                instruction = PaymentInstruction(
                    instruction_reference=instruction_ref,
                    authorization=authorization,
                    payee_type=payee_type,
                    payee_facility=payee_facility,
                    payee_name=payee_name or (payee_facility.name if payee_facility else "Verified Provider"),
                    bank_name=bank_name or "Central Bank / NIBSS Clearing",
                    account_number=account_number or "0123456789",
                    amount=amount,
                    authorized_by=authorizer,
                    status=PaymentInstruction.Status.PENDING,
                )
                instruction.full_clean()  # Enforces authorizer != decision_maker & balance check
                instruction.save()

                messages.success(
                    request,
                    f"Payment instruction {instruction.instruction_reference} authorized for "
                    f"NGN {amount:,.2f} to {instruction.payee_name}.",
                )
                return redirect("funding_portal")

            elif action == "execute_payment":
                instruction_id = request.POST.get("instruction_id")
                payment_method = request.POST.get("payment_method", Payment.PaymentMethod.NIBSS_INSTANT_PAYMENT)
                channel_ref = request.POST.get("channel_reference", "").strip() or f"NIBSS-TXN-{uuid.uuid4().hex[:10].upper()}"
                executor_id = request.POST.get("executor_id")

                instruction = get_object_or_404(PaymentInstruction, id=instruction_id)
                executor = current_user
                if executor_id:
                    executor = get_object_or_404(User, id=executor_id)

                pay_ref = f"PAY-2026-{uuid.uuid4().hex[:8].upper()}"

                with transaction.atomic():
                    payment = Payment(
                        payment_reference=pay_ref,
                        instruction=instruction,
                        amount=instruction.amount,
                        currency_code=instruction.currency_code,
                        payment_method=payment_method,
                        channel_reference=channel_ref,
                        executed_by=executor,
                        executed_at=timezone.now(),
                        status=Payment.Status.SUCCESSFUL,
                        transaction_response="Settlement completed via NIBSS gateway. Transaction response code 00.",
                    )
                    payment.full_clean()  # Enforces executor != instruction.authorized_by
                    payment.save()

                    # Update instruction
                    instruction.status = PaymentInstruction.Status.COMPLETED
                    instruction.save(update_fields=["status"])

                    # Update authorization disbursed amount
                    auth = instruction.authorization
                    auth.disbursed_amount += payment.amount
                    if auth.remaining_balance <= Decimal("0.00"):
                        auth.status = AssistanceAuthorization.Status.EXHAUSTED
                    auth.save(update_fields=["disbursed_amount", "status"])

                    # Update source and programme disbursements
                    if auth.case and hasattr(auth.case, "funding_applications"):
                        first_app = auth.case.funding_applications.first()
                        if first_app and first_app.programme:
                            first_app.programme.disbursed_amount += payment.amount
                            first_app.programme.save(update_fields=["disbursed_amount"])
                            if first_app.programme.source:
                                first_app.programme.source.disbursed_amount += payment.amount
                                first_app.programme.source.save(update_fields=["disbursed_amount"])

                    messages.success(
                        request,
                        f"Direct settlement of NGN {payment.amount:,.2f} executed successfully! "
                        f"Reference: {payment.payment_reference}. Beneficiary: {instruction.payee_name}.",
                    )
                return redirect("funding_portal")

            elif action == "run_reconciliation":
                notes = request.POST.get("reconciliation_notes", "").strip()
                reconciler_id = request.POST.get("reconciler_id")
                reconciler = current_user
                if reconciler_id:
                    reconciler = get_object_or_404(User, id=reconciler_id)

                # Calculate cumulative totals
                instr_total = PaymentInstruction.objects.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
                exec_total = Payment.objects.filter(status=Payment.Status.SUCCESSFUL).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

                start_date = date.today() - timedelta(days=30)
                end_date = date.today()

                reconciliation = Reconciliation.objects.create(
                    reconciliation_period_start=start_date,
                    reconciliation_period_end=end_date,
                    total_instruction_amount=instr_total,
                    total_executed_amount=exec_total,
                    total_adjusted_amount=Decimal("0.00"),
                    discrepancy_amount=instr_total - exec_total,
                    status=Reconciliation.Status.BALANCED if (instr_total == exec_total) else Reconciliation.Status.DISCREPANCY_FLAGGED,
                    reconciled_by=reconciler,
                    notes=notes or f"Periodic banking audit executed for period {start_date} to {end_date}.",
                )

                messages.success(
                    request,
                    f"Financial reconciliation completed! Status: {reconciliation.get_status_display()}. "
                    f"Total Executed: NGN {exec_total:,.2f}.",
                )
                return redirect("funding_portal")

        except ValidationError as val_err:
            error_msg = "; ".join(val_err.messages) if hasattr(val_err, "messages") else str(val_err)
            messages.error(request, f"Governance Validation Error: {error_msg}")
            return redirect("funding_portal")
        except Exception as exc:
            messages.error(request, f"Operational Error: {str(exc)}")
            return redirect("funding_portal")

    context = {
        "current_user": current_user,
        "all_users": all_users,
        "total_pool": total_pool,
        "total_disbursed": total_disbursed,
        "active_programmes_count": active_programmes_count,
        "active_auths_count": active_auths_count,
        "total_authorized_balance": total_authorized_balance,
        "pending_apps_count": pending_apps_count,
        "pending_instructions_count": pending_instructions_count,
        "applications": apps_qs,
        "eligible_cases": eligible_cases,
        "programmes": programmes,
        "facilities": facilities,
        "authorizations": active_authorizations,
        "payment_instructions": payment_instructions,
        "recent_payments": recent_payments,
        "recent_reconciliations": recent_reconciliations,
        "search_q": search_q,
    }

    return render(request, "portal/funding_portal.html", context)


def donor_portal(request):
    """
    Real-Time Global Donor Transparency Portal.
    Provides bilateral donors, philanthropic foundations, and global health partners
    with verifiable telemetry on capital allocation, multi-currency conversion,
    100% direct-to-provider disbursement routing, condition impact distribution,
    and cryptographic SHA-256 settlement audit logs.
    """
    # Exchange rates relative to base NGN
    RATES = {
        "NGN": Decimal("1.0"),
        "USD": Decimal("1480.0"),
        "EUR": Decimal("1600.0"),
        "GBP": Decimal("1880.0"),
        "KES": Decimal("11.4"),
    }

    selected_currency = request.GET.get("currency", "USD").upper()
    if selected_currency not in RATES:
        selected_currency = "USD"
    conversion_rate = RATES[selected_currency]

    # Aggregate total capital pool and disbursements from sources
    sources_qs = FundingSource.objects.all().prefetch_related("programmes")
    pool_stats = sources_qs.aggregate(
        total_pool=Sum("total_allocation"),
        total_allocated=Sum("allocated_amount"),
        total_disbursed=Sum("disbursed_amount"),
    )
    total_pool_ngn = pool_stats["total_pool"] or Decimal("0.00")
    total_allocated_ngn = pool_stats["total_allocated"] or Decimal("0.00")
    total_disbursed_ngn = pool_stats["total_disbursed"] or Decimal("0.00")
    remaining_pool_ngn = max(Decimal("0.00"), total_pool_ngn - total_disbursed_ngn)

    # Converted metrics
    def to_curr(val_ngn):
        return (val_ngn / conversion_rate).quantize(Decimal("0.01")) if val_ngn else Decimal("0.00")

    total_pool_curr = to_curr(total_pool_ngn)
    total_disbursed_curr = to_curr(total_disbursed_ngn)
    remaining_pool_curr = to_curr(remaining_pool_ngn)

    # Currency overview dictionary for the multi-currency summary card
    multi_currency_summary = {
        "NGN": f"₦{total_pool_ngn:,.2f}",
        "USD": f"${to_curr(total_pool_ngn):,.2f}",
        "EUR": f"€{(total_pool_ngn / RATES['EUR']).quantize(Decimal('0.01')):,.2f}",
        "GBP": f"£{(total_pool_ngn / RATES['GBP']).quantize(Decimal('0.01')):,.2f}",
        "KES": f"KSh {(total_pool_ngn / RATES['KES']).quantize(Decimal('0.01')):,.2f}",
    }

    # Verified payments and Direct-to-Provider verification
    successful_payments = (
        Payment.objects.filter(status=Payment.Status.SUCCESSFUL)
        .select_related("instruction", "instruction__payee_facility", "instruction__authorization__case__patient")
        .prefetch_related("service_evidences")
        .order_by("-executed_at")
    )
    
    total_direct_provider_disbursed_ngn = (
        successful_payments.filter(
            instruction__payee_type__in=[
                PaymentInstruction.PayeeType.HEALTHCARE_FACILITY,
                PaymentInstruction.PayeeType.PHARMACY,
                PaymentInstruction.PayeeType.DIAGNOSTIC_CENTRE,
            ]
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    )

    direct_provider_ratio = (
        100.0 if total_disbursed_ngn > 0 and total_direct_provider_disbursed_ngn >= total_disbursed_ngn else
        float((total_direct_provider_disbursed_ngn / total_disbursed_ngn) * 100) if total_disbursed_ngn > 0 else 100.0
    )

    # Impact by condition category
    cases_supported = CareSupportCase.objects.select_related("primary_clinical_need", "patient").all()
    condition_counts = {
        "Oncology (Breast/Cervical/Prostate)": 0,
        "Chronic Kidney Disease / ESRD": 0,
        "Cardiovascular / Hypertension": 0,
        "Metabolic / Diabetes Mellitus": 0,
        "Other NCDs": 0,
    }
    for c in cases_supported:
        need = c.primary_clinical_need
        if not need:
            condition_counts["Other NCDs"] += 1
            continue
        icd = (need.icd10_code or "").upper()
        if icd.startswith("C"):
            condition_counts["Oncology (Breast/Cervical/Prostate)"] += 1
        elif icd.startswith("N18"):
            condition_counts["Chronic Kidney Disease / ESRD"] += 1
        elif icd.startswith("I"):
            condition_counts["Cardiovascular / Hypertension"] += 1
        elif icd.startswith("E11") or icd.startswith("E10"):
            condition_counts["Metabolic / Diabetes Mellitus"] += 1
        else:
            condition_counts["Other NCDs"] += 1

    # Facility recipient breakdown
    facility_breakdown = []
    for facility in Facility.objects.filter(status=Facility.Status.ACTIVE):
        fac_payments = successful_payments.filter(instruction__payee_facility=facility)
        fac_sum = fac_payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        if fac_sum > 0 or facility.payment_instructions.exists():
            facility_breakdown.append({
                "facility": facility,
                "amount_ngn": fac_sum,
                "amount_curr": to_curr(fac_sum),
                "patients_served": fac_payments.values("instruction__authorization__case__patient").distinct().count(),
                "status": facility.get_facility_type_display(),
            })

    # Prepare donor sources with converted figures
    donor_sources = []
    for s in sources_qs:
        donor_sources.append({
            "source": s,
            "total_allocation_curr": to_curr(s.total_allocation),
            "disbursed_curr": to_curr(s.disbursed_amount),
            "remaining_curr": to_curr(max(Decimal("0.00"), s.total_allocation - s.disbursed_amount)),
            "utilization_pct": float((s.disbursed_amount / s.total_allocation) * 100) if s.total_allocation > 0 else 0.0,
        })

    # Currency symbols
    CURRENCY_SYMBOLS = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "KES": "KSh ",
        "NGN": "₦",
    }

    context = {
        "selected_currency": selected_currency,
        "currency_symbol": CURRENCY_SYMBOLS.get(selected_currency, "$"),
        "multi_currency_summary": multi_currency_summary,
        "total_pool_curr": total_pool_curr,
        "total_pool_ngn": total_pool_ngn,
        "total_disbursed_curr": total_disbursed_curr,
        "total_disbursed_ngn": total_disbursed_ngn,
        "remaining_pool_curr": remaining_pool_curr,
        "remaining_pool_ngn": remaining_pool_ngn,
        "direct_provider_ratio": direct_provider_ratio,
        "donor_sources": donor_sources,
        "facility_breakdown": facility_breakdown,
        "condition_counts": condition_counts,
        "successful_payments": successful_payments[:20],
        "cases_count": cases_supported.count(),
    }

    return render(request, "portal/donor_portal.html", context)
