from datetime import date
import uuid

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from apps.clinical_need.models import ClinicalNeed
from apps.patients.models import Patient
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
