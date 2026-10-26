import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from apps.clinical_need.models import (
    ClinicalEvidence,
    ClinicalNeed,
    ClinicalVerification,
)
from apps.organizations.models import Facility, HealthcareProfessional, Organization
from apps.patients.models import (
    CaregiverRelationship,
    ExternalIdentifier,
    Patient,
    PatientContact,
)
from apps.safety.models import SafetyEvent

from .models import CareSupportCase, CaseAssignment


class CareSupportCaseModelTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(
            first_name="Zainab",
            last_name="Mohammed",
            date_of_birth=date(1998, 2, 17),
            gender=Patient.Gender.FEMALE,
        )
        self.clinical_need = ClinicalNeed.objects.create(
            patient=self.patient,
            condition_name="Type 1 Diabetes Mellitus",
            clinical_summary="Insulin pump therapy and ongoing monitoring.",
        )

    def test_care_case_creation(self):
        case = CareSupportCase.objects.create(
            case_number="CASE-2026-0001",
            patient=self.patient,
            primary_clinical_need=self.clinical_need,
            title="Comprehensive Diabetes Management Plan",
            priority=CareSupportCase.Priority.HIGH,
        )

        self.assertEqual(case.status, CareSupportCase.Status.OPEN)
        self.assertEqual(case.priority, CareSupportCase.Priority.HIGH)
        self.assertEqual(case.patient, self.patient)
        self.assertEqual(case.primary_clinical_need, self.clinical_need)
        self.assertIsNotNone(case.public_id)
        self.assertIsInstance(case.public_id, uuid.UUID)

    def test_care_case_unique_number(self):
        CareSupportCase.objects.create(
            case_number="CASE-2026-0001",
            patient=self.patient,
            title="First Case",
        )

        with self.assertRaises(IntegrityError):
            CareSupportCase.objects.create(
                case_number="CASE-2026-0001",
                patient=self.patient,
                title="Duplicate Case",
            )

    def test_care_case_protects_patient_from_deletion(self):
        CareSupportCase.objects.create(
            case_number="CASE-2026-0002",
            patient=self.patient,
            title="Patient Protection Test",
        )

        with self.assertRaises(ProtectedError):
            self.patient.delete()

    def test_care_case_protects_clinical_need_from_deletion(self):
        CareSupportCase.objects.create(
            case_number="CASE-2026-0003",
            patient=self.patient,
            primary_clinical_need=self.clinical_need,
            title="Clinical Need Protection Test",
        )

        with self.assertRaises(ProtectedError):
            self.clinical_need.delete()


class CaseAssignmentModelTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(
            first_name="Haruna",
            last_name="Danladi",
            date_of_birth=date(1988, 9, 9),
            gender=Patient.Gender.MALE,
        )
        self.case = CareSupportCase.objects.create(
            case_number="CASE-2026-0010",
            patient=self.patient,
            title="Cardiovascular Monitoring Support",
        )
        self.staff_user = get_user_model().objects.create_user(
            username="officer_danladi",
            email="officer@example.org",
            password="test-password-123",
        )

    def test_case_assignment_creation(self):
        assignment = CaseAssignment.objects.create(
            case=self.case,
            assigned_to=self.staff_user,
            role=CaseAssignment.Role.CASE_OFFICER,
            notes="Assigned as primary liaison.",
        )

        self.assertEqual(assignment.case, self.case)
        self.assertEqual(assignment.assigned_to, self.staff_user)
        self.assertTrue(assignment.is_active)
        self.assertIsNotNone(assignment.public_id)

    def test_case_assignment_protects_assigned_user_deletion(self):
        CaseAssignment.objects.create(
            case=self.case,
            assigned_to=self.staff_user,
            role=CaseAssignment.Role.CASE_OFFICER,
        )

        with self.assertRaises(ProtectedError):
            self.staff_user.delete()

    def test_case_deletion_cascades_to_assignments(self):
        CaseAssignment.objects.create(
            case=self.case,
            assigned_to=self.staff_user,
            role=CaseAssignment.Role.CASE_OFFICER,
        )
        self.assertEqual(CaseAssignment.objects.count(), 1)

        self.case.delete()
        self.assertEqual(CaseAssignment.objects.count(), 0)


