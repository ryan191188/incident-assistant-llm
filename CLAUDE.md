# CLAUDE.md

Production Incident Assistant: Django 6.1 (ASGI, served by **uvicorn**) + DRF + Channels,
PostgreSQL, Celery/Redis, Claude for RCA. Read `architecture.md` before designing features;
section numbers (§3.3, §9.2, …) are referenced in docstrings.

## Build & run (Docker — primary workflow)

```bash
cp .env.example .env                 # first time only
docker compose up -d --build         # web (uvicorn --reload), worker, beat, db, redis
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose --profile aws up -d localstack   # optional AWS mocks; set AWS_ENDPOINT_URL=http://localstack:4566
docker compose logs -f web worker beat
```

- API `http://localhost:8000/api/`, health `/api/health/`, admin `/admin/`,
  WebSocket `ws://localhost:8000/ws/incidents/<id>/`.
- Postgres is exposed on host port **5433** (5432 is taken by a native Windows Postgres
  service on this machine). Redis on 6379.
- `beat` is plain `celery beat`; the schedule is `CELERY_BEAT_SCHEDULE` in
  `config/settings.py` (no django-celery-beat). Restart `worker` and `beat` after changing
  tasks or the schedule; `web` hot-reloads.
- Ingestion tasks live in `ingestion/<source>.py`, not `tasks.py`, so any new module must be
  added to `CELERY_IMPORTS` or the worker rejects it with `KeyError`.

## Local virtualenv (Windows)

The default `python` on this machine is 3.9, which is too old. Use the launcher:

```bash
py -3.14 -m venv .venv
.venv/Scripts/pip install -r requirements-dev.txt
```

Running Django or pytest from the host needs the compose `db`/`redis` up and host URLs:

```bash
export DATABASE_URL=postgres://incident:incident@localhost:5433/incident
export REDIS_URL=redis://localhost:6379/0
.venv/Scripts/python manage.py runserver   # or: .venv/Scripts/uvicorn config.asgi:application --reload
```

## Tests & lint

```bash
docker compose exec web pytest                 # full suite (needs Postgres)
docker compose exec web pytest tests/test_api.py -k status
.venv/Scripts/pytest                           # from host, with the env vars above
.venv/Scripts/ruff check . && .venv/Scripts/ruff format .
docker compose exec web python manage.py makemigrations --check --dry-run
```

pytest config (`DJANGO_SETTINGS_MODULE`, `asyncio_mode=auto`) and ruff config are in
`pyproject.toml`. Shared fixtures (`api_client`, `auth_client`, `user`) are in `tests/conftest.py`.

## Layout

- `config/`: settings (all env-driven via django-environ), `asgi.py` (HTTP + Channels
  websocket router), `celery.py`, root `urls.py`.
- `incidents/`: models (§3.2), DRF `IncidentViewSet` (`/api/incidents/`, `timeline`, `status`,
  `rca` actions), `/api/health/`, WebSocket consumer, `correlation.py` (§3.3), `tasks.py`
  (debounced RCA, §9).
- `ingestion/`: one module per source (cloudwatch, cloudtrail, logs, traces, deploys) plus
  `/api/webhooks/{cloudwatch,deploy}/`. `aws.py` is the boto3 client factory (localstack-aware).
- `rca/`: `context_builder.py` (redaction, context hash), `client.py` (Anthropic SDK,
  model from `CLAUDE_MODEL`), `prompts.py`.
- `integrations/slack/`: outbound client + `/api/webhooks/slack/` (signature-verified).
- `tests/`: pytest-django tests.

## Conventions

- Ingestion is idempotent: dedup on each model's unique `source_event_id`.
- Never call RCA directly from an `AlertEvent`. Go through `correlation.correlate_alert` →
  `maybe_run_rca` (debounce token, cooldown, run cap). See architecture §9.
- All log and commit text sent to Claude must pass through `rca.context_builder.redact`.
- Secrets come only from environment variables. `.env` is gitignored; add new vars to
  `.env.example` and `config/settings.py` together.
- Stubbed functions raise `NotImplementedError`, except periodic poll tasks, which log and
  return 0 so beat doesn't flood the worker with errors.
