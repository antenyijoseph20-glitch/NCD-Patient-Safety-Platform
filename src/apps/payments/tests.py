from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.cases.models import CareSupportCase
from apps.clinical_need.models import ClinicalNeed, ClinicalVerification
from apps.funding.models import (
    AssistanceAuthorization,
    FundingApplication,
    FundingDecision,
    FundingProgramme,
    FundingSource,
)
from apps.organizations.models import Facility, HealthcareProfessional, Organization
from apps.patients.models import Patient

from .models import (
    Payment,
    PaymentAdjustment,
    PaymentInstruction,
    Reconciliation,
    ServiceEvidence,
)


class PaymentWorkflowModelTests(TestCase):
    def setUp(self):
        # 1. Patient & Clinical Setup
        self.patient = Patient.objects.create(
            first_name="Babajide",
            last_name="Adeyemi",
            date_of_birth=date(1985, 3, 15),
            gender=Patient.Gender.MALE,
        )

        self.need = ClinicalNeed.objects.create(
            patient=self.patient,
            condition_name="End Stage Renal Disease",
            clinical_summary="Requires regular hemodialysis sessions.",
            severity=ClinicalNeed.Severity.CRITICAL,
        )

        self.org = Organization.objects.create(
            name="Lagos University Teaching Hospital",
            organization_type=Organization.OrganizationType.HEALTHCARE_PROVIDER,
        )

        self.facility = Facility.objects.create(
            organization=self.org,
            name="Nephrology Dialysis Centre",
            facility_type=Facility.FacilityType.SPECIALIST_CENTRE,
        )

        self.doctor_user = get_user_model().objects.create_user(
            username="dr_folake",
            email="folake@example.org",
            password="test-password-123",
        )

        self.doctor = HealthcareProfessional.objects.create(
            user=self.doctor_user,
            profession=HealthcareProfessional.Profession.DOCTOR,
            license_number="MDCN-554433",
            license_status=HealthcareProfessional.LicenseStatus.VERIFIED,
        )

        self.verification = ClinicalVerification.objects.create(
            clinical_need=self.need,
            professional=self.doctor,
            facility=self.facility,
            status=ClinicalVerification.Status.VERIFIED,
            verification_notes="Dialysis schedule confirmed.",
            verified_at=timezone.now(),
        )

        # 2. Case Setup
        self.case = CareSupportCase.objects.create(
            case_number="CASE-2026-P001",
            patient=self.patient,
            primary_clinical_need=self.need,
            title="Hemodialysis Support Package",
            status=CareSupportCase.Status.FUNDING_ELIGIBLE,
        )

        # 3. Actors (Enforcing Separation of Duties)
        self.applicant_user = get_user_model().objects.create_user(
            username="case_worker_emeka",
            email="emeka@example.org",
            password="test-password-123",
        )

        self.funding_approver = get_user_model().objects.create_user(
            username="funding_lead_halima",
            email="halima@example.org",
            password="test-password-123",
        )

        self.finance_officer = get_user_model().objects.create_user(
            username="finance_officer_tunde",
            email="tunde@example.org",
            password="test-password-123",
        )

        self.disbursement_agent = get_user_model().objects.create_user(
            username="disbursement_agent_ngozi",
            email="ngozi@example.org",
            password="test-password-123",
        )

        # 4. Funding Setup
        self.source = FundingSource.objects.create(
            name="National Kidney Care Fund",
            source_type=FundingSource.SourceType.DONOR,
            total_allocation=Decimal("20000000.00"),
        )

        self.programme = FundingProgramme.objects.create(
            source=self.source,
            name="Renal Dialysis Subsidy",
            budget_limit=Decimal("8000000.00"),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )

        self.app = FundingApplication.objects.create(
            application_number="APP-2026-P001",
            case=self.case,
            programme=self.programme,
            applied_by=self.applicant_user,
            requested_amount=Decimal("600000.00"),
            clinical_justification="Bi-weekly hemodialysis for 6 months.",
            status=FundingApplication.Status.APPROVED,
        )

        self.decision = FundingDecision.objects.create(
            application=self.app,
            decision_maker=self.funding_approver,
            decision=FundingDecision.Decision.APPROVED,
            approved_amount=Decimal("600000.00"),
            decision_notes="Approved according to renal subsidy tariff.",
        )

        self.authorization = AssistanceAuthorization.objects.create(
            authorization_code="AUTH-2026-P001",
            decision=self.decision,
            case=self.case,
            facility=self.facility,
            authorized_amount=Decimal("600000.00"),
            valid_from=date(2026, 1, 1),
            valid_to=date(2026, 6, 30),
        )

    def test_payment_instruction_separation_of_duties(self):
        # Violation: Funding approver (Halima) tries to authorize payment instruction:
        violating_instruction = PaymentInstruction(
            instruction_reference="INS-2026-0001",
            authorization=self.authorization,
            payee_facility=self.facility,
            payee_name="LUTH Nephrology Account",
            bank_name="Zenith Bank",
            account_number="1010101010",
            amount=Decimal("200000.00"),
            authorized_by=self.funding_approver,
        )

        with self.assertRaises(ValidationError) as ctx:
            violating_instruction.clean()
        self.assertIn("Separation of duties violation", str(ctx.exception))

        # Valid authorization by Finance Officer:
        valid_instruction = PaymentInstruction(
            instruction_reference="INS-2026-0001",
            authorization=self.authorization,
            payee_facility=self.facility,
            payee_name="LUTH Nephrology Account",
            bank_name="Zenith Bank",
            account_number="1010101010",
            amount=Decimal("200000.00"),
            authorized_by=self.finance_officer,
        )
        valid_instruction.clean()
        valid_instruction.save()
        self.assertEqual(valid_instruction.amount, Decimal("200000.00"))

    def test_instruction_amount_exceeding_balance_fails(self):
        excessive_instruction = PaymentInstruction(
            instruction_reference="INS-2026-EXCESS",
            authorization=self.authorization,
            payee_name="LUTH Nephrology Account",
            bank_name="Zenith Bank",
            account_number="1010101010",
            amount=Decimal("700000.00"),  # Exceeds 600,000 cap
            authorized_by=self.finance_officer,
        )
        with self.assertRaises(ValidationError) as ctx:
            excessive_instruction.clean()
        self.assertIn("exceeds remaining authorization balance", str(ctx.exception))

    def test_payment_execution_separation_of_duties(self):
        instruction = PaymentInstruction.objects.create(
            instruction_reference="INS-2026-0002",
            authorization=self.authorization,
            payee_facility=self.facility,
            payee_name="LUTH Nephrology Account",
            bank_name="Zenith Bank",
            account_number="1010101010",
            amount=Decimal("150000.00"),
            authorized_by=self.finance_officer,
        )

        # Violation: Finance officer who authorized instruction tries to execute payment:
        violating_payment = Payment(
            payment_reference="PAY-2026-0001",
            instruction=instruction,
            amount=Decimal("150000.00"),
            executed_by=self.finance_officer,
            executed_at=timezone.now(),
        )

        with self.assertRaises(ValidationError) as ctx:
            violating_payment.clean()
        self.assertIn("Separation of duties violation", str(ctx.exception))

        # Valid payment execution by disbursement agent:
        valid_payment = Payment(
            payment_reference="PAY-2026-0001",
            instruction=instruction,
            amount=Decimal("150000.00"),
            payment_method=Payment.PaymentMethod.NIBSS_INSTANT_PAYMENT,
            channel_reference="NIP-SESSION-9922883311",
            executed_by=self.disbursement_agent,
            executed_at=timezone.now(),
            status=Payment.Status.SUCCESSFUL,
        )
        valid_payment.clean()
        valid_payment.save()
        self.assertEqual(valid_payment.status, Payment.Status.SUCCESSFUL)

        # Payment Adjustment:
        adjustment = PaymentAdjustment.objects.create(
            adjustment_reference="ADJ-2026-0001",
            payment=valid_payment,
            adjustment_type=PaymentAdjustment.AdjustmentType.REFUND,
            amount=Decimal("15000.00"),
            reason="Unused medication credit returned by hospital.",
            authorized_by=self.finance_officer,
        )
        self.assertEqual(adjustment.payment, valid_payment)

        # Service Evidence Attachment:
        evidence = ServiceEvidence.objects.create(
            case=self.case,
            payment=valid_payment,
            facility=self.facility,
            evidence_type=ServiceEvidence.EvidenceType.INVOICE,
            reference_number="INV-LUTH-8819",
            amount_claimed=Decimal("150000.00"),
            sha256_checksum="11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff",
            verified=True,
            verified_by=self.finance_officer,
            verified_at=timezone.now(),
        )
        self.assertTrue(evidence.verified)

        # Reconciliation:
        reconciliation = Reconciliation.objects.create(
            reconciliation_period_start=date(2026, 1, 1),
            reconciliation_period_end=date(2026, 1, 31),
            total_instruction_amount=Decimal("150000.00"),
            total_executed_amount=Decimal("150000.00"),
            total_adjusted_amount=Decimal("15000.00"),
            discrepancy_amount=Decimal("0.00"),
            status=Reconciliation.Status.BALANCED,
            reconciled_by=self.finance_officer,
            notes="January batch reconciliation balanced against bank statement.",
        )
        self.assertEqual(reconciliation.status, Reconciliation.Status.BALANCED)
