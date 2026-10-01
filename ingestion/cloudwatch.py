"""CloudWatch alarm ingestion (ARCHITECTURE.md §3.1).

Primary path is EventBridge → SQS/API Destination; `poll_alarms` is the 60s fallback.
Ingestion must be idempotent: dedup on AlertEvent.source_event_id.
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


def fingerprint_for_alarm(alarm: dict) -> str:
    """Stable fingerprint used by the Correlation Engine to group repeat alarms."""
    return f"cloudwatch:{alarm.get('AlarmName', 'unknown')}"


@shared_task
def poll_alarms() -> int:
    """Fetch alarms in ALARM state via `describe_alarms` and store new AlertEvents."""
    logger.debug("poll_alarms: not implemented yet")
    return 0


def handle_eventbridge_alarm(payload: dict) -> None:
    """Normalize an EventBridge 'CloudWatch Alarm State Change' event into an AlertEvent."""
    raise NotImplementedError
