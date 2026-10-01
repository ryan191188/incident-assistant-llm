"""Shared boto3 client factory (supports localstack via AWS_ENDPOINT_URL)."""

import boto3
from django.conf import settings


def client(service: str):
    return boto3.client(
        service, region_name=settings.AWS_REGION, endpoint_url=settings.AWS_ENDPOINT_URL
    )
