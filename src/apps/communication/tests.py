from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.cases.models import CareSupportCase
from apps.clinical_need.models import ClinicalNeed
from apps.funding.models import (
    AssistanceAuthorization,
    FundingApplication,
    FundingDecision,
    FundingProgramme,
    FundingSource,
)
from apps.organizations.models import Facility, Organization
from apps.patients.models import Patient
from apps.safety.models import SafetyEvent

from .models import Notification, USSDSession
from .services import NotificationService, USSDMenuEngine

User = get_user_model()


class CommunicationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            username="comm_officer",
            password="OfficerPass2026!",
            email="comm@health.gov.ng",
            is_staff=True,
        )

        self.patient = Patient.objects.create(
            first_name="Amina",
            last_name="Bello",
            date_of_birth=date(1982, 5, 12),
            gender=Patient.Gender.FEMALE,
            primary_phone="+2348061234567",
            email="amina.bello@example.ng",
        )

        self.need = ClinicalNeed.objects.create(
            patient=self.patient,
            condition_name="Infiltrating Ductal Breast Carcinoma",
            icd10_code="C50.9",
            severity=ClinicalNeed.Severity.SEVERE,
        )

        self.case = CareSupportCase.objects.create(
            case_number="CASE-2026-TEST",
            patient=self.patient,
            primary_clinical_need=self.need,
            title="Breast Oncology Care Support",
            status=CareSupportCase.Status.ASSISTANCE_ACTIVE,
        )

        self.org = Organization.objects.create(name="Federal Health Board")
        self.facility = Facility.objects.create(
            organization=self.org,
            name="National Hospital Cancer Centre",
            facility_type=Facility.FacilityType.SPECIALIST_CENTRE,
        )

        src = FundingSource.objects.create(name="Cancer Fund", source_type=FundingSource.SourceType.GOVERNMENT)
        prog = FundingProgramme.objects.create(
            name="Chemotherapy Access",
            source=src,
            budget_limit=Decimal("10000000.00"),
            start_date=date.today(),
            end_date=date(2026, 12, 31),
        )
        app = FundingApplication.objects.create(
            case=self.case,
            programme=prog,
            applied_by=self.staff_user,
            requested_amount=Decimal("350000.00"),
            approved_amount=Decimal("350000.00"),
            status=FundingApplication.Status.APPROVED,
        )
        dec = FundingDecision.objects.create(
            application=app,
            decision_maker=self.staff_user,
            decision=FundingDecision.Decision.APPROVED,
            approved_amount=Decimal("350000.00"),
        )
        self.auth = AssistanceAuthorization.objects.create(
            authorization_code="AUTH-COMM-TEST",
            decision=dec,
            case=self.case,
            facility=self.facility,
            authorized_amount=Decimal("350000.00"),
            disbursed_amount=Decimal("100000.00"),
            valid_from=date.today(),
            valid_to=date(2026, 12, 31),
            status=AssistanceAuthorization.Status.ACTIVE,
        )

    def test_notification_creation_and_simulated_dispatch(self):
        notif = NotificationService.create_and_send(
            patient=self.patient,
            phone=self.patient.primary_phone,
            template_key="SUBSIDY_APPROVED",
            context={
                "amount": Decimal("350000.00"),
                "condition": "Breast Oncology",
                "token": "AUTH-COMM-TEST",
                "facility": "National Hospital",
            },
            language="EN",
            case=self.case,
        )
        self.assertEqual(notif.status, Notification.Status.DISPATCHED)
        self.assertTrue(notif.gateway_reference.startswith("TELCO-SIM-"))
        self.assertIn("350,000.00", notif.message_body)
        self.assertEqual(notif.delivery_attempts, 1)

    def test_multilingual_templates(self):
        # Hausa
        ha_notif = NotificationService.create_and_send(
            patient=self.patient,
            phone=self.patient.primary_phone,
            template_key="SUBSIDY_APPROVED",
            context={
                "amount": Decimal("350000.00"),
                "condition": "Kansar Nono",
                "token": "AUTH-COMM-TEST",
                "facility": "Asibitin Kasa",
            },
            language="HA",
        )
        self.assertIn("tallafin lafiyarka na Naira", ha_notif.message_body)

        # Yorùbá
        yo_notif = NotificationService.create_and_send(
            patient=self.patient,
            phone=self.patient.primary_phone,
            template_key="SUBSIDY_APPROVED",
            context={
                "amount": Decimal("350000.00"),
                "condition": "Àrùn Jẹjẹrẹ Ọmú",
                "token": "AUTH-COMM-TEST",
                "facility": "National Hospital",
            },
            language="YO",
        )
        self.assertIn("ìrànwọ́ ìtọ́jú owó", yo_notif.message_body)

        # Igbo
        ig_notif = NotificationService.create_and_send(
            patient=self.patient,
            phone=self.patient.primary_phone,
            template_key="SUBSIDY_APPROVED",
            context={
                "amount": Decimal("350000.00"),
                "condition": "Ọrịa Kansa",
                "token": "AUTH-COMM-TEST",
                "facility": "Ụlọ Ọgwụ National",
            },
            language="IG",
        )
        self.assertIn("Akwadola enyemaka ahụike gị", ig_notif.message_body)

    def test_ussd_menu_engine_flows(self):
        # 1. Initial dial -> Main Menu
        resp = USSDMenuEngine.handle_request(
            session_id="SESSION-101",
            service_code="*384*2026#",
            phone_number=self.patient.primary_phone,
            text="",
        )
        self.assertTrue(resp.startswith("CON Federal NCD CareLink"))
        self.assertIn("1. Check Case Status", resp)

        # 2. Option 1: Check Case Status
        resp_case = USSDMenuEngine.handle_request(
            session_id="SESSION-101",
            service_code="*384*2026#",
            phone_number=self.patient.primary_phone,
            text="1",
        )
        self.assertTrue(resp_case.startswith("END Patient: Amina Bello"))
        self.assertIn("CASE-2026-TEST", resp_case)

        # 3. Option 2: Check Subsidy Balance
        resp_subsidy = USSDMenuEngine.handle_request(
            session_id="SESSION-102",
            service_code="*384*2026#",
            phone_number=self.patient.primary_phone,
            text="2",
        )
        self.assertTrue(resp_subsidy.startswith("END Subsidy: AUTH-COMM-TEST"))
        self.assertIn("Remaining: NGN 250,000.00", resp_subsidy)

        # 4. Option 4: Report Adverse Reaction (Emergency)
        resp_safety_prompt = USSDMenuEngine.handle_request(
            session_id="SESSION-103",
            service_code="*384*2026#",
            phone_number=self.patient.primary_phone,
            text="4",
        )
        self.assertTrue(resp_safety_prompt.startswith("CON Report Immediate Clinical Issue"))

        resp_safety_submit = USSDMenuEngine.handle_request(
            session_id="SESSION-103",
            service_code="*384*2026#",
            phone_number=self.patient.primary_phone,
            text="4*1",
        )
        self.assertTrue(resp_safety_submit.startswith("END Clinical Safety Alert Logged!"))
        # Verify safety event was created in DB
        event = SafetyEvent.objects.filter(patient=self.patient).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.severity, SafetyEvent.Severity.SEVERE_HARM)
        self.assertIn("Severe Allergic Reaction", event.event_description)

    def test_ussd_http_webhook(self):
        url = reverse("ussd-callback")
        response = self.client.post(
            url,
            {
                "sessionId": "WEBHOOK-SESS-99",
                "serviceCode": "*384*2026#",
                "phoneNumber": "+2348061234567",
                "text": "1",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertIn("CASE-2026-TEST", response.content.decode("utf-8"))

    def test_dlr_webhook_updates_status(self):
        notif = Notification.objects.create(
            recipient_phone="+2348061234567",
            message_body="Test DLR message",
            status=Notification.Status.DISPATCHED,
            gateway_reference="TELCO-REF-8842",
        )
        url = reverse("delivery-report-callback")
        response = self.client.post(
            url,
            {"gateway_reference": "TELCO-REF-8842", "status": "DELIVERED"},
        )
        self.assertEqual(response.status_code, 200)
        notif.refresh_from_db()
        self.assertEqual(notif.status, Notification.Status.DELIVERED)
        self.assertIsNotNone(notif.delivered_at)

    def test_notification_rest_api(self):
        self.client.force_login(self.staff_user)
        url = reverse("notification-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
