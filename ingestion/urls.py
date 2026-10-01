from django.urls import path

from . import views

urlpatterns = [
    path("cloudwatch/", views.cloudwatch_webhook, name="webhook-cloudwatch"),
    path("deploy/", views.deploy_webhook, name="webhook-deploy"),
]
