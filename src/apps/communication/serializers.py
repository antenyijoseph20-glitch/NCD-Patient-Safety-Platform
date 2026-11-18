from rest_framework import serializers

from .models import Notification, USSDSession


class NotificationSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField(source="patient.full_name")
    channel_display = serializers.CharField(source="get_channel_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "public_id",
            "patient",
            "patient_name",
            "case",
            "recipient_phone",
            "recipient_email",
            "channel",
            "channel_display",
            "language",
            "message_title",
            "message_body",
            "status",
            "status_display",
            "gateway_provider",
            "gateway_reference",
            "cost_ngn",
            "delivery_attempts",
            "sent_at",
            "delivered_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "public_id",
            "status",
            "gateway_provider",
            "gateway_reference",
            "cost_ngn",
            "delivery_attempts",
            "sent_at",
            "delivered_at",
            "created_at",
        ]


class USSDSessionSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField(source="patient.full_name")

    class Meta:
        model = USSDSession
        fields = [
            "id",
            "session_id",
            "phone_number",
            "service_code",
            "patient",
            "patient_name",
            "current_step",
            "language",
            "is_active",
            "created_at",
            "last_interaction_at",
        ]
        read_only_fields = ["id", "created_at", "last_interaction_at"]
