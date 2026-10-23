from datetime import date
import uuid

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from .models import CaregiverRelationship, Patient, PatientContact


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


class PatientContactModelTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(
            first_name="Emeka",
            last_name="Okonkwo",
            date_of_birth=date(1990, 8, 20),
            gender=Patient.Gender.MALE,
        )

    def test_patient_contact_creation(self):
        contact = PatientContact.objects.create(
            patient=self.patient,
            contact_type=PatientContact.ContactType.PHONE,
            value="+2348098765432",
            is_primary=True,
        )

        self.assertEqual(contact.patient, self.patient)
        self.assertTrue(contact.is_primary)
        self.assertIsNotNone(contact.public_id)

    def test_patient_can_have_multiple_contacts(self):
        PatientContact.objects.create(
            patient=self.patient,
            contact_type=PatientContact.ContactType.PHONE,
            value="+2348098765432",
            is_primary=True,
        )
        PatientContact.objects.create(
            patient=self.patient,
            contact_type=PatientContact.ContactType.EMAIL,
            value="emeka.okonkwo@example.org",
        )

        self.assertEqual(self.patient.contacts.count(), 2)

    def test_patient_deletion_cascades_to_contacts(self):
        PatientContact.objects.create(
            patient=self.patient,
            contact_type=PatientContact.ContactType.PHONE,
            value="+2348098765432",
        )
        self.assertEqual(PatientContact.objects.count(), 1)

        self.patient.delete()
        self.assertEqual(PatientContact.objects.count(), 0)


class CaregiverRelationshipModelTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(
            first_name="Chiamaka",
            last_name="Nwosu",
            date_of_birth=date(2010, 3, 15),
            gender=Patient.Gender.FEMALE,
        )
        self.caregiver_user = get_user_model().objects.create_user(
            username="caregiver_nwosu",
            email="caregiver@example.org",
            password="secure-password-123",
        )

    def test_caregiver_relationship_creation(self):
        rel = CaregiverRelationship.objects.create(
            patient=self.patient,
            user=self.caregiver_user,
            relationship_type=CaregiverRelationship.RelationshipType.PARENT,
            can_manage_care=True,
            can_apply_funding=True,
        )

        self.assertEqual(rel.status, CaregiverRelationship.Status.PENDING)
        self.assertTrue(rel.can_manage_care)
        self.assertTrue(rel.can_apply_funding)
        self.assertIsNotNone(rel.public_id)

    def test_unique_patient_caregiver_user_constraint(self):
        CaregiverRelationship.objects.create(
            patient=self.patient,
            user=self.caregiver_user,
            relationship_type=CaregiverRelationship.RelationshipType.PARENT,
        )

        with self.assertRaises(IntegrityError):
            CaregiverRelationship.objects.create(
                patient=self.patient,
                user=self.caregiver_user,
                relationship_type=CaregiverRelationship.RelationshipType.LEGAL_GUARDIAN,
            )

    def test_patient_protected_from_deletion_when_caregiver_exists(self):
        CaregiverRelationship.objects.create(
            patient=self.patient,
            user=self.caregiver_user,
            relationship_type=CaregiverRelationship.RelationshipType.PARENT,
        )

        with self.assertRaises(ProtectedError):
            self.patient.delete()

    def test_user_protected_from_deletion_when_caregiver_exists(self):
        CaregiverRelationship.objects.create(
            patient=self.patient,
            user=self.caregiver_user,
            relationship_type=CaregiverRelationship.RelationshipType.PARENT,
        )

        with self.assertRaises(ProtectedError):
            self.caregiver_user.delete()
