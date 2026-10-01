"""Thin wrapper around the Anthropic SDK for RCA calls."""

import json

import anthropic
from django.conf import settings

from .prompts import SYSTEM_PROMPT


def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)


def generate_rca(context: dict) -> tuple[dict, anthropic.types.Message]:
    """Send the context package to Claude and return (parsed_json, raw_message)."""
    message = get_client().messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=settings.RCA_MAX_OUTPUT_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(context, default=str)}],
    )
    text = "".join(block.text for block in message.content if block.type == "text")
    return json.loads(text), message
