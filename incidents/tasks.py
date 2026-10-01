"""Celery tasks for incident RCA orchestration (ARCHITECTURE.md §3.4, §9)."""

import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import Incident

logger = logging.getLogger(__name__)


@shared_task
def maybe_run_rca(incident_id: int, token: str) -> None:
    """Debounced entrypoint: only the last task scheduled in a burst proceeds (§9.2)."""
    incident = Incident.objects.get(id=incident_id)
    if str(incident.debounce_token) != token:
        return  # superseded by a newer event in the same burst

    if incident.rca_run_count >= settings.RCA_MAX_RUNS_PER_INCIDENT:
        logger.info("Incident %s hit RCA run cap; skipping", incident_id)
        return
    if (
        incident.last_rca_at
        and (timezone.now() - incident.last_rca_at).total_seconds()
        < settings.RCA_MIN_INTERVAL_SECONDS
    ):
        logger.info("Incident %s within RCA cooldown; skipping", incident_id)
        return

    run_rca_for_incident.delay(incident_id)


@shared_task
def run_rca_for_incident(incident_id: int) -> None:
    """Build context, call Claude, persist an RCAReport, and notify.

    TODO: global circuit breaker (§9.4), context-hash pre-filter (§9.5),
    fingerprint cache (§9.6), Slack + Channels broadcast.
    """
    raise NotImplementedError
