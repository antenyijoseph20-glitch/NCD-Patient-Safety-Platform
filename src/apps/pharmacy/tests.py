from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.clinical_need.models import ClinicalNeed
from apps.organizations.models import Facility, HealthcareProfessional, Organization
from apps.patients.models import Patient
from apps.safety.models import SafetyEvent

from .models import MedicationRegimen, PharmacyDispensingLog

User = get_user_model()


class PharmacyTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.pharmacist_user = User.objects.create_user(
            username="pharm_uche",
            password="PharmPass2026!",
            email="uche@nationalhospital.gov.ng",
            is_staff=True,
        )
        self.client.force_login(self.pharmacist_user)

        self.patient = Patient.objects.create(
            first_name="Amina",
            last_name="Bello",
            date_of_birth=date(1982, 5, 12),
            gender=Patient.Gender.FEMALE,
            primary_phone="+2348061234567",
        )

        self.need = ClinicalNeed.objects.create(
            patient=self.patient,
            condition_name="Infiltrating Ductal Breast Carcinoma",
            icd10_code="C50.9",
            severity=ClinicalNeed.Severity.SEVERE,
        )

        self.org = Organization.objects.create(name="National Hospital Abuja")
        self.facility = Facility.objects.create(
            organization=self.org,
            name="Oncology Chemotherapy Day Care",
            facility_type=Facility.FacilityType.SPECIALIST_CENTRE,
        )

        self.professional = HealthcareProfessional.objects.create(
            user=self.pharmacist_user,
            profession=HealthcareProfessional.Profession.PHARMACIST,
            license_number="PCN-992144",
        )

        self.regimen = MedicationRegimen.objects.create(
            patient=self.patient,
            clinical_need=self.need,
            prescribed_by=self.professional,
            medication_name="Trastuzumab (Herceptin)",
            generic_name="Trastuzumab",
            dosage="440 mg IV infusion",
            frequency="Every 21 days",
            route=MedicationRegimen.Route.INTRAVENOUS,
            total_cycles=6,
            completed_cycles=0,
            status=MedicationRegimen.Status.ACTIVE,
            start_date=date.today(),
            protocol_reference="NCCN-C50-HER2+",
        )

    def test_medication_regimen_progress_and_cycle_advance(self):
        self.assertEqual(self.regimen.progress_percentage, 0)

        # Advance cycle via endpoint
        url = reverse("regimen-advance-cycle", kwargs={"pk": self.regimen.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regimen.refresh_from_db()
        self.assertEqual(self.regimen.completed_cycles, 1)
        self.assertEqual(self.regimen.progress_percentage, 16)

    def test_pharmacy_dispensing_creates_cryptographic_seal(self):
        dispensing = PharmacyDispensingLog.objects.create(
            regimen=self.regimen,
            patient=self.patient,
            facility=self.facility,
            dispensed_by=self.professional,
            medication_name="Trastuzumab 440mg",
            nafdac_reg_number="A4-1029",
            batch_number="TRZ-BATCH-2026-99",
            expiry_date=date.today() + timedelta(days=365),
            quantity_dispensed=Decimal("1.00"),
            cycle_number=2,
            subsidy_amount_applied=Decimal("250000.00"),
        )
        self.assertTrue(len(dispensing.verification_seal_hash) == 64)
        self.regimen.refresh_from_db()
        self.assertEqual(self.regimen.completed_cycles, 2)

    def test_expired_medication_rejected(self):
        expired_date = date.today() - timedelta(days=10)
        dispensing = PharmacyDispensingLog(
            patient=self.patient,
            facility=self.facility,
            medication_name="Expired Doxorubicin",
            nafdac_reg_number="A4-8812",
            batch_number="DOX-EXP-001",
            expiry_date=expired_date,
        )
        with self.assertRaises(ValidationError):
            dispensing.clean()

    def test_seal_verification_endpoint(self):
        dispensing = PharmacyDispensingLog.objects.create(
            patient=self.patient,
            facility=self.facility,
            medication_name="Erythropoietin (EPO) 4000 IU",
            nafdac_reg_number="B4-5512",
            batch_number="EPO-2026-881",
            expiry_date=date.today() + timedelta(days=200),
            quantity_dispensed=Decimal("2.00"),
        )
        url = reverse("dispensing-verify-seal") + f"?seal={dispensing.verification_seal_hash}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data["verified"])
        self.assertEqual(data["batch_number"], "EPO-2026-881")
        self.assertEqual(data["medication_name"], "Erythropoietin (EPO) 4000 IU")

    def test_dispensing_with_adverse_reaction_triggers_safety_event(self):
        url = reverse("dispensing-list")
        payload = {
            "patient": self.patient.id,
            "facility": self.facility.id,
            "dispensed_by": self.professional.id,
            "medication_name": "Paclitaxel 100mg",
            "nafdac_reg_number": "A4-9912",
            "batch_number": "PAC-9912-A",
            "expiry_date": (date.today() + timedelta(days=180)).isoformat(),
            "quantity_dispensed": "1.00",
            "cycle_number": 1,
            "adverse_reaction_observed": True,
            "notes": "Patient developed acute flushing and bronchospasm 5 minutes into infusion.",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check safety event was created
        safety = SafetyEvent.objects.filter(patient=self.patient, severity=SafetyEvent.Severity.MODERATE_HARM).first()
        self.assertIsNotNone(safety)
        self.assertIn("Paclitaxel 100mg", safety.event_description)
