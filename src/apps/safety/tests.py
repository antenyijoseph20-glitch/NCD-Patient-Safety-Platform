from datetime import date
import uuid

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from apps.cases.models import CareSupportCase
from apps.patients.models import Patient
from .models import SafetyEvent


class SafetyEventModelTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(
            first_name="Kalu",
            last_name="Umeh",
            date_of_birth=date(1968, 12, 1),
            gender=Patient.Gender.MALE,
        )
        self.case = CareSupportCase.objects.create(
            case_number="CASE-2026-0099",
            patient=self.patient,
            title="Chemotherapy Co-Management",
        )
        self.reporter = get_user_model().objects.create_user(
            username="safety_officer_kalu",
            email="safety@example.org",
            password="test-password-123",
        )

    def test_safety_event_creation(self):
        event = SafetyEvent.objects.create(
            reference_code="SAFE-2026-0001",
            patient=self.patient,
            case=self.case,
            reported_by=self.reporter,
            severity=SafetyEvent.Severity.SEVERE_HARM,
            event_description="Incorrect dosage calculation for chemotherapy infusion detected before administration.",
            immediate_action_taken="Infusion stopped, oncologist notified, dosage re-calculated and verified.",
            occurred_at=timezone.now(),
        )

        self.assertEqual(event.status, SafetyEvent.Status.REPORTED)
        self.assertEqual(event.severity, SafetyEvent.Severity.SEVERE_HARM)
        self.assertEqual(event.patient, self.patient)
        self.assertEqual(event.case, self.case)
        self.assertIsNotNone(event.public_id)
        self.assertIsInstance(event.public_id, uuid.UUID)

    def test_safety_event_unique_reference(self):
        SafetyEvent.objects.create(
            reference_code="SAFE-2026-0001",
            patient=self.patient,
            reported_by=self.reporter,
            event_description="Adverse drug reaction.",
            occurred_at=timezone.now(),
        )

        with self.assertRaises(IntegrityError):
            SafetyEvent.objects.create(
                reference_code="SAFE-2026-0001",
                patient=self.patient,
                reported_by=self.reporter,
                event_description="Duplicate reference event.",
                occurred_at=timezone.now(),
            )

    def test_safety_event_protects_patient_deletion(self):
        SafetyEvent.objects.create(
            reference_code="SAFE-2026-0002",
            patient=self.patient,
            reported_by=self.reporter,
            event_description="Slip and fall in clinic corridor.",
            occurred_at=timezone.now(),
        )

        with self.assertRaises(ProtectedError):
            self.patient.delete()

    def test_safety_event_case_deletion_sets_null(self):
        event = SafetyEvent.objects.create(
            reference_code="SAFE-2026-0003",
            patient=self.patient,
            case=self.case,
            reported_by=self.reporter,
            event_description="Case linked incident.",
            occurred_at=timezone.now(),
        )
        self.assertEqual(event.case, self.case)

        self.case.delete()
        event.refresh_from_db()
        self.assertIsNone(event.case)
