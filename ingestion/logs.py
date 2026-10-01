"""gunicorn/nginx log ingestion (ARCHITECTURE.md §3.1).

Logs are shipped to CloudWatch Logs; this consumes them via Logs Insights queries
over settings.CLOUDWATCH_LOG_GROUPS (or a subscription filter → SQS).
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def poll_log_groups() -> int:
    """Store new warning/error lines as LogEntry rows (dedup by source_event_id)."""
    logger.debug("poll_log_groups: not implemented yet")
    return 0
