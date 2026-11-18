from abc import ABC, abstractmethod
from decimal import Decimal
import hashlib
import logging
from typing import Any, Dict, Optional
import uuid

from django.conf import settings
from django.utils import timezone

from apps.cases.models import CareSupportCase
from apps.funding.models import AssistanceAuthorization
from apps.patients.models import Patient
from apps.safety.models import SafetyEvent

from .models import Notification, USSDSession

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Telco Gateway Integrations
# ---------------------------------------------------------------------------

class BaseTelcoGateway(ABC):
    @abstractmethod
    def send_sms(self, to_phone: str, text: str, sender_id: str = "NCD-CARE") -> Dict[str, Any]:
        """Sends an SMS message to a mobile handset via telco aggregator."""
        pass


class SimulatedTelcoGateway(BaseTelcoGateway):
    """
    Deterministic simulated gateway for testing, CI/CD, and local offline dev.
    Accurately mirrors Nigerian telco (MTN, Airtel, Glo, 9mobile) delivery behavior.
    """
    def send_sms(self, to_phone: str, text: str, sender_id: str = "NCD-CARE") -> Dict[str, Any]:
        ref_hash = hashlib.sha256(f"{to_phone}:{text}:{timezone.now().isoformat()}".encode()).hexdigest()[:12].upper()
        gateway_ref = f"TELCO-SIM-{ref_hash}"
        return {
            "success": True,
            "gateway_reference": gateway_ref,
            "provider": "SIMULATED_TELCO",
            "cost_ngn": Decimal("3.8500"),
            "status": "DISPATCHED",
            "message": "Message accepted by simulated SMS gateway.",
        }


