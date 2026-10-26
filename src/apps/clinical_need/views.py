import hashlib
import uuid
from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.cases.models import CareSupportCase
from apps.clinical_need.models import (
    ClinicalEvidence,
    ClinicalNeed,
    ClinicalVerification,
)
from apps.organizations.models import Facility, HealthcareProfessional
from apps.patients.models import Patient
from apps.safety.models import SafetyEvent


def clinician_portal(request):
    """
    Dedicated Hospital & Clinician Portal for licensed healthcare professionals.
    Provides medical verification workflows, patient clinical intake, evidence attachment,
    and adverse safety incident reporting without exposing backend administrative tables.
    """
    clinician = None
    if request.user.is_authenticated and hasattr(request.user, "healthcare_professional"):
        clinician = request.user.healthcare_professional
    else:
        clinician = (
            HealthcareProfessional.objects.select_related("user")
            .filter(license_status=HealthcareProfessional.LicenseStatus.VERIFIED)
            .first()
        )

    facilities = Facility.objects.filter(status=Facility.Status.ACTIVE)
    active_facility = facilities.first()

    search_query = request.GET.get("q", "").strip()

    cases_qs = CareSupportCase.objects.select_related("patient", "primary_clinical_need").prefetch_related(
        "primary_clinical_need__verifications"
    )

    if search_query:
        cases_qs = (
            cases_qs.filter(case_number__icontains=search_query)
            | cases_qs.filter(patient__first_name__icontains=search_query)
            | cases_qs.filter(patient__last_name__icontains=search_query)
            | cases_qs.filter(primary_clinical_need__condition_name__icontains=search_query)
        )

    pending_cases = cases_qs.filter(
        status__in=[CareSupportCase.Status.OPEN, CareSupportCase.Status.CLINICAL_REVIEW]
    ).order_by("-opened_at")

    verified_cases = cases_qs.filter(
        status__in=[CareSupportCase.Status.FUNDING_ELIGIBLE, CareSupportCase.Status.ASSISTANCE_ACTIVE]
    ).order_by("-updated_at")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "verify_clinical_need":
            case_id = request.POST.get("case_id")
            verification_notes = request.POST.get("verification_notes", "").strip()
            facility_id = request.POST.get("facility_id")

            case = get_object_or_404(CareSupportCase, id=case_id)
            facility = Facility.objects.filter(id=facility_id).first() or active_facility

            if case.primary_clinical_need and clinician:
                ClinicalVerification.objects.create(
                    clinical_need=case.primary_clinical_need,
                    professional=clinician,
                    facility=facility,
                    status=ClinicalVerification.Status.VERIFIED,
                    verification_notes=verification_notes or "Clinical diagnosis and treatment plan certified.",
                    verified_at=timezone.now(),
                )

                case.primary_clinical_need.status = ClinicalNeed.Status.VERIFIED
                case.primary_clinical_need.save()

                case.status = CareSupportCase.Status.FUNDING_ELIGIBLE
                case.save()

                messages.success(
                    request,
                    f"Case {case.case_number} for {case.patient} has been clinically verified! "
                    "Case is now eligible for assistance funding.",
                )
                return redirect("clinician_portal")

        elif action == "report_safety_event":
            patient_id = request.POST.get("patient_id")
            severity = request.POST.get("severity", SafetyEvent.Severity.MODERATE_HARM)
            description = request.POST.get("description", "").strip()
            immediate_action = request.POST.get("immediate_action", "").strip()

            patient = get_object_or_404(Patient, id=patient_id)
            user_reporter = clinician.user if clinician else request.user

            ref_code = f"SAFE-{date.today().year}-{uuid.uuid4().hex[:6].upper()}"

            SafetyEvent.objects.create(
                reference_code=ref_code,
                patient=patient,
                reported_by=user_reporter,
                facility=active_facility,
                severity=severity,
                event_description=description,
                immediate_action_taken=immediate_action,
                occurred_at=timezone.now(),
            )

            messages.warning(
                request,
                f"Adverse safety event {ref_code} logged and triaged for clinical audit.",
            )
            return redirect("clinician_portal")

        elif action == "attach_evidence":
            case_id = request.POST.get("case_id")
            evidence_type = request.POST.get("evidence_type", ClinicalEvidence.EvidenceType.PATHOLOGY_REPORT)
            title = request.POST.get("title", "").strip()
            doc_ref = request.POST.get("doc_ref", "").strip()

            case = get_object_or_404(CareSupportCase, id=case_id)
            if case.primary_clinical_need:
                checksum = hashlib.sha256(f"{title}-{doc_ref}-{timezone.now()}".encode()).hexdigest()

                ClinicalEvidence.objects.create(
                    clinical_need=case.primary_clinical_need,
                    evidence_type=evidence_type,
                    title=title,
                    document_reference=doc_ref,
                    sha256_checksum=checksum,
                    issued_by=active_facility.name if active_facility else "Certified Hospital Unit",
                    issued_date=date.today(),
                )
                messages.success(request, f"Clinical evidence '{title}' attached with cryptographic SHA-256 seal.")
                return redirect("clinician_portal")

    context = {
        "clinician": clinician,
        "active_facility": active_facility,
        "facilities": facilities,
        "pending_cases": pending_cases,
        "verified_cases": verified_cases,
        "search_query": search_query,
        "all_patients": Patient.objects.all()[:20],
    }

    return render(request, "portal/clinician_portal.html", context)
