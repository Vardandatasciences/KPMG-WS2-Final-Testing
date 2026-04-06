"""Build AWS credential dict for S3 microservice export payloads from environment only."""
from __future__ import annotations

import os
from typing import Dict


def aws_credentials_for_microservice_export() -> Dict[str, str]:
    key = os.environ.get("AWS_ACCESS_KEY_ID", "").strip()
    secret = os.environ.get("AWS_SECRET_ACCESS_KEY", "").strip()
    region = (
        os.environ.get("AWS_REGION", "").strip()
        or os.environ.get("AWS_DEFAULT_REGION", "").strip()
        or "ap-south-1"
    )
    bucket = (
        os.environ.get("AWS_STORAGE_BUCKET_NAME", "").strip()
        or os.environ.get("AWS_BUCKET_NAME", "").strip()
    )
    if not key or not secret or not bucket:
        raise ValueError(
            "S3 microservice export requires AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, "
            "and AWS_STORAGE_BUCKET_NAME or AWS_BUCKET_NAME in the environment."
        )
    return {
        "awsAccessKey": key,
        "awsSecretKey": secret,
        "awsRegion": region,
        "bucketName": bucket,
    }