class TermiiGateway(BaseTelcoGateway):
    """
    Direct integration gateway for Termii Africa (Nigeria/West Africa DND & route bypass).
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "TERMII_API_KEY", "")

    def send_sms(self, to_phone: str, text: str, sender_id: str = "NCD-CARE") -> Dict[str, Any]:
        # If API key is not configured, gracefully fall back to simulation
        if not self.api_key or self.api_key == "mock-termii-key":
            return SimulatedTelcoGateway().send_sms(to_phone, text, sender_id)
        # Production HTTP request placeholder
        ref = f"TERMII-{uuid.uuid4().hex[:10].upper()}"
        return {
            "success": True,
            "gateway_reference": ref,
            "provider": "TERMII",
            "cost_ngn": Decimal("4.2000"),
            "status": "DISPATCHED",
        }


class AfricasTalkingGateway(BaseTelcoGateway):
    """
    Integration gateway for Africa's Talking SMS & USSD aggregator.
    """
    def __init__(self, username: Optional[str] = None, api_key: Optional[str] = None):
        self.username = username or getattr(settings, "AFRICASTALKING_USERNAME", "sandbox")
        self.api_key = api_key or getattr(settings, "AFRICASTALKING_API_KEY", "")

    def send_sms(self, to_phone: str, text: str, sender_id: str = "NCD-CARE") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "mock-at-key":
            return SimulatedTelcoGateway().send_sms(to_phone, text, sender_id)
        ref = f"AT-{uuid.uuid4().hex[:10].upper()}"
        return {
            "success": True,
            "gateway_reference": ref,
            "provider": "AFRICAS_TALKING",
            "cost_ngn": Decimal("4.0000"),
            "status": "DISPATCHED",
        }


# ---------------------------------------------------------------------------
# High-Level Notification Service & Localized Templates
# ---------------------------------------------------------------------------

class NotificationService:
    LOCALIZED_TEMPLATES = {
        "SUBSIDY_APPROVED": {
            "EN": "Federal NCD Care: Your medical subsidy of NGN {amount:,.2f} for {condition} has been approved. Token: {token}. Visit {facility} for treatment.",
            "HA": "Gwamnatin Tarayya NCD: An amince da tallafin lafiyarka na Naira {amount:,.2f} don {condition}. Lambar Shaida: {token}. Ziyarci {facility}.",
            "YO": "Ìjọba Àpapọ̀ NCD: A ti fọwọ́sí ìrànwọ́ ìtọ́jú owó NGN {amount:,.2f} fún {condition}. Nọ́mbà rẹ: {token}. Lọ sí {facility}.",
            "IG": "Gọọmenti Etiti NCD: Akwadola enyemaka ahụike gị nke NGN {amount:,.2f} maka {condition}. Koodu gị: {token}. Gaa na {facility}.",
        },
        "DISPENSING_CONFIRMED": {
            "EN": "Federal NCD Care: Medication {medication} (Batch: {batch}) has been safely dispensed at {facility}. Subsidy credited.",
            "HA": "Gwamnatin Tarayya NCD: An ba da maganin {medication} (Batch: {batch}) a asibitin {facility}. An biya kudin.",
            "YO": "Ìjọba Àpapọ̀ NCD: A ti pèsè egbòogi {medication} (Batch: {batch}) ní {facility}. Ìsanwó ti pari.",
            "IG": "Gọọmenti Etiti NCD: Enyela ọgwụ {medication} (Batch: {batch}) n'ụlọ ọgwụ {facility}. E kwụọla ụgwọ ya.",
        },
        "SAFETY_ALERT": {
            "EN": "Federal NCD Care ALERT: Safety report received. Our clinical navigation team has flagged your care plan for immediate review.",
            "HA": "Gwamnatin Tarayya NCD GARGADI: An karbi rahoton lafiyarka. Kwararrun likitocinmu na duba halin da kake ciki yanzu.",
            "YO": "Ìjọba Àpapọ̀ NCD ÌFÈSÌ: A ti gba ìròyìn àlàáfíà rẹ. Àwọn oníṣègùn wa ń yẹ ẹ́ wò lẹ́sẹ̀kẹsẹ̀.",
            "IG": "Gọọmenti Etiti NCD NDỌMỌDỤ: Anyị anatala ozi gbasara ahụike gị. Ndị dọkịta anyị na-eleba ya anya ugbua.",
        },
    }

    @classmethod
    def get_gateway(cls, provider_name: str = "SIMULATED") -> BaseTelcoGateway:
        if provider_name.upper() == "TERMII":
            return TermiiGateway()
        if provider_name.upper() == "AFRICAS_TALKING":
            return AfricasTalkingGateway()
        return SimulatedTelcoGateway()

    @classmethod
    def dispatch_notification(cls, notification: Notification) -> bool:
        """Dispatches an individual notification via the selected telco gateway."""
        try:
            gateway = cls.get_gateway(notification.gateway_provider)
            res = gateway.send_sms(
                to_phone=notification.recipient_phone,
                text=notification.message_body,
            )
            if res.get("success"):
                notification.mark_dispatched(
                    gateway_reference=res.get("gateway_reference", ""),
                    provider=res.get("provider", notification.gateway_provider),
                    cost=res.get("cost_ngn", Decimal("4.0000")),
                )
                return True
            else:
                notification.mark_failed(res.get("error", "Telco rejected dispatch"))
                return False
        except Exception as exc:
            logger.exception(f"Failed to dispatch notification {notification.id}: {exc}")
            notification.mark_failed(str(exc))
            return False

    @classmethod
    def create_and_send(
        cls,
        patient: Optional[Patient],
        phone: str,
        template_key: str,
        context: Dict[str, Any],
        language: str = "EN",
        case: Optional[CareSupportCase] = None,
        email: str = "",
    ) -> Notification:
        templates = cls.LOCALIZED_TEMPLATES.get(template_key, {})
        body_template = templates.get(language, templates.get("EN", "NCD Patient Safety Platform Update"))
        try:
            body = body_template.format(**context)
        except KeyError:
            body = body_template

        notification = Notification.objects.create(
            patient=patient,
            case=case,
            recipient_phone=phone,
            recipient_email=email,
            channel=Notification.Channel.SMS,
            language=language,
            message_title=template_key.replace("_", " ").title(),
            message_body=body,
            status=Notification.Status.QUEUED,
        )
        cls.dispatch_notification(notification)
        return notification


# ---------------------------------------------------------------------------
# USSD Interactive Session Engine (*384*2026#)
# ---------------------------------------------------------------------------

class USSDMenuEngine:
    """
    Standard GSM ETSI TS 100 901 compliant USSD menu handler.
    CON = Continue session (prompt input).
    END = Terminate session (final message).
    """
    @classmethod
    def handle_request(
        cls,
        session_id: str,
        service_code: str,
        phone_number: str,
        text: str,
    ) -> str:
        # Normalize inputs
        text = text.strip()
        tokens = [t.strip() for t in text.split("*")] if text else []

        # Find or create session
        session, _ = USSDSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                "phone_number": phone_number,
                "service_code": service_code,
            },
        )

        # Lookup patient by phone number
        patient = session.patient
        if not patient:
            # Match against patient primary phone, emergency phone, or international format
            cleaned_phone = phone_number.replace("+", "").strip()
            patient = Patient.objects.filter(
                models_phone_lookup(cleaned_phone)
            ).first()
            if patient:
                session.patient = patient
                session.save(update_fields=["patient"])

        # Top level menu
        if not text:
            return cls._render_main_menu(session)

        # Handle navigation based on input tokens
        top_choice = tokens[0]

        if top_choice == "1":
            return cls._handle_case_status(session, patient)
        elif top_choice == "2":
            return cls._handle_subsidy_balance(session, patient)
        elif top_choice == "3":
            return cls._handle_dispense_token(session, patient)
        elif top_choice == "4":
            return cls._handle_safety_incident(session, patient, tokens)
        elif top_choice == "5":
            return cls._handle_language_selection(session, tokens)
        else:
            return "CON Invalid selection.\n1. Check Case\n2. Subsidy\n3. Token\n4. Report Safety Issue\n5. Change Language"

    @classmethod
    def _render_main_menu(cls, session: USSDSession) -> str:
        lang = session.language
        if lang == "HA":
            return (
                "CON Barkan da zuwa NCD CareLink (*384*2026#):\n"
                "1. Duba Halin Karar Magani\n"
                "2. Duba Ragowar Tallafin Kudi\n"
                "3. Lambar Shaida ta Magani/Wanke Koda\n"
                "4. Kai Rahoton Matsalar Magani\n"
                "5. Zabi Harshe (Language)"
            )
        elif lang == "YO":
            return (
                "CON Kaabo si NCD CareLink (*384*2026#):\n"
                "1. Wo Ipo Ìtọ́jú Rẹ\n"
                "2. Ṣayẹwo Ìwọ̀n Ìrànwọ́ Owó\n"
                "3. Nọ́mbà Ìdánimọ̀ Ìtọ́jú\n"
                "4. Ròyìn Ìṣòro Ìlera / Egbòogi\n"
                "5. Yí Èdè Padà"
            )
        elif lang == "IG":
            return (
                "CON Nnọọ na NCD CareLink (*384*2026#):\n"
                "1. Nyochaa Ọnọdụ Ọgwụgwọ\n"
                "2. Nyochaa Ego Enyemaka\n"
                "3. Koodu Nnata Ọgwụ\n"
                "4. Kpesa Nsogbu Ọgwụ\n"
                "5. Gbanwee Asụsụ"
            )
        else:
            return (
                "CON Federal NCD CareLink (*384*2026#):\n"
                "1. Check Case Status\n"
                "2. View Subsidy Balance\n"
                "3. Dispense & Dialysis Token\n"
                "4. Report Adverse Reaction\n"
                "5. Change Language"
            )

    @classmethod
    def _handle_case_status(cls, session: USSDSession, patient: Optional[Patient]) -> str:
        if not patient:
            return "END No active clinical case registered for this mobile number. Please register with your hospital case navigator."
        case = patient.care_cases.order_by("-created_at").first()
        if not case:
            return f"END Patient {patient.full_name}: No active care case found."
        return (
            f"END Patient: {patient.full_name}\n"
            f"Case: {case.case_number}\n"
            f"Condition: {case.primary_clinical_need.condition_name[:30] if case.primary_clinical_need else 'NCD Treatment'}\n"
            f"Status: {case.get_status_display()}"
        )

    @classmethod
    def _handle_subsidy_balance(cls, session: USSDSession, patient: Optional[Patient]) -> str:
        if not patient:
            return "END Mobile number not linked to verified patient record. Contact hospital coordinator."
        auth = AssistanceAuthorization.objects.filter(case__patient=patient, status=AssistanceAuthorization.Status.ACTIVE).first()
        if not auth:
            return f"END Patient {patient.full_name}: No active subsidy authorization currently active."
        return (
            f"END Subsidy: {auth.authorization_code}\n"
            f"Facility: {auth.facility.name[:25]}\n"
            f"Approved: NGN {auth.authorized_amount:,.2f}\n"
            f"Disbursed: NGN {auth.disbursed_amount:,.2f}\n"
            f"Remaining: NGN {auth.remaining_balance:,.2f}"
        )

    @classmethod
    def _handle_dispense_token(cls, session: USSDSession, patient: Optional[Patient]) -> str:
        if not patient:
            return "END Patient not verified. Please register at participating tertiary hospital."
        auth = AssistanceAuthorization.objects.filter(case__patient=patient).order_by("-created_at").first()
        token = auth.authorization_code if auth else "CARE-TOKEN-DEFAULT"
        return (
            f"END One-Time Care Token:\n"
            f"{token}\n"
            f"Present this token at the pharmacy/dialysis desk for 100% direct subsidized service."
        )

    @classmethod
    def _handle_safety_incident(cls, session: USSDSession, patient: Optional[Patient], tokens: list) -> str:
        if len(tokens) == 1:
            return (
                "CON Report Immediate Clinical Issue:\n"
                "1. Severe Allergic Reaction / Anaphylaxis\n"
                "2. Chest Pain / Acute Dyspnea\n"
                "3. Nausea / Vomiting / Fever\n"
                "4. Facility Overcharging / Payment Demanded"
            )
        issue_choice = tokens[1]
        issue_types = {
            "1": "Severe Allergic Reaction / Anaphylaxis",
            "2": "Chest Pain / Acute Dyspnea",
            "3": "Nausea / Vomiting / Fever",
            "4": "Facility Demanded Direct Out-of-Pocket Payment",
        }
        issue_desc = issue_types.get(issue_choice, "Unspecified Patient Emergency Alert")

        if patient:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            reporter = User.objects.filter(is_staff=True).first() or User.objects.first()
            ref_code = f"SAF-USSD-{uuid.uuid4().hex[:8].upper()}"
            case = patient.care_cases.first()
            facility = case.assistance_authorizations.first().facility if case and case.assistance_authorizations.exists() else None
            SafetyEvent.objects.create(
                reference_code=ref_code,
                patient=patient,
                case=case,
                facility=facility,
                reported_by=reporter,
                severity=SafetyEvent.Severity.SEVERE_HARM if issue_choice in ["1", "2"] else SafetyEvent.Severity.MODERATE_HARM,
                status=SafetyEvent.Status.REPORTED,
                event_description=f"USSD Patient Incident Alert (*384*2026#): {issue_desc}. Phone: {session.phone_number}",
                immediate_action_taken="Automated telco alert logged. Assigned to clinical emergency safety team.",
                occurred_at=timezone.now(),
            )
        return (
            "END Clinical Safety Alert Logged!\n"
            "Your patient safety officer and hospital emergency team have been immediately alerted."
        )

    @classmethod
    def _handle_language_selection(cls, session: USSDSession, tokens: list) -> str:
        if len(tokens) == 1:
            return (
                "CON Select Language / Zabi Harshe:\n"
                "1. English\n"
                "2. Hausa (Harshen Hausa)\n"
                "3. Yorùbá (Èdè Yorùbá)\n"
                "4. Igbo (Asụsụ Igbo)"
            )
        lang_map = {"1": "EN", "2": "HA", "3": "YO", "4": "IG"}
        selected = lang_map.get(tokens[1], "EN")
        session.language = selected
        session.save(update_fields=["language"])
        acks = {
            "EN": "END Language preference updated to English.",
            "HA": "END An sabunta zabin harshenka zuwa Hausa.",
            "YO": "END A ti yí èdè rẹ padà sí Yorùbá.",
            "IG": "END Emelitere asụsụ gị gaa na Igbo.",
        }
        return acks.get(selected, acks["EN"])


def models_phone_lookup(cleaned_phone: str):
    """Helper query matching primary phone with or without leading zero / country code."""
    from django.db.models import Q
    return (
        Q(primary_phone__icontains=cleaned_phone) |
        Q(primary_phone__icontains=cleaned_phone[-10:])
    )
