from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MedicationRegimenViewSet, PharmacyDispensingLogViewSet

router = DefaultRouter()
router.register(r"regimens", MedicationRegimenViewSet, basename="regimen")
router.register(r"dispensings", PharmacyDispensingLogViewSet, basename="dispensing")

urlpatterns = [
    path("", include(router.urls)),
]
