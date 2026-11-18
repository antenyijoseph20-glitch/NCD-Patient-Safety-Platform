import logging

from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification, USSDSession
from .serializers import NotificationSerializer, USSDSessionSerializer
from .services import NotificationService, USSDMenuEngine

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class USSDCallbackView(View):
    """
    Live Telecommunication USSD Gateway Webhook (Africa's Talking / Termii standard).
    Receives HTTP POST requests with parameters:
      - sessionId: Unique string identifying the active telco USSD dialogue.
      - serviceCode: The dialled service shortcode (e.g. *384*2026#).
      - phoneNumber: Mobile subscriber MSISDN (e.g. +2348034567890).
      - text: User input string (concatenated with * by aggregator, or single input).
    Returns plain text starting with CON (continue) or END (terminate).
    """
    def post(self, request, *args, **kwargs):
        # Support both form data and JSON payload
        session_id = request.POST.get("sessionId") or request.POST.get("session_id", "")
        service_code = request.POST.get("serviceCode") or request.POST.get("service_code", "*384*2026#")
        phone_number = request.POST.get("phoneNumber") or request.POST.get("phone_number", "")
        text = request.POST.get("text", "")

        if not session_id or not phone_number:
            # Fall back to json
            if request.content_type == "application/json":
                import json
                try:
                    data = json.loads(request.body.decode("utf-8"))
                    session_id = data.get("sessionId") or data.get("session_id", "")
                    service_code = data.get("serviceCode") or data.get("service_code", "*384*2026#")
                    phone_number = data.get("phoneNumber") or data.get("phone_number", "")
                    text = data.get("text", "")
                except Exception:
                    pass

        if not session_id or not phone_number:
            return HttpResponse("END Invalid USSD request payload.", content_type="text/plain; charset=utf-8")

        response_text = USSDMenuEngine.handle_request(
            session_id=session_id,
            service_code=service_code,
            phone_number=phone_number,
            text=text,
        )
        return HttpResponse(response_text, content_type="text/plain; charset=utf-8")

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


@method_decorator(csrf_exempt, name="dispatch")
class DeliveryReportCallbackView(View):
    """
    Telco Delivery Receipt (DLR) Webhook.
    Receives delivery status updates from telecom aggregator and updates database.
    """
    def post(self, request, *args, **kwargs):
        message_id = (
            request.POST.get("id")
            or request.POST.get("message_id")
            or request.POST.get("gateway_reference")
        )
        status_code = (
            request.POST.get("status")
            or request.POST.get("delivery_status", "")
        ).upper()

        if not message_id and request.content_type == "application/json":
            import json
            try:
                data = json.loads(request.body.decode("utf-8"))
                message_id = data.get("id") or data.get("message_id") or data.get("gateway_reference")
                status_code = (data.get("status") or data.get("delivery_status", "")).upper()
            except Exception:
                pass

        if message_id:
            notification = Notification.objects.filter(gateway_reference=message_id).first()
            if notification:
                if status_code in ["DELIVERED", "SUCCESS", "SUCCESSFUL"]:
                    notification.mark_delivered()
                elif status_code in ["FAILED", "REJECTED", "UNDELIVERED"]:
                    notification.mark_failed(f"Telco DLR: {status_code}")
                return JsonResponse({"status": "acknowledged", "notification_id": notification.id})

        return JsonResponse({"status": "not_found"}, status=200)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and initiating patient SMS/USSD alerts.
    """
    queryset = Notification.objects.select_related("patient", "case").all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        notification = serializer.save()
        # Dispatch immediately
        NotificationService.dispatch_notification(notification)

    @action(detail=True, methods=["post"], url_path="resend")
    def resend(self, request, pk=None):
        notification = self.get_object()
        success = NotificationService.dispatch_notification(notification)
        return Response(
            {
                "success": success,
                "status": notification.status,
                "gateway_reference": notification.gateway_reference,
            },
            status=status.HTTP_200_OK if success else status.HTTP_502_BAD_GATEWAY,
        )


class USSDSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only audit view for USSD telecommunication sessions.
    """
    queryset = USSDSession.objects.select_related("patient").all()
    serializer_class = USSDSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
