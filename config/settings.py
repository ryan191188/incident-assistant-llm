"""Django settings for the Production Incident Assistant.

All configuration is environment-driven; see .env.example and README.md.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env", overwrite=False)

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "0.0.0.0"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "channels",
    "incidents",
    "ingestion",
    "rca",
    "integrations.slack",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": env.db(
        "DATABASE_URL", default="postgres://incident:incident@localhost:5433/incident"
    ),
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Django REST Framework ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

# --- Redis / Channels / Celery ---
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    },
}

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_ACKS_LATE = True
CELERY_TIMEZONE = TIME_ZONE
# autodiscover_tasks() only finds `<app>/tasks.py`; ingestion tasks live in per-source modules.
CELERY_IMPORTS = [
    "ingestion.cloudwatch",
    "ingestion.cloudtrail",
    "ingestion.logs",
    "ingestion.traces",
    "ingestion.deploys",
]
# Periodic ingestion schedule (ARCHITECTURE.md §3.1), run by the `beat` compose service.
# Tasks are stubs for now; they only need to exist in the worker when beat enqueues them.
CELERY_BEAT_SCHEDULE = {
    "poll-cloudwatch-alarms": {
        "task": "ingestion.cloudwatch.poll_alarms",
        "schedule": 60.0,
    },
    "poll-cloudtrail-events": {
        "task": "ingestion.cloudtrail.poll_cloudtrail_events",
        "schedule": 180.0,
    },
    "poll-log-groups": {
        "task": "ingestion.logs.poll_log_groups",
        "schedule": 60.0,
    },
    "poll-error-traces": {
        "task": "ingestion.traces.poll_error_traces",
        "schedule": 45.0,
    },
    "poll-deploy-queue": {
        "task": "ingestion.deploys.poll_deploy_queue",
        "schedule": 60.0,
    },
}

# --- AWS ---
AWS_REGION = env("AWS_REGION", default="us-east-1")
AWS_ENDPOINT_URL = env("AWS_ENDPOINT_URL", default=None)  # e.g. localstack
CLOUDWATCH_LOG_GROUPS = env.list("CLOUDWATCH_LOG_GROUPS", default=[])
RDS_TRACE_DB_URL = env("RDS_TRACE_DB_URL", default="")
DEPLOY_EVENTBRIDGE_QUEUE_URL = env("DEPLOY_EVENTBRIDGE_QUEUE_URL", default="")
DEPLOY_AMI_COMMIT_TAG_KEY = env("DEPLOY_AMI_COMMIT_TAG_KEY", default="CommitSHA")
DEPLOY_WEBHOOK_SECRET = env("DEPLOY_WEBHOOK_SECRET", default="")
GITHUB_TOKEN = env("GITHUB_TOKEN", default="")
GIT_PROVIDER_API_URL = env("GIT_PROVIDER_API_URL", default="https://api.github.com")

# --- Claude ---
CLAUDE_API_KEY = env("CLAUDE_API_KEY", default="")
CLAUDE_MODEL = env("CLAUDE_MODEL", default="claude-sonnet-4-6")

# --- Slack ---
SLACK_BOT_TOKEN = env("SLACK_BOT_TOKEN", default="")
SLACK_SIGNING_SECRET = env("SLACK_SIGNING_SECRET", default="")
SLACK_DEFAULT_CHANNEL = env("SLACK_DEFAULT_CHANNEL", default="#incidents")

# --- RCA cost control (ARCHITECTURE.md §9.8) ---
RCA_DEBOUNCE_SECONDS = env.int("RCA_DEBOUNCE_SECONDS", default=45)
RCA_MIN_INTERVAL_SECONDS = env.int("RCA_MIN_INTERVAL_SECONDS", default=120)
RCA_MAX_RUNS_PER_INCIDENT = env.int("RCA_MAX_RUNS_PER_INCIDENT", default=5)
LLM_CIRCUIT_BREAKER_THRESHOLD = env.int("LLM_CIRCUIT_BREAKER_THRESHOLD", default=20)
RCA_CACHE_TTL_SECONDS = env.int("RCA_CACHE_TTL_SECONDS", default=3600)
RCA_MAX_CONTEXT_TOKENS = env.int("RCA_MAX_CONTEXT_TOKENS", default=50_000)
RCA_MAX_OUTPUT_TOKENS = env.int("RCA_MAX_OUTPUT_TOKENS", default=2_000)
CORRELATION_DEDUP_WINDOW_SECONDS = env.int("CORRELATION_DEDUP_WINDOW_SECONDS", default=600)
CORRELATION_LOOKBACK_SECONDS = env.int("CORRELATION_LOOKBACK_SECONDS", default=900)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
}
