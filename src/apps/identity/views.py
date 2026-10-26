from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import render

from apps.cases.models import CareSupportCase
from apps.funding.models import AssistanceAuthorization, FundingProgramme
from apps.organizations.models import Facility
from apps.patients.models import Patient

from .forms import DemoForm


def home(request):
    try:
        patient_count = Patient.objects.count()
        facility_count = Facility.objects.count()
        case_count = CareSupportCase.objects.count()
        programme_count = FundingProgramme.objects.count()
        total_authorized = (
            AssistanceAuthorization.objects.aggregate(total=Sum("authorized_amount"))["total"]
            or Decimal("0.00")
        )
    except Exception:
        patient_count = 0
        facility_count = 0
        case_count = 0
        programme_count = 0
        total_authorized = Decimal("0.00")

    context = {
        "platform_name": "NCD Patient Safety Platform",
        "tagline": "Standards-Based Noncommunicable Disease Care Coordination & Financial Assistance",
        "patient_count": patient_count,
        "facility_count": facility_count,
        "case_count": case_count,
        "programme_count": programme_count,
        "total_authorized": total_authorized,
    }

    return render(request, "home.html", context)


def case_demo(request, case_id):
    context = {
        "case_id": case_id,
    }

    return render(request, "case_demo.html", context)


def demo_form(request):
    form = DemoForm()

    context = {
        "form": form,
    }

    return render(request, "demo_form.html", context)
