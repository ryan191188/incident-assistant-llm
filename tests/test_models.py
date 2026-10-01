import pytest
from django.utils import timezone

from incidents.models import AlertEvent, Incident, RCAReport

pytestmark = pytest.mark.django_db


def test_incident_defaults():
    incident = Incident.objects.create(title="High 5xx rate")
    assert incident.status == Incident.Status.OPEN
    assert incident.rca_run_count == 0
    assert incident.debounce_token is not None


def test_latest_rca_ordering():
    incident = Incident.objects.create(title="DB latency")
    RCAReport.objects.create(incident=incident, summary="first", llm_model="m")
    second = RCAReport.objects.create(incident=incident, summary="second", llm_model="m")
    assert incident.rca_reports.first() == second


def test_alert_event_attaches_to_incident():
    incident = Incident.objects.create(title="CPU")
    AlertEvent.objects.create(
        incident=incident,
        source=AlertEvent.Source.CLOUDWATCH,
        source_event_id="evt-1",
        fingerprint="cloudwatch:cpu-high",
        occurred_at=timezone.now(),
    )
    assert incident.alerts.count() == 1
