"""Module containing shared dependencies across API."""

import logging
import os
from pathlib import Path
from typing import Optional

import boto3
from boto3.dynamodb.types import TypeDeserializer
from dotenv import load_dotenv
from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

# Set up standardized logger for entire API
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(filename)s -  %(lineno)d - %(message)s"
)
console_handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(console_handler)

BASE_PATH = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_PATH / ".env")

dynamodb_client = boto3.client("dynamodb")
table_name = os.getenv("DYNAMODB_TABLE_NAME", "fantasy-analytics-app-db")
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
