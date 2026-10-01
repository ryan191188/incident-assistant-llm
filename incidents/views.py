from django.db import connection
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Incident
from .serializers import (
    IncidentSerializer,
    IncidentStatusSerializer,
    RCAReportSerializer,
    TimelineEntrySerializer,
)


class IncidentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Incident.objects.prefetch_related("rca_reports")
    serializer_class = IncidentSerializer

    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        """Merged, time-ordered view of alerts, logs and deploys for the incident."""
        incident = self.get_object()
        entries = [
            {
                "kind": "alert",
                "occurred_at": a.occurred_at,
                "summary": f"{a.source}: {a.fingerprint}",
                "ref_id": a.id,
            }
            for a in incident.alerts.all()
        ] + [
            {
                "kind": "log",
                "occurred_at": log.occurred_at,
                "summary": f"[{log.level}] {log.message[:200]}",
                "ref_id": log.id,
            }
            for log in incident.logs.all()
        ]
        # TODO: include deployments/commits within the correlation window.
        entries.sort(key=lambda e: e["occurred_at"])
        return Response(TimelineEntrySerializer(entries, many=True).data)

    @action(detail=True, methods=["post"], url_path="status")
    def set_status(self, request, pk=None):
        incident = self.get_object()
        serializer = IncidentStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        incident.status = serializer.validated_data["status"]
        if incident.status == Incident.Status.RESOLVED:
            incident.resolved_at = timezone.now()
        incident.save(update_fields=["status", "resolved_at"])
        # TODO: broadcast status change over Channels and Slack.
        return Response(IncidentSerializer(incident).data)

    @action(detail=True, methods=["get"])
    def rca(self, request, pk=None):
        incident = self.get_object()
        return Response(RCAReportSerializer(incident.rca_reports.all(), many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False
    code = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response({"status": "ok" if db_ok else "degraded", "database": db_ok}, status=code)
