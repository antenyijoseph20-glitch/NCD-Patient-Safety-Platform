"""
HL7 FHIR Release 4 (R4) Resource Serializers for NCD Patient Safety Platform.
Converts internal relational and domain models into standardized FHIR resources:
- Patient
- Condition (ClinicalNeed)
- CarePlan (CareSupportCase)
- DiagnosticReport (ClinicalEvidence)
- AdverseEvent (SafetyEvent)
- Coverage (AssistanceAuthorization)
- Claim (PaymentInstruction)
"""

from typing import Any, Dict, List

from apps.cases.models import CareSupportCase
from apps.clinical_need.models import ClinicalEvidence, ClinicalNeed
from apps.funding.models import AssistanceAuthorization
from apps.patients.models import Patient
from apps.payments.models import PaymentInstruction
from apps.safety.models import SafetyEvent


def serialize_fhir_patient(patient: Patient) -> Dict[str, Any]:
    """Serializes Patient to HL7 FHIR R4 Patient resource."""
    identifiers: List[Dict[str, Any]] = []
    for ext in patient.external_identifiers.all():
        system_uri = "urn:oid:2.16.566.1" if ext.system == "NIN" else f"urn:system:{ext.system.lower()}"
        identifiers.append(
            {
                "system": system_uri,
                "value": ext.value,
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "NN" if ext.system == "NIN" else "MR",
                            "display": ext.get_identifier_type_display(),
                        }
                    ]
                },
            }
        )

    telecom = []
    if patient.primary_phone:
        telecom.append({"system": "phone", "value": patient.primary_phone, "use": "mobile"})
    if patient.email:
        telecom.append({"system": "email", "value": patient.email, "use": "home"})

    contacts = []
    for c in patient.contacts.all():
        contacts.append(
            {
                "relationship": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0131",
                                "display": c.get_contact_type_display(),
                            }
                        ]
                    }
                ],
                "telecom": [{"system": "phone" if "@" not in c.value else "email", "value": c.value}],
            }
        )

    gender_map = {
        Patient.Gender.MALE: "male",
        Patient.Gender.FEMALE: "female",
        Patient.Gender.OTHER: "other",
    }

    return {
        "resourceType": "Patient",
        "id": str(patient.public_id),
        "meta": {
            "versionId": "1",
            "lastUpdated": patient.updated_at.isoformat(),
            "profile": ["http://hl7.org/fhir/StructureDefinition/Patient"],
        },
        "identifier": identifiers,
        "active": patient.status == Patient.Status.ACTIVE,
        "name": [
            {
                "use": "official",
                "family": patient.last_name,
                "given": [n for n in [patient.first_name, patient.other_names] if n],
                "text": patient.full_name,
            }
        ],
        "telecom": telecom,
        "gender": gender_map.get(patient.gender, "unknown"),
        "birthDate": patient.date_of_birth.isoformat(),
        "address": [{"text": patient.address, "country": "NGA"} if patient.address else {"country": "NGA"}],
        "contact": contacts,
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-bloodGroup",
                "valueString": patient.blood_group,
            },
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-genotype",
                "valueString": patient.genotype,
            },
        ],
    }


