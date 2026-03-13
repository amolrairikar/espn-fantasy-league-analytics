"""Module containing shared dependencies across API."""

import json
import logging
import os
import requests
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException, Query


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


def validate_espn_credentials(
    league_id: str,
    season: str,
    swid_cookie: str,
    espn_s2_cookie: str,
) -> None:
    """
    Validates ESPN credentials by executing a simple Fantasy Football API request.

    Args:
        league_id (str): Unique ID for the league.
        season (str): Season to validate league information for.
        swid_cookie (str): SWID cookie from browser cookies.
        espn_s2_cookie (str): ESPN S2 cookie from browser cookies.
    """
    url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}"
    headers = {}
    headers = build_api_request_headers(
        cookies={
            "swid": swid_cookie,
            "espn_s2": espn_s2_cookie,
        },
    )
    logger.info("API headers: %s", headers)
    response = requests.get(url=url, headers=headers)
    response.raise_for_status()


def verify_espn_access(
    league_id: str = Query(description="Unique ID for the league."),
    season: str = Query(description="Season to validate league information for."),
    swid_cookie: str = Query(
        default=None, description="SWID cookie from browser cookies."
    ),
    espn_s2_cookie: str = Query(
        default=None, description="ESPN S2 cookie from browser cookies."
    ),
) -> None:
    """
    Wrapper dependency to validate ESPN credentials.

    Args:
        league_id (str): Unique ID for the league.
        season (str): Season to validate league information for.
        swid_cookie (str): SWID cookie from browser cookies.
        espn_s2_cookie (str): ESPN S2 cookie from browser cookies.
    """
    validate_espn_credentials(
        league_id=league_id,
        season=season,
        swid_cookie=swid_cookie,
        espn_s2_cookie=espn_s2_cookie,
    )
