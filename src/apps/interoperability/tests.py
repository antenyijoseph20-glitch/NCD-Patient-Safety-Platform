import hashlib
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone

from apps.cases.models import CareSupportCase, CaseAssignment, MentalHealthScreening
from apps.clinical_need.ai_service import ClinicalAIDecisionSupport
from apps.clinical_need.models import (
    ClinicalEvidence,
    ClinicalNeed,
    ClinicalVerification,
)
from apps.funding.models import (
    AssistanceAuthorization,
    FundingApplication,
    FundingDecision,
    FundingProgramme,
    FundingSource,
)
from apps.organizations.models import Facility, HealthcareProfessional, Organization
from apps.patients.models import ExternalIdentifier, Patient
from apps.payments.models import Payment, PaymentInstruction, ServiceEvidence
from apps.safety.models import SafetyEvent


class GlobalHealthAndInteroperabilityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client = Client()

        self.doctor = User.objects.create_user(
            username="test_dr_oge",
            email="dr.oge@ncd-safety.gov.ng",
            first_name="Oge",
            last_name="Doctor",
        )
        self.patient_user = User.objects.create_user(
            username="test_patient_user",
            email="patient.test@ncd-safety.gov.ng",
        )

        self.org = Organization.objects.create(
            name="Federal Medical Centre Abuja",
            organization_type=Organization.OrganizationType.HEALTHCARE_PROVIDER,
            status=Organization.Status.ACTIVE,
        )
        self.facility = Facility.objects.create(
            organization=self.org,
            name="FMC Abuja Oncology & Chemotherapy Suite",
            facility_type=Facility.FacilityType.SPECIALIST_CENTRE,
            status=Facility.Status.ACTIVE,
        )

        self.patient = Patient.objects.create(
            first_name="Zainab",
            last_name="Abubakar",
            date_of_birth=date(1985, 3, 14),
            gender=Patient.Gender.FEMALE,
            blood_group=Patient.BloodGroup.A_POSITIVE,
            genotype=Patient.Genotype.AA,
            primary_phone="+2348030001122",
        )
        self.ext_id = ExternalIdentifier.objects.create(
            patient=self.patient,
            system="http://standards.health.gov.ng/nin",
            value="19850314001",
            identifier_type=ExternalIdentifier.IdentifierType.NATIONAL_ID,
            verification_status=ExternalIdentifier.VerificationStatus.VERIFIED,
        )

        self.need = ClinicalNeed.objects.create(
            patient=self.patient,
            condition_name="Invasive Breast Carcinoma",
            icd10_code="C50.9",
            severity=ClinicalNeed.Severity.SEVERE,
            status=ClinicalNeed.Status.VERIFIED,
            clinical_summary="Histology confirmed invasive ductal breast cancer Stage IIb.",
            diagnosed_date=date(2026, 1, 15),
        )

        self.evidence = ClinicalEvidence.objects.create(
            clinical_need=self.need,
            title="Histopathology Biopsy Report",
            evidence_type=ClinicalEvidence.EvidenceType.PATHOLOGY_REPORT,
            document_reference="PATH-2026-001",
            sha256_checksum=hashlib.sha256(b"Histopathology Evidence").hexdigest(),
            issued_by="National Medical Centre",
            issued_date=date(2026, 1, 16),
        )

        self.case = CareSupportCase.objects.create(
            case_number="CASE-2026-TEST-001",
            patient=self.patient,
            primary_clinical_need=self.need,
            title="Oncology Subsidy & Chemotherapy Case",
            description="Patient subsidy case for 6 cycles of chemo.",
            priority=CareSupportCase.Priority.HIGH,
            status=CareSupportCase.Status.ASSISTANCE_ACTIVE,
        )

        self.mental_health = MentalHealthScreening.objects.create(
            case=self.case,
            patient=self.patient,
            screening_tool=MentalHealthScreening.ScreeningTool.PHQ9,
            score=11,
            severity=MentalHealthScreening.Severity.MODERATE,
            suicidal_ideation_detected=False,
            depression_risk_flag=True,
            psychosocial_support_plan="Psychological support sessions scheduled.",
            screened_by=self.doctor,
        )

        # Funding & Payment Setup
        self.source = FundingSource.objects.create(
            name="World Health Organization Global NCD Emergency Grant",
            source_type=FundingSource.SourceType.DONOR,
            status=FundingSource.Status.ACTIVE,
            currency_code="NGN",
            total_allocation=Decimal("200000000.00"),
            allocated_amount=Decimal("1500000.00"),
            disbursed_amount=Decimal("750000.00"),
        )
        self.programme = FundingProgramme.objects.create(
            name="WHO HEARTS Cancer Aid Programme",
            source=self.source,
            description="Patient subsidy grant",
            budget_limit=Decimal("50000000.00"),
            status=FundingProgramme.Status.ACTIVE,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        self.app = FundingApplication.objects.create(
            application_number="APP-2026-TEST-001",
            case=self.case,
            programme=self.programme,
            applicant_type=FundingApplication.ApplicantType.CASE_OFFICER,
            applied_by=self.doctor,
            requested_amount=Decimal("750000.00"),
            approved_amount=Decimal("750000.00"),
            clinical_justification="Verified cancer chemotherapy grant",
            status=FundingApplication.Status.APPROVED,
        )
        self.dec = FundingDecision.objects.create(
            application=self.app,
            decision_maker=self.patient_user,
            decision=FundingDecision.Decision.APPROVED,
            approved_amount=Decimal("750000.00"),
            decision_notes="Approved under WHO guidelines",
        )
        self.auth = AssistanceAuthorization.objects.create(
            authorization_code="AUTH-2026-TEST-001",
            decision=self.dec,
            case=self.case,
            facility=self.facility,
            authorized_amount=Decimal("750000.00"),
            disbursed_amount=Decimal("750000.00"),
            valid_from=date.today(),
            valid_to=date.today() + timedelta(days=60),
            status=AssistanceAuthorization.Status.ACTIVE,
        )
        self.instruction = PaymentInstruction.objects.create(
            instruction_reference="INST-2026-TEST-001",
            authorization=self.auth,
            payee_type=PaymentInstruction.PayeeType.HEALTHCARE_FACILITY,
            payee_facility=self.facility,
            payee_name="FMC Abuja Oncology Suite",
            bank_name="Central Bank of Nigeria",
            account_number="0123456789",
            amount=Decimal("750000.00"),
            authorized_by=self.doctor,
            status=PaymentInstruction.Status.COMPLETED,
        )
        self.payment = Payment.objects.create(
            payment_reference="PAY-2026-TEST-001",
            instruction=self.instruction,
            amount=Decimal("750000.00"),
            payment_method=Payment.PaymentMethod.NIBSS_INSTANT_PAYMENT,
            executed_by=self.patient_user,
            executed_at=timezone.now(),
            status=Payment.Status.SUCCESSFUL,
        )

    def test_fhir_capability_statement(self):
        """HL7 FHIR R4 CapabilityStatement metadata endpoint."""
        resp = self.client.get("/api/fhir/metadata")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["resourceType"], "CapabilityStatement")
        self.assertEqual(data["fhirVersion"], "4.0.1")
        self.assertEqual(data["status"], "active")
        self.assertIn("rest", data)
        security = data["rest"][0]["security"]
        self.assertEqual(security["service"][0]["coding"][0]["code"], "SMART-on-FHIR")
        resources = [r["type"] for r in data["rest"][0]["resource"]]
        self.assertIn("Patient", resources)
        self.assertIn("Condition", resources)
        self.assertIn("CarePlan", resources)
        self.assertIn("Coverage", resources)
        self.assertIn("Claim", resources)

    def test_fhir_patient_bundle(self):
        """HL7 FHIR R4 Patient search / bundle export."""
        resp = self.client.get("/api/fhir/Patient")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["resourceType"], "Bundle")
        self.assertGreaterEqual(data["total"], 1)
        first_entry = data["entry"][0]["resource"]
        self.assertEqual(first_entry["resourceType"], "Patient")
        self.assertIn("identifier", first_entry)

    def test_fhir_condition_bundle(self):
        """HL7 FHIR R4 Condition clinical resource."""
        resp = self.client.get("/api/fhir/Condition")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["resourceType"], "Bundle")
        self.assertGreaterEqual(data["total"], 1)
        entry = data["entry"][0]["resource"]
        self.assertEqual(entry["resourceType"], "Condition")
        self.assertEqual(entry["clinicalStatus"]["coding"][0]["code"], "active")

    def test_fhir_careplan_bundle(self):
        """HL7 FHIR R4 CarePlan resource mapping."""
        resp = self.client.get("/api/fhir/CarePlan")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["resourceType"], "Bundle")
        self.assertGreaterEqual(data["total"], 1)

    def test_fhir_coverage_and_claim(self):
        """HL7 FHIR R4 Financial Interoperability (Coverage & Claim)."""
        resp_cov = self.client.get("/api/fhir/Coverage")
        self.assertEqual(resp_cov.status_code, 200)
        self.assertEqual(resp_cov.json()["resourceType"], "Bundle")

        resp_claim = self.client.get("/api/fhir/Claim")
        self.assertEqual(resp_claim.status_code, 200)
        self.assertEqual(resp_claim.json()["resourceType"], "Bundle")

    def test_ai_clinical_decision_support(self):
        """AI Decision Support guidelines evaluation and compliance scoring."""
        eval_result = ClinicalAIDecisionSupport.evaluate(self.need)
        self.assertIn("NCCN", eval_result["guideline_applied"])
        self.assertGreaterEqual(eval_result["compliance_score"], 50)
        self.assertIn("recommendation", eval_result)
        self.assertTrue(len(eval_result["satisfied_criteria"]) >= 1)

    def test_mental_health_screening(self):
        """Holistic mental health screening scoring and triage."""
        self.assertEqual(self.mental_health.score, 11)
        self.assertEqual(self.mental_health.severity, MentalHealthScreening.Severity.MODERATE)
        self.assertTrue(self.mental_health.depression_risk_flag)

        # DRF endpoint
        resp = self.client.get("/api/v1/mental-health-screenings/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        count = data["count"] if isinstance(data, dict) and "count" in data else len(data)
        self.assertGreaterEqual(count, 1)

    def test_donor_transparency_portal(self):
        """Multi-currency conversions and 100% direct-to-provider routing."""
        resp_usd = self.client.get("/portal/donor/?currency=USD")
        self.assertEqual(resp_usd.status_code, 200)
        self.assertContains(resp_usd, "Global Donor Transparency Portal")
        self.assertContains(resp_usd, "100% Direct-to-Provider Routing")
        self.assertContains(resp_usd, "Zero Leakage")

        resp_eur = self.client.get("/portal/donor/?currency=EUR")
        self.assertEqual(resp_eur.status_code, 200)

        resp_kes = self.client.get("/portal/donor/?currency=KES")
        self.assertEqual(resp_kes.status_code, 200)

    def test_patient_tracker_portal_and_ussd_simulation(self):
        """Patient assistance tracking and low-bandwidth USSD simulation."""
        resp = self.client.get(f"/portal/patient/?q={self.case.case_number}")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Patient &amp; Caregiver Assistance Tracker")
        self.assertContains(resp, "USSD Session: *384*2026#")
        self.assertContains(resp, "Zainab Abubakar")

        # Localized Hausa SMS simulation
        resp_ha = self.client.get(f"/portal/patient/?q={self.case.case_number}&lang=ha")
        self.assertEqual(resp_ha.status_code, 200)
        self.assertContains(resp_ha, "Sannu")
