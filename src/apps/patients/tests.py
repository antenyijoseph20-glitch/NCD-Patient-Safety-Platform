from datetime import date
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Patient


class PatientModelTests(TestCase):
    def setUp(self):
        self.patient_data = {
            "first_name": "Ngozi",
            "last_name": "Eze",
            "other_names": "Ada",
            "date_of_birth": date(1985, 4, 12),
            "gender": Patient.Gender.FEMALE,
            "primary_phone": "+2348012345678",
            "email": "ngozi.eze@example.org",
        }

    def test_patient_creation_with_defaults(self):
        patient = Patient.objects.create(**self.patient_data)

        self.assertEqual(patient.status, Patient.Status.PENDING_VERIFICATION)
        self.assertEqual(patient.blood_group, Patient.BloodGroup.UNKNOWN)
        self.assertEqual(patient.genotype, Patient.Genotype.UNKNOWN)
        self.assertEqual(str(patient), "Ngozi Eze")

    def test_patient_gets_public_id(self):
        patient = Patient.objects.create(**self.patient_data)

        self.assertIsNotNone(patient.public_id)
        self.assertIsInstance(patient.public_id, uuid.UUID)

    def test_patient_full_name_property(self):
        patient = Patient.objects.create(**self.patient_data)
        self.assertEqual(patient.full_name, "Ngozi Ada Eze")

        patient.other_names = ""
        self.assertEqual(patient.full_name, "Ngozi Eze")

    def test_patient_can_exist_without_user(self):
        patient = Patient.objects.create(**self.patient_data)
        self.assertIsNone(patient.user)

    def test_patient_user_deletion_sets_null(self):
        user = get_user_model().objects.create_user(
            username="patient_user",
            email="patient@example.org",
            password="secure-password-123",
        )
        patient = Patient.objects.create(user=user, **self.patient_data)
        self.assertEqual(patient.user, user)

        user.delete()
        patient.refresh_from_db()
        self.assertIsNone(patient.user)
