from django.contrib import admin

from .models import AlertEvent, Commit, Deployment, Incident, LogEntry, RCAReport, SlackNotification


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "severity", "service", "opened_at")
    list_filter = ("status", "severity")
    search_fields = ("title", "service", "fingerprint")


@admin.register(AlertEvent)
class AlertEventAdmin(admin.ModelAdmin):
    list_display = ("id", "source", "fingerprint", "incident", "occurred_at")
    list_filter = ("source",)


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "source", "level", "incident", "occurred_at")
    list_filter = ("source", "level")


@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    list_display = ("id", "service", "version", "commit_sha", "status", "deployed_at")


admin.site.register(Commit)
admin.site.register(RCAReport)
admin.site.register(SlackNotification)
