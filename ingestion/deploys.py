"""Deployment/commit collector (ARCHITECTURE.md §3.1, §3.1.1).

Current: EventBridge 'EC2 Instance Refresh Succeeded' → SQS (DEPLOY_EVENTBRIDGE_QUEUE_URL);
commit SHA read from the AMI tag DEPLOY_AMI_COMMIT_TAG_KEY.
Future: swap to CodePipeline 'Pipeline Execution State Change' — only this module changes.
"""

import hmac
import logging

from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task
def poll_deploy_queue() -> int:
    """Receive Instance Refresh events from SQS and create Deployment rows."""
    logger.debug("poll_deploy_queue: not implemented yet")
    return 0


def verify_deploy_webhook(auth_header: str) -> bool:
    """Bearer-token check for the fallback deploy webhook."""
    secret = settings.DEPLOY_WEBHOOK_SECRET
    if not secret or not auth_header.startswith("Bearer "):
        return False
    return hmac.compare_digest(auth_header.removeprefix("Bearer "), secret)
