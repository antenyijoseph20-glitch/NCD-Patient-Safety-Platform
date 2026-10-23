from datetime import date
import uuid

from django.db.models.deletion import ProtectedError
from django.test import TestCase

from apps.patients.models import Patient
from .models import ClinicalNeed


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