def serialize_fhir_condition(need: ClinicalNeed) -> Dict[str, Any]:
    """Serializes ClinicalNeed to HL7 FHIR R4 Condition resource."""
    clin_status = "active" if need.status in [ClinicalNeed.Status.IDENTIFIED, ClinicalNeed.Status.VERIFIED] else "resolved"
    ver_status = "confirmed" if need.status == ClinicalNeed.Status.VERIFIED else "provisional"

    coding = []
    if need.icd10_code:
        coding.append(
            {
                "system": "http://hl7.org/fhir/sid/icd-10",
                "code": need.icd10_code,
                "display": need.condition_name,
            }
        )
    # Add SNOMED CT generic concept for chronic disease
    coding.append(
        {
            "system": "http://snomed.info/sct",
            "code": "417335005",
            "display": "Chronic noncommunicable disease",
        }
    )

    verifications = []
    for ver in need.verifications.filter(status="VERIFIED"):
        verifications.append(
            {
                "display": f"Verified by {ver.professional} at {ver.facility}",
                "extension": [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/verificationDate",
                        "valueDateTime": ver.verified_at.isoformat() if ver.verified_at else "",
                    }
                ],
            }
        )

    return {
        "resourceType": "Condition",
        "id": str(need.public_id),
        "meta": {
            "profile": ["http://hl7.org/fhir/StructureDefinition/Condition"],
            "lastUpdated": need.updated_at.isoformat(),
        },
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": clin_status,
                }
            ]
        },
        "verificationStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": ver_status,
                }
            ]
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                        "code": "encounter-diagnosis",
                        "display": "Encounter Diagnosis",
                    }
                ]
            }
        ],
        "severity": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "24484000",
                    "display": need.get_severity_display(),
                }
            ],
            "text": need.get_severity_display(),
        },
        "code": {
            "coding": coding,
            "text": need.condition_name,
        },
        "subject": {
            "reference": f"Patient/{need.patient.public_id}",
            "display": need.patient.full_name,
        },
        "recordedDate": need.created_at.isoformat(),
        "onsetDateTime": need.diagnosed_date.isoformat() if need.diagnosed_date else None,
        "note": [{"text": need.clinical_summary}],
        "evidence": verifications,
    }


def serialize_fhir_careplan(case: CareSupportCase) -> Dict[str, Any]:
    """Serializes CareSupportCase to HL7 FHIR R4 CarePlan resource."""
    status_map = {
        CareSupportCase.Status.OPEN: "draft",
        CareSupportCase.Status.CLINICAL_REVIEW: "active",
        CareSupportCase.Status.FUNDING_ELIGIBLE: "active",
        CareSupportCase.Status.ASSISTANCE_ACTIVE: "active",
        CareSupportCase.Status.CLOSED: "completed",
        CareSupportCase.Status.CANCELLED: "revoked",
    }

    activities = []
    if case.primary_clinical_need:
        activities.append(
            {
                "detail": {
                    "kind": "ServiceRequest",
                    "code": {
                        "text": f"Treatment protocol for {case.primary_clinical_need.condition_name}",
                    },
                    "status": "in-progress",
                    "description": case.description or "Comprehensive clinical care and medical assistance.",
                }
            }
        )

    contributors = [
        {"display": f"{asgn.get_role_display()}: {asgn.assigned_to.get_full_name() or asgn.assigned_to.username}"}
        for asgn in case.assignments.filter(is_active=True)
    ]

    return {
        "resourceType": "CarePlan",
        "id": str(case.public_id),
        "meta": {
            "profile": ["http://hl7.org/fhir/StructureDefinition/CarePlan"],
            "lastUpdated": case.updated_at.isoformat(),
        },
        "identifier": [
            {
                "system": "http://ncd-platform.health.gov.ng/cases",
                "value": case.case_number,
            }
        ],
        "status": status_map.get(case.status, "active"),
        "intent": "plan",
        "title": case.title,
        "description": case.description,
        "subject": {
            "reference": f"Patient/{case.patient.public_id}",
            "display": case.patient.full_name,
        },
        "period": {
            "start": case.opened_at.isoformat(),
            "end": case.closed_at.isoformat() if case.closed_at else None,
        },
        "contributor": contributors,
        "activity": activities,
    }


def serialize_fhir_diagnostic_report(evidence: ClinicalEvidence) -> Dict[str, Any]:
    """Serializes ClinicalEvidence to HL7 FHIR R4 DiagnosticReport resource."""
    return {
        "resourceType": "DiagnosticReport",
        "id": str(evidence.public_id),
        "meta": {
            "profile": ["http://hl7.org/fhir/StructureDefinition/DiagnosticReport"],
            "lastUpdated": evidence.created_at.isoformat(),
        },
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                        "code": "LAB" if "REPORT" in evidence.evidence_type else "RAD",
                        "display": evidence.get_evidence_type_display(),
                    }
                ]
            }
        ],
        "code": {
            "text": evidence.title,
        },
        "subject": {
            "reference": f"Patient/{evidence.clinical_need.patient.public_id}",
            "display": evidence.clinical_need.patient.full_name,
        },
        "effectiveDateTime": evidence.issued_date.isoformat() if evidence.issued_date else evidence.created_at.isoformat(),
        "issued": evidence.created_at.isoformat(),
        "performer": [{"display": evidence.issued_by or "Accredited Health Unit"}],
        "presentedForm": [
            {
                "contentType": "application/pdf",
                "url": evidence.document_reference or "https://evidence-vault.health.gov.ng/records/",
                "hash": evidence.sha256_checksum,
                "title": evidence.title,
            }
        ],
    }


