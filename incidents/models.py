"""Core data model (ARCHITECTURE.md §3.2)."""

import uuid

from django.db import models


class Incident(models.Model):
    class Status(models.TextChoices):
        OPEN = "open"
        INVESTIGATING = "investigating"
        MITIGATED = "mitigated"
        RESOLVED = "resolved"

    class Severity(models.TextChoices):
        SEV1 = "sev1"
        SEV2 = "sev2"
        SEV3 = "sev3"
        SEV4 = "sev4"

    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status, default=Status.OPEN)
    severity = models.CharField(max_length=10, choices=Severity, default=Severity.SEV3)
    service = models.CharField(max_length=128, blank=True)
    fingerprint = models.CharField(max_length=128, blank=True, db_index=True)
    opened_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    slack_channel_id = models.CharField(max_length=64, blank=True)

    # RCA cost control (§9.2, §9.3)
    debounce_token = models.UUIDField(default=uuid.uuid4)
    last_rca_at = models.DateTimeField(null=True, blank=True)
    rca_run_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-opened_at"]
        indexes = [models.Index(fields=["status", "service"])]

    def __str__(self):
        return f"#{self.pk} {self.title}"


class AlertEvent(models.Model):
    class Source(models.TextChoices):
        CLOUDWATCH = "cloudwatch"
        CLOUDTRAIL = "cloudtrail"

    incident = models.ForeignKey(
        Incident, null=True, blank=True, on_delete=models.SET_NULL, related_name="alerts"
    )
    source = models.CharField(max_length=20, choices=Source)
    source_event_id = models.CharField(max_length=255, unique=True)
    raw_payload = models.JSONField(default=dict)
    fingerprint = models.CharField(max_length=128, db_index=True)
    occurred_at = models.DateTimeField(db_index=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at"]

    def __str__(self):
        return f"{self.source}:{self.fingerprint} @ {self.occurred_at:%Y-%m-%d %H:%M}"


class LogEntry(models.Model):
    class Source(models.TextChoices):
        GUNICORN = "gunicorn"
        NGINX = "nginx"
        RDS_TRACE = "rds_trace"

    incident = models.ForeignKey(
        Incident, null=True, blank=True, on_delete=models.SET_NULL, related_name="logs"
    )
    source = models.CharField(max_length=20, choices=Source)
    source_event_id = models.CharField(max_length=255, unique=True)
    level = models.CharField(max_length=20, db_index=True)
    message = models.TextField()
    raw_payload = models.JSONField(default=dict)
    occurred_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ["-occurred_at"]
        verbose_name_plural = "log entries"

    def __str__(self):
        return f"[{self.level}] {self.message[:80]}"


class Deployment(models.Model):
    class Status(models.TextChoices):
        SUCCEEDED = "succeeded"
        FAILED = "failed"
        IN_PROGRESS = "in_progress"

    service = models.CharField(max_length=128)
    version = models.CharField(max_length=128, blank=True)
    commit_sha = models.CharField(max_length=64, blank=True, db_index=True)
    source_event_id = models.CharField(max_length=255, unique=True)
    deployed_at = models.DateTimeField(db_index=True)
    deployed_by = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status, default=Status.SUCCEEDED)

    class Meta:
        ordering = ["-deployed_at"]

    def __str__(self):
        return f"{self.service} {self.version or self.commit_sha[:8]}"


class Commit(models.Model):
    sha = models.CharField(max_length=64, unique=True)
    author = models.CharField(max_length=255)
    message = models.TextField()
    files_changed = models.JSONField(default=list)
    committed_at = models.DateTimeField(db_index=True)
    deployment = models.ForeignKey(
        Deployment, null=True, blank=True, on_delete=models.SET_NULL, related_name="commits"
    )

    class Meta:
        ordering = ["-committed_at"]

    def __str__(self):
        return self.sha[:8]


class RCAReport(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="rca_reports")
    summary = models.TextField()
    likely_root_causes = models.JSONField(default=list)
    suggested_next_steps = models.JSONField(default=list)
    relevant_evidence = models.JSONField(default=list)
    confidence = models.CharField(max_length=20, blank=True)
    llm_model = models.CharField(max_length=64)
    prompt_context_ref = models.CharField(max_length=255, blank=True)
    context_hash = models.CharField(max_length=64, blank=True)  # §9.5 pre-filter
    input_tokens = models.PositiveIntegerField(null=True, blank=True)
    output_tokens = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"RCA #{self.pk} for incident #{self.incident_id}"


class SlackNotification(models.Model):
    class Type(models.TextChoices):
        INCIDENT_OPENED = "incident_opened"
        RCA_UPDATE = "rca_update"
        STATUS_CHANGE = "status_change"
        CIRCUIT_BREAKER = "circuit_breaker"

    incident = models.ForeignKey(
        Incident, null=True, blank=True, on_delete=models.CASCADE, related_name="notifications"
    )
    channel = models.CharField(max_length=64)
    message_ts = models.CharField(max_length=64)
    notification_type = models.CharField(max_length=30, choices=Type)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.notification_type} -> {self.channel}"
