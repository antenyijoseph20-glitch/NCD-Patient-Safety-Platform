from datetime import date, timedelta
from decimal import Decimal
import hashlib

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.cases.models import (
    CareSupportCase,
    CaseAssignment,
    MentalHealthScreening,
)
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
    FundingReview,
    FundingSource,
    ProgrammeRule,
)
from apps.organizations.models import Facility, HealthcareProfessional, Organization
from apps.patients.models import (
    CaregiverRelationship,
    ExternalIdentifier,
    Patient,
    PatientContact,
)
from apps.payments.models import (
    Payment,
    PaymentInstruction,
    Reconciliation,
    ServiceEvidence,
)
from apps.safety.models import SafetyEvent


class Command(BaseCommand):
    help = "Seeds comprehensive, realistic Nigerian NCD healthcare, clinical, and financial governance data."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Initializing NCD Patient Safety Platform demo dataset..."))

        User = get_user_model()

        with transaction.atomic():
            # 1. Identity & Governance Users
            self.stdout.write("1. Provisioning identity accounts & governance staff...")
            admin_user, _ = User.objects.get_or_create(
                username="admin_ochi",
                defaults={
                    "first_name": "Adanu",
                    "last_name": "Oche Gabriel",
                    "email": "oche8004@gmail.com",
                    "is_staff": True,
                    "is_superuser": True,
                },
            )
            admin_user.set_password("AdminPass2026!")
            admin_user.save()

            dr_fatima_user, _ = User.objects.get_or_create(
                username="dr_fatima",
                defaults={
                    "first_name": "Fatima",
                    "last_name": "Audu",
                    "email": "fatima.audu@nationalhospital.gov.ng",
                    "is_staff": True,
                },
            )
            dr_fatima_user.set_password("ClinicianPass2026!")
            dr_fatima_user.save()

            dr_chidi_user, _ = User.objects.get_or_create(
                username="dr_chidi",
                defaults={
                    "first_name": "Chidi",
                    "last_name": "Eze",
                    "email": "chidi.eze@luth.edu.ng",
                    "is_staff": True,
                },
            )
            dr_chidi_user.set_password("ClinicianPass2026!")
            dr_chidi_user.save()

            nurse_ngozi_user, _ = User.objects.get_or_create(
                username="nurse_ngozi",
                defaults={
                    "first_name": "Ngozi",
                    "last_name": "Okafor",
                    "email": "ngozi.okafor@carelink.gov.ng",
                    "is_staff": True,
                },
            )
            nurse_ngozi_user.set_password("NursePass2026!")
            nurse_ngozi_user.save()

            officer_kalu_user, _ = User.objects.get_or_create(
                username="officer_kalu",
                defaults={
                    "first_name": "Kalu",
                    "last_name": "Ibrahim",
                    "email": "kalu.ibrahim@ncd-safety.gov.ng",
                    "is_staff": True,
                },
            )
            officer_kalu_user.set_password("StaffPass2026!")
            officer_kalu_user.save()

            director_danladi_user, _ = User.objects.get_or_create(
                username="director_danladi",
                defaults={
                    "first_name": "Danladi",
                    "last_name": "Yakubu",
                    "email": "danladi.yakubu@fmoh.gov.ng",
                    "is_staff": True,
                },
            )
            director_danladi_user.set_password("DirectorPass2026!")
            director_danladi_user.save()

            treasury_femi_user, _ = User.objects.get_or_create(
                username="treasury_femi",
                defaults={
                    "first_name": "Femi",
                    "last_name": "Adeleke",
                    "email": "femi.adeleke@treasury.gov.ng",
                    "is_staff": True,
                },
            )
            treasury_femi_user.set_password("FinancePass2026!")
            treasury_femi_user.save()

            auditor_zainab_user, _ = User.objects.get_or_create(
                username="auditor_zainab",
                defaults={
                    "first_name": "Zainab",
                    "last_name": "Mohammed",
                    "email": "zainab.mohammed@audit.gov.ng",
                    "is_staff": True,
                },
            )
            auditor_zainab_user.set_password("AuditPass2026!")
            auditor_zainab_user.save()

            # 2. Organizations & Healthcare Facilities
            self.stdout.write("2. Establishing accredited healthcare provider network...")
            fmoh_org, _ = Organization.objects.get_or_create(
                name="Federal Ministry of Health & Social Welfare",
                defaults={
                    "organization_type": Organization.OrganizationType.GOVERNMENT,
                    "status": Organization.Status.ACTIVE,
                    "registration_number": "FMOH-FED-001",
                    "email": "info@health.gov.ng",
                    "website": "https://health.gov.ng",
                    "address": "Federal Secretariat Complex, Phase III, Ahmadu Bello Way, Abuja",
                },
            )

            nha_org, _ = Organization.objects.get_or_create(
                name="National Hospital Abuja",
                defaults={
                    "organization_type": Organization.OrganizationType.HEALTHCARE_PROVIDER,
                    "status": Organization.Status.ACTIVE,
                    "registration_number": "NHA-TERTIARY-042",
                    "email": "clinical@nationalhospital.gov.ng",
                    "website": "https://nationalhospital.gov.ng",
                    "address": "Plot 132 Central District (Phase II), Garki, Abuja",
                },
            )

            luth_org, _ = Organization.objects.get_or_create(
                name="Lagos University Teaching Hospital",
                defaults={
                    "organization_type": Organization.OrganizationType.HEALTHCARE_PROVIDER,
                    "status": Organization.Status.ACTIVE,
                    "registration_number": "LUTH-TERTIARY-018",
                    "email": "medical@luth.edu.ng",
                    "website": "https://luth.edu.ng",
                    "address": "Ishaga Road, Idi-Araba, Surulere, Lagos",
                },
            )

            nha_oncology_fac, _ = Facility.objects.get_or_create(
                name="National Hospital Oncology & Radiotherapy Complex",
                defaults={
                    "organization": nha_org,
                    "facility_type": Facility.FacilityType.SPECIALIST_CENTRE,
                    "status": Facility.Status.ACTIVE,
                    "email": "oncology@nationalhospital.gov.ng",
                    "phone": "+2349021234567",
                    "address": "Cancer Care Wing, National Hospital Abuja",
                },
            )

            luth_dialysis_fac, _ = Facility.objects.get_or_create(
                name="LUTH Nephrology Dialysis & Kidney Centre",
                defaults={
                    "organization": luth_org,
                    "facility_type": Facility.FacilityType.SPECIALIST_CENTRE,
                    "status": Facility.Status.ACTIVE,
                    "email": "dialysis@luth.edu.ng",
                    "phone": "+2348039876543",
                    "address": "Block C, Renal Unit, LUTH Complex, Lagos",
                },
            )

            # Healthcare Professionals
            HealthcareProfessional.objects.get_or_create(
                user=dr_fatima_user,
                defaults={
                    "profession": HealthcareProfessional.Profession.DOCTOR,
                    "license_number": "MDCN-102938",
                    "license_status": HealthcareProfessional.LicenseStatus.VERIFIED,
                    "status": HealthcareProfessional.Status.ACTIVE,
                    "phone": "+2348031122334",
                },
            )

            dr_chidi_prof, _ = HealthcareProfessional.objects.get_or_create(
                user=dr_chidi_user,
                defaults={
                    "profession": HealthcareProfessional.Profession.DOCTOR,
                    "license_number": "MDCN-204958",
                    "license_status": HealthcareProfessional.LicenseStatus.VERIFIED,
                    "status": HealthcareProfessional.Status.ACTIVE,
                    "phone": "+2348052233445",
                },
            )

            HealthcareProfessional.objects.get_or_create(
                user=nurse_ngozi_user,
                defaults={
                    "profession": HealthcareProfessional.Profession.NURSE,
                    "license_number": "NMCN-884920",
                    "license_status": HealthcareProfessional.LicenseStatus.VERIFIED,
                    "status": HealthcareProfessional.Status.ACTIVE,
                    "phone": "+2348093344556",
                },
            )

            # 3. Patients, Contacts & Clinical Needs
            self.stdout.write("3. Creating real-world NCD patient cohort & clinical records...")

            # Patient 1: Emeka Nwosu (Renal Disease -> Fully Funded & Disbursed)
            p1, _ = Patient.objects.get_or_create(
                first_name="Emeka",
                last_name="Nwosu",
                defaults={
                    "other_names": "Chukwudi",
                    "date_of_birth": date(1972, 8, 14),
                    "gender": Patient.Gender.MALE,
                    "blood_group": Patient.BloodGroup.B_POSITIVE,
                    "genotype": Patient.Genotype.AS,
                    "status": Patient.Status.ACTIVE,
                    "primary_phone": "+2348034567890",
                    "email": "emeka.nwosu@example.ng",
                    "address": "14 Adeniran Ogunsanya Street, Surulere, Lagos",
                    "emergency_contact_name": "Ifeoma Nwosu",
                    "emergency_contact_phone": "+2348023456789",
                    "emergency_contact_relationship": "Daughter",
                },
            )
            ExternalIdentifier.objects.get_or_create(
                patient=p1,
                system="NIN",
                value="78901234561",
                defaults={
                    "identifier_type": ExternalIdentifier.IdentifierType.NATIONAL_ID,
                    "verification_status": ExternalIdentifier.VerificationStatus.VERIFIED,
                    "issuing_authority": "National Identity Management Commission (NIMC)",
                },
            )
            CaregiverRelationship.objects.get_or_create(
                patient=p1,
                user=nurse_ngozi_user,
                defaults={
                    "relationship_type": CaregiverRelationship.RelationshipType.OTHER,
                    "status": CaregiverRelationship.Status.ACTIVE,
                    "can_view_records": True,
                    "can_manage_care": True,
                    "can_apply_funding": True,
                },
            )

            need1, _ = ClinicalNeed.objects.get_or_create(
                patient=p1,
                condition_name="End-Stage Renal Disease on Hemodialysis",
                defaults={
                    "icd10_code": "N18.6",
                    "severity": ClinicalNeed.Severity.CRITICAL,
                    "status": ClinicalNeed.Status.VERIFIED,
                    "clinical_summary": "Stage 5 CKD requiring twice-weekly hemodialysis sessions, erythropoietin, and electrolyte monitoring.",
                    "diagnosed_date": date(2025, 11, 10),
                },
            )
            ClinicalVerification.objects.get_or_create(
                clinical_need=need1,
                defaults={
                    "professional": dr_chidi_prof,
                    "facility": luth_dialysis_fac,
                    "status": ClinicalVerification.Status.VERIFIED,
                    "verification_notes": "Clinical diagnosis verified through eGFR < 15 and continuous dialysis dependency.",
                    "verified_at": timezone.now() - timedelta(days=20),
                },
            )
            ClinicalEvidence.objects.get_or_create(
                clinical_need=need1,
                title="Renal Function Biopsy & Dialysis Chart",
                defaults={
                    "evidence_type": ClinicalEvidence.EvidenceType.PATHOLOGY_REPORT,
                    "document_reference": "LUTH-LAB-2026-8812",
                    "sha256_checksum": hashlib.sha256(b"Emeka-Nwosu-Renal-Evidence-2026").hexdigest(),
                    "issued_by": luth_dialysis_fac.name,
                    "issued_date": date(2026, 1, 15),
                },
            )

            case1, _ = CareSupportCase.objects.get_or_create(
                case_number="CASE-2026-001",
                defaults={
                    "patient": p1,
                    "primary_clinical_need": need1,
                    "title": "Renal Hemodialysis Maintenance & Subsidy",
                    "description": "Financial assistance program for 24 hemodialysis sessions and dialysis consumables.",
                    "priority": CareSupportCase.Priority.EMERGENCY,
                    "status": CareSupportCase.Status.ASSISTANCE_ACTIVE,
                },
            )
            CaseAssignment.objects.get_or_create(
                case=case1,
                assigned_to=officer_kalu_user,
                defaults={"role": CaseAssignment.Role.CASE_OFFICER, "is_active": True},
            )

            # Patient 2: Amina Bello (Oncology -> Verified, Ready for Committee Action)
            p2, _ = Patient.objects.get_or_create(
                first_name="Amina",
                last_name="Bello",
                defaults={
                    "other_names": "Zahra",
                    "date_of_birth": date(1978, 3, 22),
                    "gender": Patient.Gender.FEMALE,
                    "blood_group": Patient.BloodGroup.O_POSITIVE,
                    "genotype": Patient.Genotype.AA,
                    "status": Patient.Status.ACTIVE,
                    "primary_phone": "+2348061234567",
                    "email": "amina.bello@example.ng",
                    "address": "Plot 89 Gwarinpa Estate, Abuja",
                },
            )
            need2, _ = ClinicalNeed.objects.get_or_create(
                patient=p2,
                condition_name="Infiltrating Ductal Breast Carcinoma",
                defaults={
                    "icd10_code": "C50.9",
                    "severity": ClinicalNeed.Severity.SEVERE,
                    "status": ClinicalNeed.Status.VERIFIED,
                    "clinical_summary": "Locally advanced breast cancer (Stage IIIb). Requires neoadjuvant chemotherapy protocol.",
                    "diagnosed_date": date(2026, 1, 8),
                },
            )
            ClinicalVerification.objects.get_or_create(
                clinical_need=need2,
                defaults={
                    "professional": HealthcareProfessional.objects.get(user=dr_fatima_user),
                    "facility": nha_oncology_fac,
                    "status": ClinicalVerification.Status.VERIFIED,
                    "verification_notes": "Histology and immunohistochemistry confirmed ER/PR positive, HER2 enriched carcinoma.",
                    "verified_at": timezone.now() - timedelta(days=5),
                },
            )
            case2, _ = CareSupportCase.objects.get_or_create(
                case_number="CASE-2026-002",
                defaults={
                    "patient": p2,
                    "primary_clinical_need": need2,
                    "title": "Oncology Diagnostic & Chemotherapy Subsidy",
                    "description": "Oncology grant for 6 cycles of AC-T chemotherapy and targeted biologic therapy.",
                    "priority": CareSupportCase.Priority.HIGH,
                    "status": CareSupportCase.Status.FUNDING_ELIGIBLE,
                },
            )

            # Evidence for Need 1 (Emeka Nwosu - ESRD)
            ClinicalEvidence.objects.get_or_create(
                clinical_need=need1,
                title="Renal Function Panel & Serum Creatinine",
                defaults={
                    "evidence_type": ClinicalEvidence.EvidenceType.LABORATORY_REPORT,
                    "document_reference": "LAB-LUTH-2026-8819",
                    "sha256_checksum": hashlib.sha256(b"Emeka-Nwosu-eGFR-Panel").hexdigest(),
                    "issued_by": "LUTH Central Chemical Pathology Laboratory",
                    "issued_date": date(2026, 1, 10),
                },
            )
            ClinicalEvidence.objects.get_or_create(
                clinical_need=need1,
                title="Renal Ultrasonography Examination",
                defaults={
                    "evidence_type": ClinicalEvidence.EvidenceType.RADIOLOGY_SCAN,
                    "document_reference": "RAD-LUTH-2026-0412",
                    "sha256_checksum": hashlib.sha256(b"Emeka-Nwosu-Renal-Ultrasound").hexdigest(),
                    "issued_by": "LUTH Department of Radiodiagnosis",
                    "issued_date": date(2026, 1, 12),
                },
            )

            # Mental Health Screening for Case 1
            MentalHealthScreening.objects.get_or_create(
                case=case1,
                screening_tool=MentalHealthScreening.ScreeningTool.PHQ9,
                defaults={
                    "patient": p1,
                    "score": 12,
                    "severity": MentalHealthScreening.Severity.MODERATE,
                    "suicidal_ideation_detected": False,
                    "depression_risk_flag": True,
                    "psychosocial_support_plan": "Patient experiencing moderate clinical depressive symptoms secondary to dialysis fatigue. Psychosocial counseling initiated.",
                    "screened_by": nurse_ngozi_user,
                },
            )
            MentalHealthScreening.objects.get_or_create(
                case=case1,
                screening_tool=MentalHealthScreening.ScreeningTool.GAD7,
                defaults={
                    "patient": p1,
                    "score": 10,
                    "severity": MentalHealthScreening.Severity.MODERATE,
                    "suicidal_ideation_detected": False,
                    "depression_risk_flag": False,
                    "psychosocial_support_plan": "Financial and caregiver anxiety addressed through counseling.",
                    "screened_by": nurse_ngozi_user,
                },
            )

            # Evidence for Need 2 (Amina Bello - Breast Carcinoma)
            ClinicalEvidence.objects.get_or_create(
                clinical_need=need2,
                title="Core Needle Biopsy Histopathology Report",
                defaults={
                    "evidence_type": ClinicalEvidence.EvidenceType.PATHOLOGY_REPORT,
                    "document_reference": "PATH-NHA-2026-1192",
                    "sha256_checksum": hashlib.sha256(b"Amina-Bello-Core-Biopsy").hexdigest(),
                    "issued_by": "National Hospital Histopathology Department",
                    "issued_date": date(2026, 1, 15),
                },
            )
            ClinicalEvidence.objects.get_or_create(
                clinical_need=need2,
                title="Immunohistochemistry Profile (ER, PR, HER2)",
                defaults={
                    "evidence_type": ClinicalEvidence.EvidenceType.PATHOLOGY_REPORT,
                    "document_reference": "IHC-NHA-2026-3021",
                    "sha256_checksum": hashlib.sha256(b"Amina-Bello-IHC-Biomarkers").hexdigest(),
                    "issued_by": "National Hospital Molecular Pathology Lab",
                    "issued_date": date(2026, 1, 18),
                },
            )
            ClinicalEvidence.objects.get_or_create(
                clinical_need=need2,
                title="Bilateral Diagnostic Mammography & Ultrasound",
                defaults={
                    "evidence_type": ClinicalEvidence.EvidenceType.RADIOLOGY_SCAN,
                    "document_reference": "IMG-NHA-2026-9901",
                    "sha256_checksum": hashlib.sha256(b"Amina-Bello-Mammogram").hexdigest(),
                    "issued_by": "National Hospital Diagnostic Imaging Wing",
                    "issued_date": date(2026, 1, 12),
                },
            )

            # Mental Health Screening for Case 2
            MentalHealthScreening.objects.get_or_create(
                case=case2,
                screening_tool=MentalHealthScreening.ScreeningTool.PHQ9,
                defaults={
                    "patient": p2,
                    "score": 8,
                    "severity": MentalHealthScreening.Severity.MILD,
                    "suicidal_ideation_detected": False,
                    "depression_risk_flag": False,
                    "psychosocial_support_plan": "Mild reactive distress following cancer diagnosis. Supportive patient navigation provided.",
                    "screened_by": dr_fatima_user,
                },
            )

            # Patient 3: Ibrahim Danjuma (Cardiovascular Disease)
            p3, _ = Patient.objects.get_or_create(
                first_name="Ibrahim",
                last_name="Danjuma",
                date_of_birth=date(1968, 5, 20),
                defaults={
                    "gender": Patient.Gender.MALE,
                    "blood_group": Patient.BloodGroup.O_POSITIVE,
                    "genotype": Patient.Genotype.AA,
                    "primary_phone": "+2348023456789",
                    "email": "ibrahim.danjuma@example.ng",
                    "address": "14 Keffi Close, Kaduna North, Kaduna",
                },
            )
            need3, _ = ClinicalNeed.objects.get_or_create(
                patient=p3,
                condition_name="Hypertensive Heart Disease with Congestive Heart Failure",
                defaults={
                    "icd10_code": "I11.0",
                    "severity": ClinicalNeed.Severity.CRITICAL,
                    "status": ClinicalNeed.Status.VERIFIED,
                    "clinical_summary": "Hypertensive heart disease with severe left ventricular hypertrophy and NYHA Class III heart failure.",
                    "diagnosed_date": date(2026, 1, 20),
                },
            )
            case3, _ = CareSupportCase.objects.get_or_create(
                case_number="CASE-2026-003",
                defaults={
                    "patient": p3,
                    "primary_clinical_need": need3,
                    "title": "Cardiovascular Therapy & Heart Failure Subsidy",
                    "description": "Critical care grant for echocardiogram, cardioprotective pharmacotherapy, and cardiac stabilization.",
                    "priority": CareSupportCase.Priority.EMERGENCY,
                    "status": CareSupportCase.Status.ASSISTANCE_ACTIVE,
                },
            )

            # Patient 4: Ngozi Okafor (Type 2 Diabetes Mellitus)
            p4, _ = Patient.objects.get_or_create(
                first_name="Ngozi",
                last_name="Okafor",
                date_of_birth=date(1976, 11, 14),
                defaults={
                    "gender": Patient.Gender.FEMALE,
                    "blood_group": Patient.BloodGroup.B_POSITIVE,
                    "genotype": Patient.Genotype.AS,
                    "primary_phone": "+2348076543210",
                    "email": "ngozi.okafor@example.ng",
                    "address": "22 Ogui Road, Enugu",
                },
            )
            need4, _ = ClinicalNeed.objects.get_or_create(
                patient=p4,
                condition_name="Type 2 Diabetes Mellitus with Diabetic Kidney Disease",
                defaults={
                    "icd10_code": "E11.2",
                    "severity": ClinicalNeed.Severity.SEVERE,
                    "status": ClinicalNeed.Status.VERIFIED,
                    "clinical_summary": "Uncontrolled diabetes with persistent microalbuminuria (HbA1c 9.8%). Requires analog insulin and SGLT2 inhibitors.",
                    "diagnosed_date": date(2026, 1, 25),
                },
            )
            case4, _ = CareSupportCase.objects.get_or_create(
                case_number="CASE-2026-004",
                defaults={
                    "patient": p4,
                    "primary_clinical_need": need4,
                    "title": "Metabolic Diabetes Care & Renal Protection Subsidy",
                    "description": "Continuous glucose monitoring and protective therapeutic envelope.",
                    "priority": CareSupportCase.Priority.HIGH,
                    "status": CareSupportCase.Status.FUNDING_ELIGIBLE,
                },
            )

            # 4. Funding Sources & Programmes
            self.stdout.write("4. Configuring institutional funding pools & assistance programmes...")
            src_fmoh, _ = FundingSource.objects.get_or_create(
                name="Federal Government National NCD Special Intervention Fund",
                defaults={
                    "source_type": FundingSource.SourceType.GOVERNMENT,
                    "status": FundingSource.Status.ACTIVE,
                    "currency_code": "NGN",
                    "total_allocation": Decimal("150000000.00"),
                    "allocated_amount": Decimal("1200000.00"),
                    "disbursed_amount": Decimal("600000.00"),
                    "contact_name": "Director Danladi Yakubu",
                    "contact_email": "ncd-fund@health.gov.ng",
                },
            )

            src_who, _ = FundingSource.objects.get_or_create(
                name="World Health Organization (WHO) NCD Emergency Action Fund",
                defaults={
                    "source_type": FundingSource.SourceType.DONOR,
                    "status": FundingSource.Status.ACTIVE,
                    "currency_code": "NGN",
                    "total_allocation": Decimal("350000000.00"),
                    "allocated_amount": Decimal("15000000.00"),
                    "disbursed_amount": Decimal("8500000.00"),
                    "contact_name": "Dr. Matshidiso Moeti / WHO Country Rep",
                    "contact_email": "afro-ncd@who.int",
                },
            )

            src_globalfund, _ = FundingSource.objects.get_or_create(
                name="The Global Fund for Chronic Disease & Healthcare Equity",
                defaults={
                    "source_type": FundingSource.SourceType.DONOR,
                    "status": FundingSource.Status.ACTIVE,
                    "currency_code": "NGN",
                    "total_allocation": Decimal("500000000.00"),
                    "allocated_amount": Decimal("25000000.00"),
                    "disbursed_amount": Decimal("12000000.00"),
                    "contact_name": "Global Fund Geneva Grants Unit",
                    "contact_email": "grants@theglobalfund.org",
                },
            )

            src_gates, _ = FundingSource.objects.get_or_create(
                name="Bill & Melinda Gates Foundation Global Health Delivery Fund",
                defaults={
                    "source_type": FundingSource.SourceType.FOUNDATION,
                    "status": FundingSource.Status.ACTIVE,
                    "currency_code": "NGN",
                    "total_allocation": Decimal("250000000.00"),
                    "allocated_amount": Decimal("10000000.00"),
                    "disbursed_amount": Decimal("4500000.00"),
                    "contact_name": "Africa Health Team",
                    "contact_email": "health.africa@gatesfoundation.org",
                },
            )

            src_dangote, _ = FundingSource.objects.get_or_create(
                name="Aliko Dangote Foundation Health & Social Impact CSR",
                defaults={
                    "source_type": FundingSource.SourceType.CORPORATE,
                    "status": FundingSource.Status.ACTIVE,
                    "currency_code": "NGN",
                    "total_allocation": Decimal("75000000.00"),
                    "allocated_amount": Decimal("0.00"),
                    "disbursed_amount": Decimal("0.00"),
                    "contact_name": "CSR Operations Desk",
                    "contact_email": "csr@dangotefoundation.org",
                },
            )

            prog_renal, _ = FundingProgramme.objects.get_or_create(
                name="National Renal Dialysis Subsidy Scheme",
                defaults={
                    "source": src_fmoh,
                    "description": "Covers consumable packs, dialyzer reuse filters, and session fees for hemodialysis patients.",
                    "budget_limit": Decimal("50000000.00"),
                    "allocated_amount": Decimal("1200000.00"),
                    "disbursed_amount": Decimal("600000.00"),
                    "status": FundingProgramme.Status.ACTIVE,
                    "start_date": date(2026, 1, 1),
                    "end_date": date(2026, 12, 31),
                },
            )
            ProgrammeRule.objects.get_or_create(
                programme=prog_renal,
                rule_name="Renal Dialysis Cap Per Patient",
                defaults={
                    "max_amount_per_case": Decimal("1500000.00"),
                    "target_icd10_prefix": "N18",
                    "description": "Maximum of NGN 1,500,000 per patient per calendar year for dialysis support.",
                    "is_active": True,
                },
            )

            prog_cancer, _ = FundingProgramme.objects.get_or_create(
                name="National Oncology Diagnostic & Chemotherapy Relief Fund",
                defaults={
                    "source": src_fmoh,
                    "description": "Direct settlement grant for cancer patients undergoing oncology treatment at certified centres.",
                    "budget_limit": Decimal("60000000.00"),
                    "status": FundingProgramme.Status.ACTIVE,
                    "start_date": date(2026, 1, 1),
                    "end_date": date(2026, 12, 31),
                },
            )

            # 5. Financial Governance Workflow (Applications, Decisions, Authorizations, Payments)
            self.stdout.write("5. Simulating Four-Eyes governance decisions & direct provider settlements...")

            # Application for Case 1 (Emeka Nwosu) -> Approved & Partially Disbursed
            app1, _ = FundingApplication.objects.get_or_create(
                application_number="APP-2026-0001",
                defaults={
                    "case": case1,
                    "programme": prog_renal,
                    "applicant_type": FundingApplication.ApplicantType.CASE_OFFICER,
                    "applied_by": officer_kalu_user,
                    "requested_amount": Decimal("1200000.00"),
                    "approved_amount": Decimal("1200000.00"),
                    "clinical_justification": "Patient requires 24 maintenance hemodialysis sessions and EPO injections. Family is indigent.",
                    "status": FundingApplication.Status.APPROVED,
                    "submitted_at": timezone.now() - timedelta(days=15),
                },
            )

            FundingReview.objects.get_or_create(
                application=app1,
                reviewer=nurse_ngozi_user,
                defaults={
                    "recommendation": FundingReview.Recommendation.RECOMMEND_APPROVAL,
                    "recommended_amount": Decimal("1200000.00"),
                    "review_notes": "Clinical summary and dialysis chart verified. Meets indigent criteria under program guidelines.",
                },
            )

            # Four-Eyes Decision: Danladi != Kalu
            dec1, _ = FundingDecision.objects.get_or_create(
                application=app1,
                defaults={
                    "decision_maker": director_danladi_user,
                    "decision": FundingDecision.Decision.APPROVED,
                    "approved_amount": Decimal("1200000.00"),
                    "conditions": "Payable directly to LUTH Renal Unit upon verification of session logs.",
                    "decision_notes": "Approved in accordance with the National Hemodialysis Lifeline mandate.",
                },
            )

            auth1, _ = AssistanceAuthorization.objects.get_or_create(
                authorization_code="AUTH-2026-0001",
                defaults={
                    "decision": dec1,
                    "case": case1,
                    "facility": luth_dialysis_fac,
                    "authorized_amount": Decimal("1200000.00"),
                    "disbursed_amount": Decimal("600000.00"),
                    "valid_from": date.today() - timedelta(days=10),
                    "valid_to": date.today() + timedelta(days=80),
                    "status": AssistanceAuthorization.Status.ACTIVE,
                },
            )

            # Payment Instruction: Femi != Danladi
            inst1, _ = PaymentInstruction.objects.get_or_create(
                instruction_reference="INST-2026-0001",
                defaults={
                    "authorization": auth1,
                    "payee_type": PaymentInstruction.PayeeType.HEALTHCARE_FACILITY,
                    "payee_facility": luth_dialysis_fac,
                    "payee_name": "LUTH Nephrology Dialysis & Kidney Centre",
                    "bank_name": "First Bank of Nigeria / NIBSS",
                    "account_number": "2034981120",
                    "amount": Decimal("600000.00"),
                    "authorized_by": treasury_femi_user,
                    "status": PaymentInstruction.Status.COMPLETED,
                },
            )

            # Executed Payment: Kalu != Femi
            pay1, _ = Payment.objects.get_or_create(
                payment_reference="PAY-2026-0001",
                defaults={
                    "instruction": inst1,
                    "amount": Decimal("600000.00"),
                    "payment_method": Payment.PaymentMethod.NIBSS_INSTANT_PAYMENT,
                    "channel_reference": "NIBSS-NIP-20260210-994821",
                    "executed_by": officer_kalu_user,
                    "executed_at": timezone.now() - timedelta(days=3),
                    "status": Payment.Status.SUCCESSFUL,
                    "transaction_response": "NIBSS Settlement Confirmed: Account Credited with session verification.",
                },
            )

            # Service Evidence
            ServiceEvidence.objects.get_or_create(
                case=case1,
                reference_number="INV-LUTH-2026-902",
                defaults={
                    "payment": pay1,
                    "facility": luth_dialysis_fac,
                    "evidence_type": ServiceEvidence.EvidenceType.INVOICE,
                    "amount_claimed": Decimal("600000.00"),
                    "document_url": "https://vault.health.gov.ng/invoices/INV-LUTH-2026-902.pdf",
                    "sha256_checksum": hashlib.sha256(b"LUTH-Dialysis-Invoice-Batch-1").hexdigest(),
                    "verified": True,
                    "verified_by": dr_chidi_user,
                    "verified_at": timezone.now() - timedelta(days=2),
                },
            )

            # Application for Case 2 (Amina Bello) -> Submitted & Under Review
            app2, _ = FundingApplication.objects.get_or_create(
                application_number="APP-2026-0002",
                defaults={
                    "case": case2,
                    "programme": prog_cancer,
                    "applicant_type": FundingApplication.ApplicantType.CASE_OFFICER,
                    "applied_by": officer_kalu_user,
                    "requested_amount": Decimal("850000.00"),
                    "clinical_justification": "Neoadjuvant chemotherapy drugs (Doxorubicin, Cyclophosphamide, Paclitaxel) at National Hospital Abuja.",
                    "status": FundingApplication.Status.UNDER_REVIEW,
                    "submitted_at": timezone.now() - timedelta(days=2),
                },
            )
            FundingReview.objects.get_or_create(
                application=app2,
                reviewer=nurse_ngozi_user,
                defaults={
                    "recommendation": FundingReview.Recommendation.RECOMMEND_APPROVAL,
                    "recommended_amount": Decimal("850000.00"),
                    "review_notes": "Prescription protocol and hospital oncology estimation verified. Ready for committee decision.",
                },
            )

            # Application & Direct Payout for Case 3 (Ibrahim Danjuma) -> Direct to National Hospital Abuja
            prog_cvd, _ = FundingProgramme.objects.get_or_create(
                name="WHO HEARTS Cardiovascular Emergency Care Initiative",
                defaults={
                    "source": src_who,
                    "description": "Critical care grant for heart failure decompensation and cardiovascular stabilization.",
                    "budget_limit": Decimal("75000000.00"),
                    "allocated_amount": Decimal("450000.00"),
                    "disbursed_amount": Decimal("450000.00"),
                    "status": FundingProgramme.Status.ACTIVE,
                    "start_date": date(2026, 1, 1),
                    "end_date": date(2026, 12, 31),
                },
            )
            app3, _ = FundingApplication.objects.get_or_create(
                application_number="APP-2026-0003",
                defaults={
                    "case": case3,
                    "programme": prog_cvd,
                    "applicant_type": FundingApplication.ApplicantType.CASE_OFFICER,
                    "applied_by": officer_kalu_user,
                    "requested_amount": Decimal("450000.00"),
                    "approved_amount": Decimal("450000.00"),
                    "clinical_justification": "Acute hypertensive heart failure stabilization at National Hospital Abuja Cardiology Unit.",
                    "status": FundingApplication.Status.APPROVED,
                    "submitted_at": timezone.now() - timedelta(days=6),
                },
            )
            dec3, _ = FundingDecision.objects.get_or_create(
                application=app3,
                defaults={
                    "decision_maker": director_danladi_user,
                    "decision": FundingDecision.Decision.APPROVED,
                    "approved_amount": Decimal("450000.00"),
                    "conditions": "Direct disbursement to National Hospital Abuja Cardiology Care Unit.",
                    "decision_notes": "Approved under WHO HEARTS rapid access window.",
                },
            )
            auth3, _ = AssistanceAuthorization.objects.get_or_create(
                authorization_code="AUTH-2026-0003",
                defaults={
                    "decision": dec3,
                    "case": case3,
                    "facility": nha_oncology_fac,
                    "authorized_amount": Decimal("450000.00"),
                    "disbursed_amount": Decimal("450000.00"),
                    "valid_from": date.today() - timedelta(days=5),
                    "valid_to": date.today() + timedelta(days=60),
                    "status": AssistanceAuthorization.Status.ACTIVE,
                },
            )
            inst3, _ = PaymentInstruction.objects.get_or_create(
                instruction_reference="INST-2026-0003",
                defaults={
                    "authorization": auth3,
                    "payee_type": PaymentInstruction.PayeeType.HEALTHCARE_FACILITY,
                    "payee_facility": nha_oncology_fac,
                    "payee_name": "National Hospital Abuja - Clinical Services",
                    "bank_name": "Zenith Bank / CBN TSA",
                    "account_number": "1019283746",
                    "amount": Decimal("450000.00"),
                    "authorized_by": treasury_femi_user,
                    "status": PaymentInstruction.Status.COMPLETED,
                },
            )
            pay3, _ = Payment.objects.get_or_create(
                payment_reference="PAY-2026-0003",
                defaults={
                    "instruction": inst3,
                    "amount": Decimal("450000.00"),
                    "payment_method": Payment.PaymentMethod.NIBSS_INSTANT_PAYMENT,
                    "channel_reference": "NIBSS-NIP-20260214-772109",
                    "executed_by": officer_kalu_user,
                    "executed_at": timezone.now() - timedelta(days=2),
                    "status": Payment.Status.SUCCESSFUL,
                    "transaction_response": "NIBSS Direct Settlement Confirmed: Account Credited.",
                },
            )
            ServiceEvidence.objects.get_or_create(
                case=case3,
                reference_number="INV-NHA-2026-441",
                defaults={
                    "payment": pay3,
                    "facility": nha_oncology_fac,
                    "evidence_type": ServiceEvidence.EvidenceType.INVOICE,
                    "amount_claimed": Decimal("450000.00"),
                    "document_url": "https://vault.health.gov.ng/invoices/INV-NHA-2026-441.pdf",
                    "sha256_checksum": hashlib.sha256(b"National-Hospital-Abuja-Cardiac-Settlement").hexdigest(),
                    "verified": True,
                    "verified_by": dr_fatima_user,
                    "verified_at": timezone.now() - timedelta(days=1),
                },
            )

            # 6. Periodic Financial Reconciliation Audit
            self.stdout.write("6. Generating initial 30-day banking reconciliation audit...")
            Reconciliation.objects.get_or_create(
                reconciliation_period_start=date.today() - timedelta(days=30),
                reconciliation_period_end=date.today(),
                defaults={
                    "total_instruction_amount": Decimal("600000.00"),
                    "total_executed_amount": Decimal("600000.00"),
                    "total_adjusted_amount": Decimal("0.00"),
                    "discrepancy_amount": Decimal("0.00"),
                    "status": Reconciliation.Status.BALANCED,
                    "reconciled_by": auditor_zainab_user,
                    "notes": "All authorized payment instructions match CBN/NIBSS settlement logs with zero discrepancy.",
                },
            )

            # 7. Clinical Adverse Safety Event
            self.stdout.write("7. Logging patient safety incident...")
            SafetyEvent.objects.get_or_create(
                reference_code="SAF-2026-001",
                defaults={
                    "patient": p2,
                    "case": case2,
                    "facility": nha_oncology_fac,
                    "reported_by": dr_fatima_user,
                    "severity": SafetyEvent.Severity.MODERATE_HARM,
                    "status": SafetyEvent.Status.RESOLVED,
                    "event_description": "Patient developed an acute contrast-induced hypersensitivity reaction during staging CT scan.",
                    "immediate_action_taken": "Immediate intravenous hydrocortisone and chlorpheniramine administered; oxygen therapy maintained until stabilized.",
                    "occurred_at": timezone.now() - timedelta(days=4),
                },
            )

        self.stdout.write(self.style.SUCCESS("Demo dataset successfully populated!"))
        self.stdout.write(self.style.SUCCESS("You can now test the Clinician Portal and Funding & Governance Portal."))
