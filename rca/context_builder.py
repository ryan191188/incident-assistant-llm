"""Bounded, redacted context package for an incident (ARCHITECTURE.md §3.4, §5, §9.7)."""

import hashlib
import json
import re

SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key id
    re.compile(r"xox[baprs]-[0-9A-Za-z-]+"),  # Slack tokens
    re.compile(r"sk-ant-[0-9A-Za-z_-]+"),  # Anthropic keys
    re.compile(r"(?i)(password|secret|token)=\S+"),
]


def redact(text: str) -> str:
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def context_hash(context: dict) -> str:
    """Stable hash used to skip RCA calls when nothing material changed (§9.5)."""
    return hashlib.sha256(json.dumps(context, sort_keys=True, default=str).encode()).hexdigest()


def build_context(incident) -> dict:
    """Collect alerts, sampled logs, deployments and commits within the correlation window.

    TODO: time-window queries, message-pattern dedup, token budgeting.
    """
    raise NotImplementedError
