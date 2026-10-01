from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("incidents.urls")),
    path("api/webhooks/", include("ingestion.urls")),
    path("api/webhooks/slack/", include("integrations.slack.urls")),
]
