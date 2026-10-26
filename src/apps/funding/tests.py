import uuid
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from apps.cases.models import CareSupportCase
from apps.clinical_need.models import ClinicalNeed, ClinicalVerification
from apps.organizations.models import Facility, HealthcareProfessional, Organization
from apps.patients.models import Patient

from .models import (
    AssistanceAuthorization,
    FundingApplication,
    FundingDecision,
    FundingProgramme,
    FundingReview,
    FundingSource,
    ProgrammeRule,
)


class FundingModelTests(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(
            first_name="Amaka",
            last_name="Okonkwo",
            date_of_birth=date(1990, 5, 20),
            gender=Patient.Gender.FEMALE,
        )

        self.need = ClinicalNeed.objects.create(
            patient=self.patient,
            condition_name="Hypertensive Heart Disease",
            clinical_summary="Stage 3 hypertension with cardiac hypertrophy.",
            severity=ClinicalNeed.Severity.SEVERE,
        )

        self.case = CareSupportCase.objects.create(
            case_number="CASE-2026-F001",
            patient=self.patient,
            primary_clinical_need=self.need,
            title="Cardiovascular Intervention and Medication Subsidy",
            priority=CareSupportCase.Priority.HIGH,
            status=CareSupportCase.Status.OPEN,
        )

        self.source = FundingSource.objects.create(
            name="Federal Ministry of Health NCD Grant",
            source_type=FundingSource.SourceType.GOVERNMENT,
            total_allocation=Decimal("50000000.00"),
        )

        self.programme = FundingProgramme.objects.create(
            source=self.source,
            name="Emergency Cardiac Care Programme",
            budget_limit=Decimal("15000000.00"),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )

        self.case_officer = get_user_model().objects.create_user(
            username="officer_chidi",
            email="chidi@example.org",
            password="test-password-123",
        )

        self.funding_director = get_user_model().objects.create_user(
            username="director_fatima",
            email="fatima@example.org",
            password="test-password-123",
        )

        self.org = Organization.objects.create(
            name="National Hospital Abuja",
            organization_type=Organization.OrganizationType.HEALTHCARE_PROVIDER,
        )

        self.facility = Facility.objects.create(
            organization=self.org,
            name="Cardiology Specialist Wing",
            facility_type=Facility.FacilityType.SPECIALIST_CENTRE,
        )

        self.cardiologist_user = get_user_model().objects.create_user(
            username="dr_audu",
            email="audu@example.org",
            password="test-password-123",
        )

        self.cardiologist = HealthcareProfessional.objects.create(
            user=self.cardiologist_user,
            profession=HealthcareProfessional.Profession.DOCTOR,
            license_number="MDCN-998811",
            license_status=HealthcareProfessional.LicenseStatus.VERIFIED,
        )

    def test_funding_source_and_programme_creation(self):
        self.assertEqual(self.source.currency_code, "NGN")
        self.assertEqual(self.source.total_allocation, Decimal("50000000.00"))
        self.assertIsInstance(self.source.public_id, uuid.UUID)

        rule = ProgrammeRule.objects.create(
            programme=self.programme,
            rule_name="Max Cap Per Patient",
            max_amount_per_case=Decimal("500000.00"),
            target_icd10_prefix="I11",
        )
        self.assertEqual(rule.programme, self.programme)
        self.assertTrue(rule.is_active)

    def test_pre_funding_eligibility_enforcement(self):
        # Case is still OPEN (not FUNDING_ELIGIBLE), so clean() should fail:
        app = FundingApplication(
            application_number="APP-2026-0001",
            case=self.case,
            programme=self.programme,
            applied_by=self.case_officer,
            requested_amount=Decimal("350000.00"),
            clinical_justification="Urgent echocardiogram and antihypertensive therapy.",
            status=FundingApplication.Status.SUBMITTED,
        )

        with self.assertRaises(ValidationError) as ctx:
            app.clean()
        self.assertIn("must be FUNDING_ELIGIBLE", str(ctx.exception))

        # Transition case to FUNDING_ELIGIBLE but without verification:
        self.case.status = CareSupportCase.Status.FUNDING_ELIGIBLE
        self.case.save()

        with self.assertRaises(ValidationError) as ctx:
            app.clean()
        self.assertIn("verified clinical verification", str(ctx.exception))

        # Add clinical verification:
        ClinicalVerification.objects.create(
            clinical_need=self.need,
            professional=self.cardiologist,
            facility=self.facility,
            status=ClinicalVerification.Status.VERIFIED,
            verification_notes="Confirmed diagnosis from ECG and clinical examination.",
            verified_at=timezone.now(),
        )

        # Now clean() should succeed without error:
        app.clean()
        app.save()
        self.assertEqual(app.case, self.case)
        self.assertEqual(app.requested_amount, Decimal("350000.00"))

    def test_funding_application_protects_case_from_deletion(self):
        ClinicalVerification.objects.create(
            clinical_need=self.need,
            professional=self.cardiologist,
            facility=self.facility,
            status=ClinicalVerification.Status.VERIFIED,
            verification_notes="Verified.",
            verified_at=timezone.now(),
        )
        self.case.status = CareSupportCase.Status.FUNDING_ELIGIBLE
        self.case.save()

        FundingApplication.objects.create(
            application_number="APP-2026-0002",
            case=self.case,
            programme=self.programme,
            applied_by=self.case_officer,
            requested_amount=Decimal("200000.00"),
            clinical_justification="Medication support.",
        )

        with self.assertRaises(ProtectedError):
            self.case.delete()

    def test_separation_of_duties_on_funding_decision(self):
        ClinicalVerification.objects.create(
            clinical_need=self.need,
            professional=self.cardiologist,
            facility=self.facility,
            status=ClinicalVerification.Status.VERIFIED,
            verification_notes="Verified.",
            verified_at=timezone.now(),
        )
        self.case.status = CareSupportCase.Status.FUNDING_ELIGIBLE
        self.case.save()

        app = FundingApplication.objects.create(
            application_number="APP-2026-0003",
            case=self.case,
            programme=self.programme,
            applied_by=self.case_officer,
            requested_amount=Decimal("450000.00"),
            clinical_justification="Specialist surgery subsidy.",
            status=FundingApplication.Status.UNDER_REVIEW,
        )

        # Funding Review:
        FundingReview.objects.create(
            application=app,
            reviewer=self.funding_director,
            recommendation=FundingReview.Recommendation.RECOMMEND_APPROVAL,
            recommended_amount=Decimal("450000.00"),
            review_notes="Meets all clinical criteria under the grant.",
        )

        # Four-Eyes violation: Officer who submitted tries to approve:
        violating_decision = FundingDecision(
            application=app,
            decision_maker=self.case_officer,
            decision=FundingDecision.Decision.APPROVED,
            approved_amount=Decimal("450000.00"),
            decision_notes="Self-approving (invalid).",
        )

        with self.assertRaises(ValidationError) as ctx:
            violating_decision.clean()
        self.assertIn("Separation of duties violation", str(ctx.exception))

        # Valid decision by independent director:
        valid_decision = FundingDecision(
            application=app,
            decision_maker=self.funding_director,
            decision=FundingDecision.Decision.APPROVED,
            approved_amount=Decimal("450000.00"),
            decision_notes="Approved in full as per committee recommendation.",
        )
        valid_decision.clean()
        valid_decision.save()
        self.assertEqual(valid_decision.approved_amount, Decimal("450000.00"))

        # Assistance Authorization issuance:
        auth = AssistanceAuthorization.objects.create(
            authorization_code="AUTH-2026-0001",
            decision=valid_decision,
            case=self.case,
            facility=self.facility,
            authorized_amount=Decimal("450000.00"),
            valid_from=date(2026, 1, 1),
            valid_to=date(2026, 6, 30),
        )
        self.assertEqual(auth.remaining_balance, Decimal("450000.00"))
        self.assertEqual(auth.status, AssistanceAuthorization.Status.ACTIVE)


class HealthCheckAndAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="api_tester",
            email="api@example.org",
            password="test-password-123",
        )

    def test_health_check_endpoint(self):
        response = self.client.get("/healthz/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["database"], "connected")
        self.assertEqual(data["platform"], "NCD Patient Safety Platform")

    def test_funding_sources_api_list(self):
        FundingSource.objects.create(
            name="WHO NCD Assistance Fund",
            source_type=FundingSource.SourceType.DONOR,
            total_allocation=Decimal("10000000.00"),
        )
        response = self.client.get("/api/v1/funding/sources/")
        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertTrue(len(results) >= 1)
        self.assertEqual(results[0]["name"], "WHO NCD Assistance Fund")
