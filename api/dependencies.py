"""Module containing shared dependencies across API."""

import os
from pathlib import Path

import boto3
from dotenv import load_dotenv
from fastapi import Security
from fastapi.security.api_key import APIKeyHeader

BASE_PATH = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_PATH / ".env")

dynamodb_client = boto3.client("dynamodb")
table_name = "fantasy-analytics-app-db"

API_KEY = os.environ["API_KEY"]
API_KEY_NAME = "X-API-Key"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_api_key(api_key_header: str = Security(api_key_header)):
    """Dependency function to return the API key from the request header. This assumes
    that API Gateway will automatically reject requests with a 403 Forbidden error
    if an API key is not provided.
    """
    return api_key_header
