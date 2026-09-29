from django.db.models.deletion import ProtectedError
from django.test import TestCase

from .models import Facility, Organization


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