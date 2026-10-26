from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

from apps.funding.views import (
    AssistanceAuthorizationViewSet,
    FundingApplicationViewSet,
    FundingProgrammeViewSet,
    FundingSourceViewSet,
)
from apps.identity.views import case_demo, demo_form, home
from apps.payments.views import (
    PaymentInstructionViewSet,
    PaymentViewSet,
    ReconciliationViewSet,
    ServiceEvidenceViewSet,
)


def health_check(request):
    db_status = "connected"
    try:
        connection.ensure_connection()
    except Exception as e:
        db_status = f"unhealthy: {e}"

    return JsonResponse(
        {
            "status": "healthy" if db_status == "connected" else "degraded",
            "database": db_status,
            "platform": "NCD Patient Safety Platform",
            "version": "0.1.0",
        },
        status=200 if db_status == "connected" else 503,
    )


router = DefaultRouter()
router.register("funding/sources", FundingSourceViewSet, basename="funding-source")
router.register("funding/programmes", FundingProgrammeViewSet, basename="funding-programme")
router.register("funding/applications", FundingApplicationViewSet, basename="funding-application")
router.register("funding/authorizations", AssistanceAuthorizationViewSet, basename="funding-authorization")
router.register("payments/instructions", PaymentInstructionViewSet, basename="payment-instruction")
router.register("payments/records", PaymentViewSet, basename="payment-record")
router.register("payments/evidence", ServiceEvidenceViewSet, basename="service-evidence")
router.register("payments/reconciliations", ReconciliationViewSet, basename="reconciliation")

urlpatterns = [
    path("", home, name="home"),
    path("healthz/", health_check, name="health_check"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
    path("cases/<int:case_id>/", case_demo, name="case_demo"),
    path("demo-form/", demo_form, name="demo_form"),
    path("admin/", admin.site.urls),
]