class IntegrationWorkflowTests(TestCase):
    def test_end_to_end_patient_care_case_workflow(self):
        # 1. Patient Onboarding
        patient = Patient.objects.create(
            first_name="Folashade",
            last_name="Olatunji",
            date_of_birth=date(1982, 10, 14),
            gender=Patient.Gender.FEMALE,
            blood_group=Patient.BloodGroup.O_POSITIVE,
            genotype=Patient.Genotype.AA,
            primary_phone="+2348033334444",
            email="folashade@example.org",
        )
        self.assertIsNotNone(patient.public_id)

        # 2. National & External Health Identifiers
        ExternalIdentifier.objects.create(
            patient=patient,
            system="NIN",
            value="98765432100",
            identifier_type=ExternalIdentifier.IdentifierType.NATIONAL_ID,
            issuing_authority="NIMC",
            verification_status=ExternalIdentifier.VerificationStatus.VERIFIED,
        )
        PatientContact.objects.create(
            patient=patient,
            contact_type=PatientContact.ContactType.PHONE,
            value="+2348033334444",
            is_primary=True,
        )

        # 3. Caregiver Delegation
        caregiver_user = get_user_model().objects.create_user(
            username="caregiver_olatunji",
            email="caregiver_olatunji@example.org",
            password="test-password-123",
        )
        caregiver_rel = CaregiverRelationship.objects.create(
            patient=patient,
            user=caregiver_user,
            relationship_type=CaregiverRelationship.RelationshipType.SPOUSE,
            status=CaregiverRelationship.Status.ACTIVE,
            can_manage_care=True,
            can_apply_funding=True,
        )
        self.assertEqual(caregiver_rel.patient, patient)

        # 4. Clinical Need Recording
        need = ClinicalNeed.objects.create(
            patient=patient,
            condition_name="Breast Cancer (Stage IIA)",
            icd10_code="C50.9",
            severity=ClinicalNeed.Severity.SEVERE,
            clinical_summary="Invasive ductal carcinoma, hormone receptor positive.",
        )

        # 5. Clinical Evidence Attachment
        evidence = ClinicalEvidence.objects.create(
            clinical_need=need,
            evidence_type=ClinicalEvidence.EvidenceType.PATHOLOGY_REPORT,
            title="Core Needle Biopsy Histopathology",
            document_reference="s3://ncd-evidence/olatunji/biopsy_2026.pdf",
            sha256_checksum="abcd1234abcd5678abcd1234abcd5678abcd1234abcd5678abcd1234abcd5678",
            issued_by="University College Hospital Ibadan",
            issued_date=date(2026, 8, 1),
        )
        self.assertEqual(evidence.clinical_need, need)

        # 6. Clinical Verification by Qualified Professional
        org = Organization.objects.create(
            name="UCH Ibadan",
            organization_type=Organization.OrganizationType.HEALTHCARE_PROVIDER,
        )
        facility = Facility.objects.create(
            organization=org,
            name="Oncology Department",
            facility_type=Facility.FacilityType.SPECIALIST_CENTRE,
        )
        doctor_user = get_user_model().objects.create_user(
            username="dr_onco_kola",
            email="dr.kola@example.org",
            password="test-password-123",
        )
        doctor = HealthcareProfessional.objects.create(
            user=doctor_user,
            profession=HealthcareProfessional.Profession.DOCTOR,
            license_number="MDCN-778899",
            license_status=HealthcareProfessional.LicenseStatus.VERIFIED,
        )
        verification = ClinicalVerification.objects.create(
            clinical_need=need,
            professional=doctor,
            facility=facility,
            status=ClinicalVerification.Status.VERIFIED,
            verification_notes="Histopathology confirmed. Recommended for systemic chemotherapy & surgery.",
            verified_at=timezone.now(),
        )
        self.assertEqual(verification.status, ClinicalVerification.Status.VERIFIED)

        # 7. Care Support Case Creation
        case = CareSupportCase.objects.create(
            case_number="CASE-2026-0500",
            patient=patient,
            primary_clinical_need=need,
            title="Multidisciplinary Oncology Care Plan",
            priority=CareSupportCase.Priority.HIGH,
            status=CareSupportCase.Status.FUNDING_ELIGIBLE,
        )
        self.assertEqual(case.status, CareSupportCase.Status.FUNDING_ELIGIBLE)

        # 8. Staff Assignment
        staff_user = get_user_model().objects.create_user(
            username="case_officer_ada",
            email="ada@example.org",
            password="test-password-123",
        )
        assignment = CaseAssignment.objects.create(
            case=case,
            assigned_to=staff_user,
            role=CaseAssignment.Role.CASE_OFFICER,
        )
        self.assertEqual(assignment.assigned_to, staff_user)

        # 9. Safety Incident Reporting
        safety_event = SafetyEvent.objects.create(
            reference_code="SAFE-2026-0500",
            patient=patient,
            case=case,
            reported_by=staff_user,
            facility=facility,
            severity=SafetyEvent.Severity.MILD_HARM,
            event_description="Delayed lab turnaround for pre-chemo blood counts.",
            occurred_at=timezone.now(),
        )
        self.assertEqual(safety_event.case, case)
        self.assertEqual(safety_event.patient, patient)
