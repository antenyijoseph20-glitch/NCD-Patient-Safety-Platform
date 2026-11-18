import uuid
from typing import Any, Dict, List

from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from apps.cases.models import CareSupportCase
from apps.clinical_need.models import ClinicalEvidence, ClinicalNeed
from apps.funding.models import AssistanceAuthorization
from apps.patients.models import Patient
from apps.payments.models import PaymentInstruction
from apps.safety.models import SafetyEvent

from .fhir_serializers import (
    serialize_fhir_adverse_event,
    serialize_fhir_careplan,
    serialize_fhir_claim,
    serialize_fhir_condition,
    serialize_fhir_coverage,
    serialize_fhir_diagnostic_report,
    serialize_fhir_patient,
)


def _make_fhir_bundle(resource_type: str, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Wraps FHIR resource results in a standard FHIR R4 Bundle."""
    return {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "type": "searchset",
        "total": len(entries),
        "entry": [{"fullUrl": f"urn:uuid:{e.get('id')}", "resource": e} for e in entries],
    }


@require_GET
def fhir_metadata(request):
    """
    HL7 FHIR R4 CapabilityStatement declaring conformance, supported resources,
    and server interoperability profile.
    """
    capability = {
        "resourceType": "CapabilityStatement",
        "id": "ncd-platform-fhir-gateway",
        "status": "active",
        "date": "2026-11-18",
        "publisher": "Federal Ministry of Health / NCD Patient Safety Platform",
        "kind": "instance",
        "software": {
            "name": "NCD Patient Safety Platform - FHIR Interoperability Gateway",
            "version": "1.0.0",
        },
        "implementation": {
            "description": "National Digital Health Architecture (NDHA) Interoperability Adaptor",
            "url": "http://localhost:8000/api/fhir/",
        },
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [
            {
                "mode": "server",
                "security": {
                    "cors": True,
                    "service": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/restful-security-service",
                                    "code": "SMART-on-FHIR",
                                    "display": "SMART-on-FHIR",
                                }
                            ],
                            "text": "OAuth2 using SMART-on-FHIR profile (RFC 6749)",
                        }
                    ],
                    "extension": [
                        {
                            "url": "http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris",
                            "extension": [
                                {
                                    "url": "token",
                                    "valueUri": request.build_absolute_uri("/api/v1/token/"),
                                },
                                {
                                    "url": "authorize",
                                    "valueUri": request.build_absolute_uri("/api/v1/authorize/"),
                                },
                                {
                                    "url": "register",
                                    "valueUri": request.build_absolute_uri("/api/v1/register/"),
                                },
                                {
                                    "url": "introspect",
                                    "valueUri": request.build_absolute_uri("/api/v1/token/introspect/"),
                                },
                            ],
                        }
                    ],
                    "description": "Standard SMART on FHIR OAuth2 conformance profile for secure hospital EMR connectivity.",
                },
                "resource": [
                    {
                        "type": "Patient",
                        "interaction": [{"code": "read"}, {"code": "search-type"}],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "name", "type": "string"},
                            {"name": "identifier", "type": "token"},
                        ],
                    },
                    {
                        "type": "Condition",
                        "interaction": [{"code": "read"}, {"code": "search-type"}],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "patient", "type": "reference"},
                            {"name": "code", "type": "token"},
                        ],
                    },
                    {
                        "type": "CarePlan",
                        "interaction": [{"code": "read"}, {"code": "search-type"}],
                        "searchParam": [{"name": "patient", "type": "reference"}],
                    },
                    {
                        "type": "DiagnosticReport",
                        "interaction": [{"code": "read"}, {"code": "search-type"}],
                    },
                    {
                        "type": "AdverseEvent",
                        "interaction": [{"code": "read"}, {"code": "search-type"}],
                    },
                    {
                        "type": "Coverage",
                        "interaction": [{"code": "read"}, {"code": "search-type"}],
                    },
                    {
                        "type": "Claim",
                        "interaction": [{"code": "read"}, {"code": "search-type"}],
                    },
                ],
            }
        ],
    }
    return JsonResponse(capability, json_dumps_params={"indent": 2})


@require_GET
def fhir_patients(request, public_id=None):
    if public_id:
        patient = get_object_or_404(Patient, public_id=public_id)
        return JsonResponse(serialize_fhir_patient(patient), json_dumps_params={"indent": 2})

    patients = Patient.objects.all().prefetch_related("external_identifiers", "contacts")
    entries = [serialize_fhir_patient(p) for p in patients]
    return JsonResponse(_make_fhir_bundle("Patient", entries), json_dumps_params={"indent": 2})


@require_GET
def fhir_conditions(request, public_id=None):
    if public_id:
        need = get_object_or_404(ClinicalNeed, public_id=public_id)
        return JsonResponse(serialize_fhir_condition(need), json_dumps_params={"indent": 2})

    needs = ClinicalNeed.objects.all().select_related("patient").prefetch_related("verifications")
    entries = [serialize_fhir_condition(n) for n in needs]
    return JsonResponse(_make_fhir_bundle("Condition", entries), json_dumps_params={"indent": 2})


@require_GET
def fhir_careplans(request, public_id=None):
    if public_id:
        case = get_object_or_404(CareSupportCase, public_id=public_id)
        return JsonResponse(serialize_fhir_careplan(case), json_dumps_params={"indent": 2})

    cases = CareSupportCase.objects.all().select_related("patient", "primary_clinical_need").prefetch_related("assignments")
    entries = [serialize_fhir_careplan(c) for c in cases]
    return JsonResponse(_make_fhir_bundle("CarePlan", entries), json_dumps_params={"indent": 2})


@require_GET
def fhir_diagnostic_reports(request, public_id=None):
    if public_id:
        evidence = get_object_or_404(ClinicalEvidence, public_id=public_id)
        return JsonResponse(serialize_fhir_diagnostic_report(evidence), json_dumps_params={"indent": 2})

    records = ClinicalEvidence.objects.all().select_related("clinical_need__patient")
    entries = [serialize_fhir_diagnostic_report(r) for r in records]
    return JsonResponse(_make_fhir_bundle("DiagnosticReport", entries), json_dumps_params={"indent": 2})


@require_GET
def fhir_adverse_events(request, public_id=None):
    if public_id:
        event = get_object_or_404(SafetyEvent, public_id=public_id)
        return JsonResponse(serialize_fhir_adverse_event(event), json_dumps_params={"indent": 2})

    events = SafetyEvent.objects.all().select_related("patient", "reported_by", "facility")
    entries = [serialize_fhir_adverse_event(e) for e in events]
    return JsonResponse(_make_fhir_bundle("AdverseEvent", entries), json_dumps_params={"indent": 2})


@require_GET
def fhir_coverages(request, public_id=None):
    if public_id:
        auth = get_object_or_404(AssistanceAuthorization, public_id=public_id)
        return JsonResponse(serialize_fhir_coverage(auth), json_dumps_params={"indent": 2})

    auths = AssistanceAuthorization.objects.all().select_related("case__patient", "decision__application__programme")
    entries = [serialize_fhir_coverage(a) for a in auths]
    return JsonResponse(_make_fhir_bundle("Coverage", entries), json_dumps_params={"indent": 2})


@require_GET
def fhir_claims(request, public_id=None):
    if public_id:
        inst = get_object_or_404(PaymentInstruction, public_id=public_id)
        return JsonResponse(serialize_fhir_claim(inst), json_dumps_params={"indent": 2})

    instructions = PaymentInstruction.objects.all().select_related("authorization__case__patient")
    entries = [serialize_fhir_claim(i) for i in instructions]
    return JsonResponse(_make_fhir_bundle("Claim", entries), json_dumps_params={"indent": 2})
