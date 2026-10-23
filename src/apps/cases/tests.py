from datetime import date
import uuid

from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from apps.clinical_need.models import ClinicalNeed
from apps.patients.models import Patient
from .models import CareSupportCase


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
