from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DeliveryReportCallbackView,
    NotificationViewSet,
    USSDCallbackView,
    USSDSessionViewSet,
)

router = DefaultRouter()
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(r"ussd-sessions", USSDSessionViewSet, basename="ussd-session")

urlpatterns = [
    path("ussd/callback/", USSDCallbackView.as_view(), name="ussd-callback"),
    path("dlr/callback/", DeliveryReportCallbackView.as_view(), name="delivery-report-callback"),
    path("", include(router.urls)),
]
