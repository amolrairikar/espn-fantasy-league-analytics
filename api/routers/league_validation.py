"""FastAPI router for league metadata endpoints."""

import requests
from fastapi import APIRouter, Depends

from api.dependencies import (
    build_api_request_headers,
    get_api_key,
    logger,
)

router = APIRouter(
    prefix="/validate-league",
    dependencies=[Depends(get_api_key)],
)


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
