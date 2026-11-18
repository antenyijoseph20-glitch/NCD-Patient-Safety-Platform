from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone

from apps.organizations.models import Facility, Organization
from apps.patients.models import Patient

from .models import AuditEvent, ConsentAuthorization
from .services import AuditLogger, ConsentManager


class GovernanceAndConsentTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client = Client()

        self.patient_user = User.objects.create_user(
            username="amina_patient",
            email="amina.bello@example.ng",
            first_name="Amina",
            last_name="Bello",
        )
        self.doctor = User.objects.create_user(
            username="dr_fatima",
            email="fatima.audu@nationalhospital.gov.ng",
            first_name="Fatima",
            last_name="Audu",
        )

        self.org = Organization.objects.create(
            name="National Hospital Abuja",
            organization_type=Organization.OrganizationType.HEALTHCARE_PROVIDER,
            status=Organization.Status.ACTIVE,
        )
        self.facility = Facility.objects.create(
            organization=self.org,
            name="Oncology Complex",
            facility_type=Facility.FacilityType.SPECIALIST_CENTRE,
            status=Facility.Status.ACTIVE,
        )

        self.patient = Patient.objects.create(
            first_name="Amina",
            last_name="Bello",
            date_of_birth=date(1990, 8, 12),
            gender=Patient.Gender.FEMALE,
            blood_group=Patient.BloodGroup.O_POSITIVE,
            user=self.patient_user,
        )

    def test_grant_consent_and_validation(self):
        """Validates formal consent granting under NDPA 2023 with SHA-256 seal."""
        consent = ConsentManager.grant_consent(
            patient=self.patient,
            granter=self.patient_user,
            purpose=ConsentAuthorization.Purpose.CARE_COORDINATION,
            scope=ConsentAuthorization.Scope.ALL_CLINICAL_RECORDS,
            legal_basis=ConsentAuthorization.LegalBasis.CONSENT,
            organization=self.org,
            valid_days=180,
        )

        self.assertTrue(consent.is_valid())
        self.assertTrue(bool(consent.consent_document_hash))
        self.assertEqual(consent.status, ConsentAuthorization.Status.ACTIVE)

        # Check manager query
        has_consent = ConsentManager.has_valid_consent(
            patient=self.patient,
            purpose=ConsentAuthorization.Purpose.CARE_COORDINATION,
            organization=self.org,
        )
        self.assertTrue(has_consent)

        # Non-matching purpose should be False
        has_research_consent = ConsentManager.has_valid_consent(
            patient=self.patient,
            purpose=ConsentAuthorization.Purpose.SAFETY_AUDITING,
        )
        self.assertFalse(has_research_consent)

    def test_consent_withdrawal(self):
        """Validates legal right to withdraw consent with timestamp and reason."""
        consent = ConsentManager.grant_consent(
            patient=self.patient,
            granter=self.patient_user,
            purpose=ConsentAuthorization.Purpose.SUBSIDY_APPLICATION,
        )
        self.assertTrue(consent.is_valid())

        # Withdraw
        consent.withdraw(reason="Patient switched to private provider coverage.", user=self.patient_user)

        self.assertEqual(consent.status, ConsentAuthorization.Status.WITHDRAWN)
        self.assertFalse(consent.is_valid())
        self.assertIsNotNone(consent.withdrawn_at)
        self.assertIn("switched", consent.withdrawal_reason)

        has_consent = ConsentManager.has_valid_consent(
            patient=self.patient,
            purpose=ConsentAuthorization.Purpose.SUBSIDY_APPLICATION,
        )
        self.assertFalse(has_consent)

    def test_tamper_evident_audit_log_chaining(self):
        """Verifies immutable cryptographic hash chaining across audit entries."""
        event1 = AuditLogger.log(
            action=AuditEvent.Action.VIEW_PATIENT_RECORD,
            resource_type="Patient",
            resource_id=str(self.patient.public_id),
            actor=self.doctor,
            patient=self.patient,
            description="Viewed oncology staging lab results.",
        )

        event2 = AuditLogger.log(
            action=AuditEvent.Action.APPROVE_FUNDING,
            resource_type="FundingApplication",
            resource_id="APP-2026-TEST",
            actor=self.doctor,
            patient=self.patient,
            description="Four-eyes approval registered.",
        )

        self.assertTrue(bool(event1.event_hash))
        self.assertTrue(bool(event2.event_hash))
        # Event 2 must chain to Event 1's hash
        self.assertEqual(event2.previous_event_hash, event1.event_hash)

    def test_governance_api_endpoints(self):
        """Validates DRF API endpoints for consent authorizations and audit logs."""
        consent = ConsentManager.grant_consent(
            patient=self.patient,
            granter=self.patient_user,
            purpose=ConsentAuthorization.Purpose.CARE_COORDINATION,
        )

        # GET consents
        resp = self.client.get("/api/v1/governance/consents/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        count = data["count"] if isinstance(data, dict) and "count" in data else len(data)
        self.assertGreaterEqual(count, 1)

        # POST withdraw endpoint (authenticated user)
        self.client.force_login(self.patient_user)
        withdraw_resp = self.client.post(
            f"/api/v1/governance/consents/{consent.public_id}/withdraw/",
            {"reason": "Testing withdrawal API endpoint"},
            content_type="application/json",
        )
        self.assertEqual(withdraw_resp.status_code, 200)
        consent.refresh_from_db()
        self.assertEqual(consent.status, ConsentAuthorization.Status.WITHDRAWN)

        # GET audit events
        audit_resp = self.client.get("/api/v1/governance/audit-events/")
        self.assertEqual(audit_resp.status_code, 200)

    def test_audit_expiring_consents_task(self):
        """Validates automated background task for expiring and past-due consents."""
        from apps.governance.tasks import audit_expiring_consents

        # Create a past-due consent
        past_consent = ConsentAuthorization.objects.create(
            patient=self.patient,
            granter=self.patient_user,
            purpose=ConsentAuthorization.Purpose.CARE_COORDINATION,
            valid_from=timezone.now() - timedelta(days=40),
            valid_to=timezone.now() - timedelta(days=5),
            status=ConsentAuthorization.Status.ACTIVE,
        )

        res = audit_expiring_consents()
        self.assertEqual(res["expired_count"], 1)
        past_consent.refresh_from_db()
        self.assertEqual(past_consent.status, ConsentAuthorization.Status.EXPIRED)
