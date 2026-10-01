from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IncidentViewSet, health

router = DefaultRouter()
router.register("incidents", IncidentViewSet, basename="incident")

urlpatterns = [
    path("health/", health, name="health"),
    path("", include(router.urls)),
]
