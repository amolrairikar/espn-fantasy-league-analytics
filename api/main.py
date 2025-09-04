"""Main module for API with all endpoints."""

import os
from pathlib import Path

import boto3
from fastapi import FastAPI, status, Security, Depends
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from mangum import Mangum
from dotenv import load_dotenv

BASE_PATH = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_PATH / ".env")

API_KEY = os.environ["API_KEY"]
API_KEY_NAME = "X-API-Key"

dynamodb_client = boto3.client("dynamodb")
table_name = "fantasy-analytics-app-db"

app = FastAPI()

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_api_key(api_key_header: str = Security(api_key_header)):
    """Dependency function to return the API key from the request header. This assumes
    that API Gateway will automatically reject requests with a 403 Forbidden error
    if an API key is not provided.
    """
    return api_key_header


@app.get("/health")
def health_check(_: str = Depends(get_api_key)):
    """Simple health check endpoint."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy"},
    )


handler = Mangum(app)
