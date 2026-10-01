from django.urls import path

from .consumers import IncidentConsumer

websocket_urlpatterns = [
    path("ws/incidents/<int:incident_id>/", IncidentConsumer.as_asgi()),
]
