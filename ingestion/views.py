"""Inbound webhooks for ingestion sources."""

from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .deploys import verify_deploy_webhook


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def cloudwatch_webhook(request):
    """EventBridge API Destination target for CloudWatch alarm state changes."""
    # TODO: verify API Destination auth header, then handle_eventbridge_alarm(request.data).
    return Response({"detail": "Not implemented"}, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def deploy_webhook(request):
    """Fallback deploy webhook for one-off deploys outside the Instance Refresh flow."""
    if not verify_deploy_webhook(request.headers.get("Authorization", "")):
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    # TODO: create Deployment from request.data.
    return Response({"detail": "Not implemented"}, status=status.HTTP_501_NOT_IMPLEMENTED)