def serialize_fhir_adverse_event(event: SafetyEvent) -> Dict[str, Any]:
    """Serializes SafetyEvent to HL7 FHIR R4 AdverseEvent resource."""
    severity_code = {
        SafetyEvent.Severity.NEAR_MISS: "mild",
        SafetyEvent.Severity.MILD_HARM: "mild",
        SafetyEvent.Severity.MODERATE_HARM: "moderate",
        SafetyEvent.Severity.SEVERE_HARM: "severe",
        SafetyEvent.Severity.CRITICAL: "severe",
    }

    return {
        "resourceType": "AdverseEvent",
        "id": str(event.public_id),
        "meta": {
            "profile": ["http://hl7.org/fhir/StructureDefinition/AdverseEvent"],
        },
        "identifier": {
            "system": "http://ncd-platform.health.gov.ng/safety",
            "value": event.reference_code,
        },
        "actuality": "actual" if event.severity != SafetyEvent.Severity.NEAR_MISS else "potential",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/adverse-event-category",
                        "code": "medical-device" if "allergic" in event.event_description.lower() else "procedure-problem",
                        "display": "Patient Safety Incident",
                    }
                ]
            }
        ],
        "event": {
            "text": event.event_description,
        },
        "subject": {
            "reference": f"Patient/{event.patient.public_id}",
            "display": event.patient.full_name,
        },
        "date": event.occurred_at.isoformat(),
        "severity": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/adverse-event-severity",
                    "code": severity_code.get(event.severity, "moderate"),
                    "display": event.get_severity_display(),
                }
            ]
        },
        "recorder": {
            "display": event.reported_by.get_full_name() or event.reported_by.username,
        },
        "location": {
            "display": event.facility.name if event.facility else "Unspecified Accredited Facility",
        },
    }


def serialize_fhir_coverage(auth: AssistanceAuthorization) -> Dict[str, Any]:
    """Serializes AssistanceAuthorization to HL7 FHIR R4 Coverage resource."""
    return {
        "resourceType": "Coverage",
        "id": str(auth.public_id),
        "identifier": [
            {
                "system": "http://ncd-platform.health.gov.ng/authorizations",
                "value": auth.authorization_code,
            }
        ],
        "status": "active" if auth.status == "ACTIVE" else "cancelled",
        "type": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    "code": "PUBLICPOL",
                    "display": "Public healthcare assistance envelope",
                }
            ]
        },
        "beneficiary": {
            "reference": f"Patient/{auth.case.patient.public_id}",
            "display": auth.case.patient.full_name,
        },
        "period": {
            "start": auth.valid_from.isoformat(),
            "end": auth.valid_to.isoformat(),
        },
        "payor": [
            {
                "display": auth.decision.application.programme.name if auth.decision and auth.decision.application.programme else "National Assistance Programme",
            }
        ],
        "costToBeneficiary": [
            {
                "valueMoney": {
                    "value": float(auth.remaining_balance),
                    "currency": auth.currency_code,
                }
            }
        ],
    }


def serialize_fhir_claim(inst: PaymentInstruction) -> Dict[str, Any]:
    """Serializes PaymentInstruction to HL7 FHIR R4 Claim resource."""
    return {
        "resourceType": "Claim",
        "id": str(inst.public_id),
        "identifier": [
            {
                "system": "http://ncd-platform.health.gov.ng/payment-instructions",
                "value": inst.instruction_reference,
            }
        ],
        "status": "active",
        "type": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                    "code": "institutional",
                    "display": "Institutional Provider Settlement",
                }
            ]
        },
        "use": "claim",
        "patient": {
            "reference": f"Patient/{inst.authorization.case.patient.public_id}",
            "display": inst.authorization.case.patient.full_name,
        },
        "created": inst.created_at.isoformat(),
        "provider": {
            "display": inst.payee_name,
        },
        "total": {
            "value": float(inst.amount),
            "currency": inst.currency_code,
        },
    }
