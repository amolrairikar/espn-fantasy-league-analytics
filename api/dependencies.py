"""Module containing shared dependencies across API."""

import json
import logging
import os
from pathlib import Path
import time

from dotenv import load_dotenv
from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader


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

ENVIRONMENT = os.environ["ENVIRONMENT"]

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


def build_api_request_headers(cookies: dict[str, str]) -> dict[str, str]:
    """
    Builds headers for API requests sent to fantasy platform APIs.

    Args:
        cookies (dict[str, Optional[str]]): A dictionary containing the espn_s2 and swid cookies.

    Returns:
        dict (str, str): A dictionary with cookies in the request header
    """
    if not (cookies["espn_s2"] and cookies["swid"]):
        raise HTTPException(
            status_code=400,
            detail="Missing required espn_s2 and swid cookies.",
        )
    return {"Cookie": f"espn_s2={cookies['espn_s2']}; SWID={cookies['swid']};"}
