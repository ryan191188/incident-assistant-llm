from django.urls import path

from . import views

urlpatterns = [
    path("", views.slack_webhook, name="webhook-slack"),
]
