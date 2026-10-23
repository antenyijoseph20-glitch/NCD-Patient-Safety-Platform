from datetime import date
import uuid

from django.contrib.auth import get_user_model
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from apps.organizations.models import Facility, HealthcareProfessional, Organization
from apps.patients.models import Patient
from .models import ClinicalNeed, ClinicalVerification


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
