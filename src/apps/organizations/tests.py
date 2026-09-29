from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from .models import Facility, HealthcareProfessional, Organization

class OrganizationModelTests(TestCase):
    def test_organization_is_created_with_default_status(self):
        organization = Organization.objects.create(
            name="Test Healthcare Organization",
            organization_type=Organization.OrganizationType.HEALTHCARE_PROVIDER,
        )

        self.assertEqual(
            organization.status,
            Organization.Status.PENDING_VERIFICATION,
        )

    def test_organization_gets_public_id(self):
        organization = Organization.objects.create(
            name="Test Healthcare Organization",
            organization_type=Organization.OrganizationType.HEALTHCARE_PROVIDER,
        )

        self.assertIsNotNone(organization.public_id)


class FacilityModelTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Test Healthcare Organization",
            organization_type=Organization.OrganizationType.HEALTHCARE_PROVIDER,
        )

    def test_facility_belongs_to_organization(self):
        facility = Facility.objects.create(
            organization=self.organization,
            name="Test General Hospital",
            facility_type=Facility.FacilityType.HOSPITAL,
        )

        self.assertEqual(facility.organization, self.organization)

    def test_facility_gets_default_status(self):
        facility = Facility.objects.create(
            organization=self.organization,
            name="Test General Hospital",
            facility_type=Facility.FacilityType.HOSPITAL,
        )

        self.assertEqual(
            facility.status,
            Facility.Status.PENDING_VERIFICATION,
        )

    def test_facility_gets_public_id(self):
        facility = Facility.objects.create(
            organization=self.organization,
            name="Test General Hospital",
            facility_type=Facility.FacilityType.HOSPITAL,
        )

        self.assertIsNotNone(facility.public_id)

    def test_organization_can_have_multiple_facilities(self):
        Facility.objects.create(
            organization=self.organization,
            name="Test General Hospital",
            facility_type=Facility.FacilityType.HOSPITAL,
        )

        Facility.objects.create(
            organization=self.organization,
            name="Test Primary Health Centre",
            facility_type=Facility.FacilityType.PRIMARY_HEALTH_CENTRE,
        )

        self.assertEqual(self.organization.facilities.count(), 2)

    def test_organization_cannot_be_deleted_when_facility_exists(self):
        Facility.objects.create(
            organization=self.organization,
            name="Test General Hospital",
            facility_type=Facility.FacilityType.HOSPITAL,
        )

        with self.assertRaises(ProtectedError):
            self.organization.delete()

class HealthcareProfessionalModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="doctor1",
            first_name="John",
            last_name="Doe",
            email="doctor@example.com",
            password="test-password-123",
        )

    def test_healthcare_professional_belongs_to_user(self):
        professional = HealthcareProfessional.objects.create(
            user=self.user,
            profession=HealthcareProfessional.Profession.DOCTOR,
        )

        self.assertEqual(professional.user, self.user)

    def test_healthcare_professional_gets_public_id(self):
        professional = HealthcareProfessional.objects.create(
            user=self.user,
            profession=HealthcareProfessional.Profession.DOCTOR,
        )

        self.assertIsNotNone(professional.public_id)

    def test_healthcare_professional_has_default_license_status(self):
        professional = HealthcareProfessional.objects.create(
            user=self.user,
            profession=HealthcareProfessional.Profession.DOCTOR,
        )

        self.assertEqual(
            professional.license_status,
            HealthcareProfessional.LicenseStatus.PENDING_VERIFICATION,
        )

    def test_healthcare_professional_has_default_status(self):
        professional = HealthcareProfessional.objects.create(
            user=self.user,
            profession=HealthcareProfessional.Profession.DOCTOR,
        )

        self.assertEqual(
            professional.status,
            HealthcareProfessional.Status.PENDING_VERIFICATION,
        )

    def test_healthcare_professional_has_profession(self):
        professional = HealthcareProfessional.objects.create(
            user=self.user,
            profession=HealthcareProfessional.Profession.NURSE,
        )

        self.assertEqual(
            professional.profession,
            HealthcareProfessional.Profession.NURSE,
        )

    def test_user_can_have_one_healthcare_professional_profile(self):
        professional = HealthcareProfessional.objects.create(
            user=self.user,
            profession=HealthcareProfessional.Profession.DOCTOR,
        )

        self.assertEqual(
            self.user.healthcare_professional,
            professional,
        )

    def test_user_cannot_have_two_healthcare_professional_profiles(self):
        HealthcareProfessional.objects.create(
            user=self.user,
            profession=HealthcareProfessional.Profession.DOCTOR,
        )

        with self.assertRaises(IntegrityError):
            HealthcareProfessional.objects.create(
                user=self.user,
                profession=HealthcareProfessional.Profession.NURSE,
            )

    def test_user_cannot_be_deleted_when_professional_profile_exists(self):
        HealthcareProfessional.objects.create(
            user=self.user,
            profession=HealthcareProfessional.Profession.DOCTOR,
        )

        with self.assertRaises(ProtectedError):
            self.user.delete()