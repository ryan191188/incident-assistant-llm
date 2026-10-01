"""Slack slash-command / interactivity endpoint."""

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from slack_sdk.signature import SignatureVerifier


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def slack_webhook(request):
    if not settings.SLACK_SIGNING_SECRET:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    verifier = SignatureVerifier(settings.SLACK_SIGNING_SECRET)
    if not verifier.is_valid_request(request.body, dict(request.headers)):
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    # TODO: dispatch `/incident status|ack|rca` commands.
    return Response({"response_type": "ephemeral", "text": "Not implemented yet."})
