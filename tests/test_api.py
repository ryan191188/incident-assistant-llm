import pytest

from incidents.models import Incident

pytestmark = pytest.mark.django_db


def test_health_is_public(api_client):
    response = api_client.get("/api/health/")
    assert response.status_code == 200
    assert response.json()["database"] is True


def test_incidents_require_auth(api_client):
    assert api_client.get("/api/incidents/").status_code in (401, 403)


def test_create_and_list_incidents(auth_client):
    response = auth_client.post("/api/incidents/", {"title": "API errors"}, format="json")
    assert response.status_code == 201

    response = auth_client.get("/api/incidents/")
    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_update_status_to_resolved_sets_resolved_at(auth_client):
    incident = Incident.objects.create(title="Queue backlog")
    response = auth_client.post(
        f"/api/incidents/{incident.id}/status/", {"status": "resolved"}, format="json"
    )
    assert response.status_code == 200
    incident.refresh_from_db()
    assert incident.status == Incident.Status.RESOLVED
    assert incident.resolved_at is not None


def test_timeline_and_rca_endpoints(auth_client):
    incident = Incident.objects.create(title="Memory leak")
    assert auth_client.get(f"/api/incidents/{incident.id}/timeline/").json() == []
    assert auth_client.get(f"/api/incidents/{incident.id}/rca/").json() == []


def test_deploy_webhook_rejects_missing_token(api_client):
    assert api_client.post("/api/webhooks/deploy/", {}, format="json").status_code == 401


def test_slack_webhook_rejects_unsigned(api_client):
    assert api_client.post("/api/webhooks/slack/", {}).status_code == 401
