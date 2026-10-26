import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from apps.organizations.models import Facility, HealthcareProfessional, Organization
from apps.patients.models import Patient

from .models import ClinicalEvidence, ClinicalNeed, ClinicalVerification


class ClinicalNeedModelTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(
            first_name="Amina",
            last_name="Bello",
            date_of_birth=date(1992, 1, 10),
            gender=Patient.Gender.FEMALE,
        )

    def test_clinical_need_creation_with_defaults(self):
        need = ClinicalNeed.objects.create(
            patient=self.patient,
            condition_name="Type 2 Diabetes Mellitus",
            icd10_code="E11",
            clinical_summary="Patient diagnosed with elevated HbA1c requiring insulin and care management.",
        )

        self.assertEqual(need.status, ClinicalNeed.Status.IDENTIFIED)
        self.assertEqual(need.severity, ClinicalNeed.Severity.MODERATE)
        self.assertIsNotNone(need.public_id)
        self.assertIsInstance(need.public_id, uuid.UUID)

    def test_clinical_need_protects_patient_from_deletion(self):
        ClinicalNeed.objects.create(
            patient=self.patient,
            condition_name="Hypertension Stage 2",
            clinical_summary="Blood pressure consistently above 160/100.",
        )

        with self.assertRaises(ProtectedError):
            self.patient.delete()


class ClinicalVerificationModelTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(
            first_name="Ibrahim",
            last_name="Garba",
            date_of_birth=date(1975, 5, 14),
            gender=Patient.Gender.MALE,
        )
        self.clinical_need = ClinicalNeed.objects.create(
            patient=self.patient,
            condition_name="Chronic Kidney Disease",
            clinical_summary="Stage 3 CKD requiring regular nephrology checkups.",
        )
        self.org = Organization.objects.create(
            name="National Hospital Abuja",
            organization_type=Organization.OrganizationType.HEALTHCARE_PROVIDER,
        )
        self.facility = Facility.objects.create(
            organization=self.org,
            name="Main Nephrology Unit",
            facility_type=Facility.FacilityType.HOSPITAL,
        )
        self.doctor_user = get_user_model().objects.create_user(
            username="dr_adamu",
            first_name="Adamu",
            last_name="Aliyu",
            email="adamu.aliyu@example.org",
            password="test-password-123",
        )
        self.doctor = HealthcareProfessional.objects.create(
            user=self.doctor_user,
            profession=HealthcareProfessional.Profession.DOCTOR,
            license_number="MDCN-998877",
            license_status=HealthcareProfessional.LicenseStatus.VERIFIED,
        )

    def test_clinical_verification_creation(self):
        verification = ClinicalVerification.objects.create(
            clinical_need=self.clinical_need,
            professional=self.doctor,
            facility=self.facility,
            status=ClinicalVerification.Status.VERIFIED,
            verification_notes="Confirmed via eGFR results and ultrasound.",
        )

        self.assertEqual(verification.status, ClinicalVerification.Status.VERIFIED)
        self.assertEqual(verification.professional, self.doctor)
        self.assertEqual(verification.facility, self.facility)
        self.assertIsNotNone(verification.public_id)

    def test_clinical_verification_protects_professional_deletion(self):
        ClinicalVerification.objects.create(
            clinical_need=self.clinical_need,
            professional=self.doctor,
            verification_notes="Verified.",
        )

        with self.assertRaises(ProtectedError):
            self.doctor.delete()

    def test_clinical_verification_protects_clinical_need_deletion(self):
        ClinicalVerification.objects.create(
            clinical_need=self.clinical_need,
            professional=self.doctor,
            verification_notes="Verified.",
        )

        with self.assertRaises(ProtectedError):
            self.clinical_need.delete()


class ClinicalEvidenceModelTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(
            first_name="Fatima",
            last_name="Yusuf",
            date_of_birth=date(1995, 7, 30),
            gender=Patient.Gender.FEMALE,
        )
        self.clinical_need = ClinicalNeed.objects.create(
            patient=self.patient,
            condition_name="Sickle Cell Anemia (HbSS)",
            clinical_summary="Vaso-occlusive crises management and hydroxyurea therapy.",
        )

    def test_clinical_evidence_creation(self):
        evidence = ClinicalEvidence.objects.create(
            clinical_need=self.clinical_need,
            evidence_type=ClinicalEvidence.EvidenceType.LABORATORY_REPORT,
            title="Hemoglobin Electrophoresis Report",
            document_reference="s3://ncd-evidence/patient-10/hbss_electrophoresis.pdf",
            sha256_checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            issued_by="Lagos University Teaching Hospital Lab",
            issued_date=date(2026, 6, 12),
        )

        self.assertEqual(evidence.clinical_need, self.clinical_need)
        self.assertEqual(evidence.evidence_type, ClinicalEvidence.EvidenceType.LABORATORY_REPORT)
        self.assertIsNotNone(evidence.public_id)

    def test_clinical_evidence_protects_clinical_need_deletion(self):
        ClinicalEvidence.objects.create(
            clinical_need=self.clinical_need,
            evidence_type=ClinicalEvidence.EvidenceType.PRESCRIPTION,
            title="Hydroxyurea Prescription",
        )

        with self.assertRaises(ProtectedError):
            self.clinical_need.delete()
