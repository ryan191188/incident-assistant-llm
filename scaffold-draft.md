# Plan: Scaffold Incident Assistant (Django 6.1 + Uvicorn + PostgreSQL)

## Context
The repo only contains `README.md` and `architecture.md` (the design for a Django-based
Production Incident Assistant: CloudWatch/CloudTrail/log/deploy ingestion → correlation →
Claude RCA → Slack + WebSocket). We need the initial project skeleton that matches the
layout in README "Project Structure", runs under Uvicorn (ASGI, Channels-ready) against
PostgreSQL, with Celery/Redis wiring, Docker Compose for local dev, a test harness, and a
CLAUDE.md. Business logic stays stubbed; models from architecture §3.2 are implemented.

Environment facts: host default `python` is 3.9 (too old for Django 6.1), but `py -3.14`
is installed; Docker 29 available. Latest versions: Django 6.1.1, DRF 3.18.1,
channels 4.3.2, uvicorn 0.54.0, celery 5.6.3, psycopg 3.3.6.

## Scope
This is a scaffold, not the features. The models, settings, routing and wiring will be real. 
Ingestion adapters, correlation, the RCA/Claude code and Slack will be stubs with docstrings 
that point to the matching section of the architecture doc. Everything has to boot, migrate 
and pass its smoke tests.

## Dependencies
- `requirements.txt` (README references it): `Django~=6.1`, `djangorestframework`,
  `channels`, `channels-redis`, `uvicorn[standard]` (websockets support), `psycopg[binary]`,
  `dj-database-url`, `django-environ`, `celery[redis]`, `redis`,
  `boto3`, `anthropic`, `slack_sdk`.
- `requirements-dev.txt`: `-r requirements.txt`, `pytest`, `pytest-django`,
  `pytest-asyncio`, `factory-boy`, `ruff`.
- `pyproject.toml`: project metadata (requires-python >=3.12) + `[tool.pytest.ini_options]`
  (`DJANGO_SETTINGS_MODULE=config.settings`, testpaths=tests) + `[tool.ruff]` config.
- Local venv: `py -3.14 -m venv .venv` then `.venv/Scripts/pip install -r requirements-dev.txt`.

## Directory structure (per README)
```
config/        __init__.py (imports celery app), settings.py, urls.py, asgi.py
               (ProtocolTypeRouter: http + websocket via AuthMiddlewareStack), wsgi.py, celery.py
incidents/     models.py, admin.py, serializers.py, views.py, urls.py, consumers.py,
               routing.py (ws/incidents/<id>/), correlation.py, tasks.py, apps.py, migrations/
ingestion/     cloudwatch.py, cloudtrail.py, logs.py, traces.py, deploys.py (stub functions
               + docstrings referencing arch §3.1), apps.py
rca/           context_builder.py, client.py (Anthropic client wrapper, model from settings),
               prompts.py
integrations/slack/  client.py, verification.py (signing-secret check stub), views.py
tests/         conftest.py, test_models.py, test_api.py, test_health.py
manage.py, Dockerfile, docker-compose.yml, .env.example, .gitignore, .dockerignore, CLAUDE.md
```

## Key file contents
- **settings.py**: env-driven via `django-environ` (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`,
  `DATABASE_URL`, `REDIS_URL`, AWS/Claude/Slack vars from README table). `ASGI_APPLICATION`,
  `CHANNEL_LAYERS` (channels_redis), Celery config from `REDIS_URL`, DRF defaults
  (session + token auth), RCA cost-control settings from arch §9.8
  (`RCA_DEBOUNCE_SECONDS=45`, `RCA_MIN_INTERVAL_SECONDS=120`, `RCA_MAX_RUNS_PER_INCIDENT=5`,
  `LLM_CIRCUIT_BREAKER_THRESHOLD=20`, `RCA_CACHE_TTL_SECONDS=3600`, `RCA_MAX_CONTEXT_TOKENS`).
  `CLAUDE_MODEL` defaults to `claude-sonnet-4-6` as documented (env-overridable).
- **incidents/models.py**: `Incident` (status/severity TextChoices, `debounce_token`,
  `last_rca_at`, `rca_run_count`), `AlertEvent`, `LogEntry`, `Deployment`, `Commit`,
  `RCAReport` (+ `context_hash` for §9.5), `SlackNotification`; JSONField payloads;
  indexes on `occurred_at`, `fingerprint`, `incident`. Initial migration generated.
- **API routes** (`config/urls.py` → `/api/`): DRF router `IncidentViewSet` with
  `timeline`, `status`, `rca` actions; webhook stubs `/api/webhooks/cloudwatch/`,
  `/api/webhooks/deploy/`, `/api/webhooks/slack/` (return 202/501 placeholders);
  `/api/health/`; `/admin/`.
- **tasks.py**: `maybe_run_rca` (debounce-token check from arch §9.2) and
  `run_rca_for_incident` stub.
- **Dockerfile**: `python:3.14-slim`, install requirements-dev, non-root user,
  default CMD `uvicorn config.asgi:application --host 0.0.0.0 --port 8000`.
- **docker-compose.yml**: `db` (postgres:17, healthcheck, volume), `redis` (redis:7),
  `web` (uvicorn `--reload`, bind-mount source, port 8000, depends_on healthy db),
  `worker` (`celery -A config worker`), `beat` (`celery -A config beat` with
  django_celery_beat scheduler), `localstack` under `profiles: ["aws"]` (optional).
  All read `.env`.
- **.env.example**: every README env var with local-dev defaults
  (`DATABASE_URL=postgres://incident:incident@db:5432/incident`, `REDIS_URL=redis://redis:6379/0`).
- **CLAUDE.md**: project overview (pointer to architecture.md), local venv setup on Windows
  (`py -3.14`), docker compose commands, migrations, running tests (docker and local),
  lint (`ruff check`), layout summary, conventions (idempotent ingestion, no direct
  AlertEvent→RCA calls, secrets only via env).

## Verification
1. `py -3.14 -m venv .venv && .venv/Scripts/pip install -r requirements-dev.txt`
2. `.venv/Scripts/python manage.py check` and `makemigrations --check` after generating initial migration.
3. `docker compose up -d --build db redis web worker` → `docker compose exec web python manage.py migrate`
   → `curl localhost:8000/api/health/` returns 200 and `/api/incidents/` responds.
4. `docker compose exec web pytest` passes (model creation, incident API list/create, health).
5. `ruff check .` clean.
(If Python 3.14 wheels are missing for any dependency, fall back to 3.13 for the image/venv.)
