"""Module containing shared dependencies across API."""

import json
import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv


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
bucket_env_add = "-dev" if ENVIRONMENT == "DEV" else ""
BUCKET_NAME = (
    f"{os.environ['ACCOUNT_NUMBER']}-fantasy-recap-app-database{bucket_env_add}"
)
