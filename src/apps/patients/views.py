from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import permissions, viewsets

from apps.cases.models import CareSupportCase, MentalHealthScreening
from apps.funding.models import AssistanceAuthorization
from apps.payments.models import Payment

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


def patient_portal(request):
    """
    Patient & Caregiver Assistance Tracker.
    Provides equitable transparency for patients and family caregivers to look up
    active assistance case status, verified financial subsidy envelopes, assigned care team,
    and simulate low-bandwidth offline USSD (*384*2026#) and localized SMS alerts
    in English, Hausa, Yoruba, and Igbo.
    """
    query = request.GET.get("q", "").strip()
    selected_language = request.GET.get("lang", "en").lower()

    all_patients = Patient.objects.all().prefetch_related("external_identifiers", "caregiver_relationships")
    active_patient = None
    active_case = None

    if query:
        # Lookup by case number first
        case_match = CareSupportCase.objects.filter(case_number__iexact=query).select_related(
            "patient", "primary_clinical_need"
        ).first()
        if case_match:
            active_patient = case_match.patient
            active_case = case_match
        else:
            # Lookup by patient name, NIN, or hospital number
            active_patient = (
                all_patients.filter(first_name__icontains=query).first()
                or all_patients.filter(last_name__icontains=query).first()
                or all_patients.filter(external_identifiers__value__icontains=query).first()
            )
            if active_patient:
                active_case = (
                    CareSupportCase.objects.filter(patient=active_patient)
                    .select_related("primary_clinical_need")
                    .prefetch_related("assignments__assigned_to", "assistance_authorizations__facility", "mental_health_screenings")
                    .order_by("-opened_at")
                    .first()
                )
    else:
        # Default to first active patient
        active_patient = all_patients.first()
        if active_patient:
            active_case = (
                CareSupportCase.objects.filter(patient=active_patient)
                .select_related("primary_clinical_need")
                .prefetch_related("assignments__assigned_to", "assistance_authorizations__facility", "mental_health_screenings")
                .order_by("-opened_at")
                .first()
            )

    # Assistance Authorization & Balances
    authorizations = []
    total_authorized = 0
    total_disbursed = 0
    total_remaining = 0
    primary_facility_name = "Designated Federal Medical Centre"

    if active_case:
        authorizations = AssistanceAuthorization.objects.filter(case=active_case).select_related("facility")
        for auth in authorizations:
            total_authorized += auth.authorized_amount
            total_disbursed += auth.disbursed_amount
            total_remaining += auth.remaining_balance
            if auth.facility:
                primary_facility_name = auth.facility.name

    # Care Team
    care_team = []
    if active_case:
        care_team = active_case.assignments.filter(is_active=True).select_related("assigned_to")

    # Mental Health Screenings
    screenings = []
    if active_case:
        screenings = active_case.mental_health_screenings.all().order_by("-screened_at")

    # Patient Name
    patient_name = (
        f"{active_patient.first_name} {active_patient.last_name}"
        if active_patient else "Patient"
    )

    # Localized SMS Simulation
    sms_templates = {
        "en": (
            f"[NCD SafeCare] Dear {patient_name}, your clinical subsidy of ₦{total_authorized:,.2f} "
            f"at {primary_facility_name} is active. Remaining balance: ₦{total_remaining:,.2f}. "
            f"Zero out-of-pocket charges at hospital oncology/renal desk. Helpline: 0800-SAFE-NCD."
        ),
        "ha": (
            f"[NCD SafeCare] Sannu {patient_name}, an amince da tallafin lafiyarku na ₦{total_authorized:,.2f} "
            f"a asibitin {primary_facility_name}. Ragowar kudin tallafi: ₦{total_remaining:,.2f}. "
            f"Ba za ku biya komai a asibiti ba. Tuntubi: 0800-SAFE-NCD."
        ),
        "yo": (
            f"[NCD SafeCare] Bawo {patient_name}, iranlowo eto ilera re ti ₦{total_authorized:,.2f} "
            f"ni ile-iwosan {primary_facility_name} ti sise. Owo to ku: ₦{total_remaining:,.2f}. "
            f"O ko nilo lati sanwo kankan ni ile-iwosan. Fun iranlowo: 0800-SAFE-NCD."
        ),
        "ig": (
            f"[NCD SafeCare] Nno {patient_name}, enyemaka nlekota ahuike gi nke ruru ₦{total_authorized:,.2f} "
            f"na ulo ogwu {primary_facility_name} adila njikere. Ego fọdụrụ: ₦{total_remaining:,.2f}. "
            f"I gaghi akwu ugwo obula n'ulo ogwu. Kpọọ: 0800-SAFE-NCD."
        ),
    }

    # USSD Simulation (*384*2026#)
    ussd_menu = (
        f"NCD SafeCare USSD (*384*2026#)\n"
        f"-----------------------------\n"
        f"Welcome, {patient_name}\n"
        f"Case: {active_case.case_number if active_case else 'CASE-2026-001'}\n"
        f"1. Check Subsidy Balance (₦{total_remaining:,.2f} remaining)\n"
        f"2. Assigned Hospital: {primary_facility_name[:26]}\n"
        f"3. Mental Health Support Line (0800-SAFE-NCD)\n"
        f"4. Request Callback from Nurse Navigator\n"
        f"5. Emergency Transport Assistance"
    )

    context = {
        "active_patient": active_patient,
        "active_case": active_case,
        "all_patients": all_patients[:10],
        "authorizations": authorizations,
        "total_authorized": total_authorized,
        "total_disbursed": total_disbursed,
        "total_remaining": total_remaining,
        "primary_facility_name": primary_facility_name,
        "care_team": care_team,
        "screenings": screenings,
        "query": query,
        "selected_language": selected_language,
        "simulated_sms": sms_templates.get(selected_language, sms_templates["en"]),
        "simulated_ussd": ussd_menu,
    }

    return render(request, "portal/patient_portal.html", context)
