"""Correlation Engine (ARCHITECTURE.md §3.3).

Groups incoming AlertEvents into Incidents. Never calls the RCA orchestrator directly;
it only schedules the debounced `maybe_run_rca` task on incident state transitions (§9.1).
"""

import uuid
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import AlertEvent, Incident


@transaction.atomic
def correlate_alert(alert: AlertEvent, service: str = "") -> Incident:
    """Attach `alert` to an open incident with the same fingerprint, or open a new one."""
    window_start = timezone.now() - timedelta(seconds=settings.CORRELATION_DEDUP_WINDOW_SECONDS)
    incident = (
        Incident.objects.select_for_update()
        .filter(fingerprint=alert.fingerprint, opened_at__gte=window_start)
        .exclude(status=Incident.Status.RESOLVED)
        .first()
    )
    if incident is None:
        incident = Incident.objects.create(
            title=f"Alert: {alert.fingerprint}",
            fingerprint=alert.fingerprint,
            service=service,
        )
    else:
        incident.debounce_token = uuid.uuid4()
        incident.save(update_fields=["debounce_token"])

    alert.incident = incident
    alert.save(update_fields=["incident"])

    from .tasks import maybe_run_rca

    token = str(incident.debounce_token)
    transaction.on_commit(
        lambda: maybe_run_rca.apply_async(
            args=[incident.id, token], countdown=settings.RCA_DEBOUNCE_SECONDS
        )
    )
    return incident
