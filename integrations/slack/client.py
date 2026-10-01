"""Outbound Slack notifications (ARCHITECTURE.md §3.7)."""

from django.conf import settings
from slack_sdk import WebClient


def get_client() -> WebClient:
    return WebClient(token=settings.SLACK_BOT_TOKEN)


def post_message(text: str, channel: str | None = None, thread_ts: str | None = None) -> str:
    """Post a message and return its `ts` (store it on SlackNotification.message_ts)."""
    response = get_client().chat_postMessage(
        channel=channel or settings.SLACK_DEFAULT_CHANNEL, text=text, thread_ts=thread_ts
    )
    return response["ts"]
