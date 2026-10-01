"""CloudTrail ingestion (ARCHITECTURE.md §3.1): `lookup_events` poll every 2–5 min."""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def poll_cloudtrail_events() -> int:
    """Store config/deploy-relevant management events as AlertEvents (source=cloudtrail)."""
    logger.debug("poll_cloudtrail_events: not implemented yet")
    return 0
