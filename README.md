# Production Incident Assistant

A Django-based assistant that ingests AWS CloudWatch/CloudTrail alarms, application logs
(gunicorn/nginx), error traces, and deployment/commit history, then uses Claude to
generate root-cause analysis (RCA) for production incidents — with Slack notifications
and a real-time incident dashboard.

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full system design.

## Features

- Automatic incident creation from CloudWatch alarms
- Context aggregation across logs, traces, deployments, and recent commits
- Claude-generated incident summaries, likely root causes, and suggested next steps
- Slack notifications and slash-command status updates
- Real-time incident updates via WebSocket (Django Channels)
- REST API for incidents, timelines, and RCA history

## Tech Stack

- **Backend**: Django, Django REST Framework
- **Real-time**: Django Channels (ASGI)
- **Database**: PostgreSQL
- **Task queue**: Celery + Redis
- **LLM**: Claude API
- **Chat**: Slack
- **Local infra**: Docker Compose
- **Future deploy target**: AWS ECS on Fargate

## Prerequisites

- Python 3.12+
- Django 6.1
- Docker & Docker Compose
- An AWS account with read access to CloudWatch/CloudTrail (or use `localstack` for local dev)
- A Claude API key
- A Slack app/bot token (with a signing secret) for the workspace you want to notify

## Getting Started (Local Development)

1. **Clone and configure environment variables**

   ```bash
   git clone <repo-url>
   cd production-incident-assistant
   cp .env.example .env
   ```

2. **Fill in `.env`** — see [Environment Variables](#environment-variables) below.

3. **Start the stack**

   ```bash
   docker compose up --build
   ```

   This starts: `web` (Django ASGI app), `worker` (Celery), `beat` (Celery Beat),
   `db` (Postgres), `redis`, and `localstack` (optional AWS mocks).

4. **Run migrations**

   ```bash
   docker compose exec web python manage.py migrate
   ```

5. **Create a superuser** (for Django admin access)

   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

6. **Access the app**

   - API: `http://localhost:8000/api/`
   - Admin: `http://localhost:8000/admin/`
   - WebSocket: `ws://localhost:8000/ws/incidents/<id>/`

## Environment Variables

| Variable | Description |
|---|---|
| `DJANGO_SECRET_KEY` | Django secret key |
| `DJANGO_DEBUG` | `True`/`False` |
| `DATABASE_URL` | Postgres connection string |
| `REDIS_URL` | Redis connection string (Celery broker/result backend + channel layer) |
| `AWS_REGION` | AWS region for CloudWatch/CloudTrail |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | AWS credentials (use an IAM role in deployed environments instead) |
| `CLOUDWATCH_LOG_GROUPS` | Comma-separated log groups to poll/subscribe to |
| `RDS_TRACE_DB_URL` | Read-only connection string to the RDS table storing error traces |
| `CLAUDE_API_KEY` | Claude API key |
| `CLAUDE_MODEL` | Defaults to `claude-sonnet-4-6` |
| `SLACK_BOT_TOKEN` | Slack bot OAuth token |
| `SLACK_SIGNING_SECRET` | Used to verify Slack webhook requests |
| `SLACK_DEFAULT_CHANNEL` | Fallback channel for incident notifications |
| `DEPLOY_EVENTBRIDGE_QUEUE_URL` | SQS queue URL fed by the EventBridge rule on ASG `Instance Refresh Succeeded` (current primary deploy signal; auth via IAM, no shared secret). Swaps to a CodePipeline `Pipeline Execution State Change` rule once CI/CD migration happens — see `ARCHITECTURE.md §3.1.1` |
| `DEPLOY_AMI_COMMIT_TAG_KEY` | Tag key used to read the commit SHA off the AMI associated with a succeeded instance refresh (default: `CommitSHA`). Not needed once migrated to CodePipeline, since the SHA comes from the pipeline execution directly |
| `GITHUB_TOKEN` / `GIT_PROVIDER_API_URL` | For fetching recent commit metadata — not needed if source control is CodeCommit (uses IAM via boto3 instead) |
| `DEPLOY_WEBHOOK_SECRET` | Fallback only, for one-off deploys outside the primary flow — bearer-token comparison, not treated as a reliable primary source |

## Project Structure

```
production-incident-assistant/
├── config/                  # Django project settings, asgi.py, celery.py
├── incidents/                # Core app: Incident, AlertEvent, RCAReport models
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── consumers.py          # Channels WebSocket consumers
│   ├── correlation.py        # Correlation engine
│   └── tasks.py               # Celery tasks
├── ingestion/                 # Source-specific ingestion adapters
│   ├── cloudwatch.py
│   ├── cloudtrail.py
│   ├── logs.py                # gunicorn/nginx log consumers
│   ├── traces.py               # RDS trace reader
│   └── deploys.py               # Deployment/commit collector
├── rca/                        # Claude integration
│   ├── context_builder.py
│   ├── client.py
│   └── prompts.py
├── integrations/
│   └── slack/
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── manage.py
├── ARCHITECTURE.md
└── README.md
```

## Running Tests

```bash
docker compose exec web pytest
```

## Slack App Setup

1. Create a Slack app at https://api.slack.com/apps.
2. Enable **Bot Token Scopes**: `chat:write`, `channels:read`, `commands`.
3. Add a slash command (e.g., `/incident`) pointing to
   `https://<your-host>/api/webhooks/slack/`.
4. Enable **Interactivity** with the same request URL.
5. Copy the Bot Token and Signing Secret into `.env`.

## Deployment

Local development uses Docker Compose. Production deployment targets AWS ECS on
Fargate (see [`ARCHITECTURE.md §8`](./ARCHITECTURE.md#8-future-deployment-ecs-on-fargate))
with managed RDS Postgres and ElastiCache Redis. Deployment manifests/Terraform are
tracked separately (see `infra/` once added).

## Roadmap

- [ ] Two-way sync (alarm ack, PagerDuty/Opsgenie status sync)
- [ ] Additional alert sources (Sentry, Datadog, Prometheus/Alertmanager)
- [ ] Historical incident similarity search
- [ ] Auto-drafted postmortem documents

## License

TBD
