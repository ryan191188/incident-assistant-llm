from rest_framework import serializers

from .models import Incident, RCAReport


class RCAReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = RCAReport
        fields = [
            "id",
            "summary",
            "likely_root_causes",
            "suggested_next_steps",
            "relevant_evidence",
            "confidence",
            "llm_model",
            "created_at",
        ]


class IncidentSerializer(serializers.ModelSerializer):
    latest_rca = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = [
            "id",
            "title",
            "status",
            "severity",
            "service",
            "opened_at",
            "resolved_at",
            "slack_channel_id",
            "latest_rca",
        ]
        read_only_fields = ["opened_at", "resolved_at"]

    def get_latest_rca(self, obj):
        report = obj.rca_reports.first()
        return RCAReportSerializer(report).data if report else None


class IncidentStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Incident.Status.choices)


class TimelineEntrySerializer(serializers.Serializer):
    kind = serializers.CharField()
    occurred_at = serializers.DateTimeField()
    summary = serializers.CharField()
    ref_id = serializers.IntegerField()
