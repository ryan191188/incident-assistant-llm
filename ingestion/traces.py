"""RDS error-trace reader (ARCHITECTURE.md §3.1).

Reads from settings.RDS_TRACE_DB_URL using a read-only user, ideally a read replica.
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def poll_error_traces() -> int:
    """Copy new trace rows into LogEntry (source=rds_trace)."""
    logger.debug("poll_error_traces: not implemented yet")
    return 0
