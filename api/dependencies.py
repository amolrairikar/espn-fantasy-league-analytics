"""Module containing shared dependencies across API."""

import json
import logging
import os
from pathlib import Path
import time
from typing import Any, Optional

import boto3
import botocore.exceptions
from boto3.dynamodb.types import TypeDeserializer
from dotenv import load_dotenv
from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from api.models import APIResponse


class JsonFormatter(logging.Formatter):
    """Class to format logs in JSON format."""

    def format(self, record) -> str:
        """
        Format the log record as a JSON object.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: JSON formatted log string.
        """
        log_object = {
            "timestamp": int(time.time() * 1000),
            "level": record.levelname,
            "message": record.getMessage(),
            "function": record.funcName,
        }
        return json.dumps(log_object)


# Set up JSON logger for API
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.handlers = [handler]

BASE_PATH = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_PATH / ".env")

dynamodb_client = boto3.client("dynamodb", region_name="us-east-1")
table_name = os.getenv("DYNAMODB_TABLE_NAME", "fantasy-recap-app-db-dev")
deserializer = TypeDeserializer()

API_KEY = os.getenv("API_KEY")
if API_KEY is None:
    error_message = "API_KEY environment variable not set."
    logger.error(error_message)
    raise RuntimeError(error_message)
API_KEY_NAME = "x-api-key"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_api_key(api_key_header: str = Security(api_key_header)):
    """
    Dependency function to return the API key from the request header.
    API Gateway will automatically reject requests with a 403 Forbidden error
    if an API key is not provided.
    """
    return api_key_header


def build_api_request_headers(
    privacy: str, cookies: dict[str, Optional[str]]
) -> Optional[dict]:
    """
    Builds headers for API requests sent to fantasy platform APIs.

    Args:
        data (LeagueMetadata): The league information (ID, cookies, platform).

    Returns:
        dict (str, str): A dictionary with cookies in the request header
    """
    if privacy == "private":
        if not (cookies["espn_s2"] and cookies["swid"]):
            raise HTTPException(
                status_code=400,
                detail="Missing required espn_s2 and swid cookies.",
            )
        return {"Cookie": f"espn_s2={cookies['espn_s2']}; SWID={cookies['swid']};"}
    return {}


def filter_dynamodb_response(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Filters and deserializes DynamoDB query response items.

    Args:
        response (dict): The raw response from DynamoDB.

    Returns:
        list[dict]: A list of deserialized items.
    """
    items = [
        {
            k: deserializer.deserialize(v)
            for k, v in sorted(item.items())
            if k not in ("PK", "SK") and not k.endswith(("PK", "SK"))
        }
        for item in response.get("Items", [])
    ]
    return items


def query_dynamodb(pk: str, sk_prefix: str) -> APIResponse:
    """Wrapper to try a DynamoDB query and handle exceptions."""
    try:
        response = dynamodb_client.query(
            TableName=table_name,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": pk},
                ":sk_prefix": {"S": sk_prefix},
            },
        )
        items = filter_dynamodb_response(response=response)
        if not items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No entries found for pk {pk} and sk_prefix {sk_prefix}",
            )
        return APIResponse(
            detail=f"Found records for pk {pk} and sk_prefix {sk_prefix}",
            data=items,
        )
    except botocore.exceptions.ClientError as e:
        logger.exception("Unexpected error while querying DynamoDB: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


def query_with_handling(fn, *args, **kwargs):
    """Wrapper to try a DynamoDB query and handle ClientError exceptions."""
    try:
        return fn(*args, **kwargs)
    except botocore.exceptions.ClientError as e:
        logger.exception("Unexpected error while getting matchups")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
