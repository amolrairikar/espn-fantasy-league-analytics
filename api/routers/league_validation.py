"""FastAPI router for league metadata endpoints."""

import requests
from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import (
    build_api_request_headers,
    get_api_key,
    logger,
)
from api.models import APIResponse

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


@router.get(path="", status_code=status.HTTP_200_OK, response_model_exclude_none=True)
def validate_league_info(
    league_id: str = Query(description="Unique ID for the league."),
    platform: str = Query(description="Platform the fantasy league is on."),
    season: str = Query(description="Season to validate league information for."),
    swid_cookie: str = Query(
        default=None, description="SWID cookie from browser cookies."
    ),
    espn_s2_cookie: str = Query(
        default=None, description="ESPN S2 cookie from browser cookies."
    ),
) -> APIResponse:
    """
    Validates that the provided league information links to a valid league,
    and that cookie credentials work with API requests.

    Args:
        season (str): The most recent season the league was active for.
        data (LeagueMetadata): The league information (ID, cookies, platform) to validate.

    Returns:
        APIResponse: A JSON response with a message field indicating success/failure
            and an optional data field to capture additional details.

    Raises:
        HTTPException: 400, 401, 404, or 500 errors if an exception occurs.
    """
    if platform == "ESPN":
        try:
            logger.info("Validating ESPN league")
            validate_espn_credentials(
                league_id=league_id,
                season=season,
                swid_cookie=swid_cookie,
                espn_s2_cookie=espn_s2_cookie,
            )
            log_message = "League information validated successfully."
            logger.info(log_message)
            return APIResponse(detail=log_message)
        except requests.RequestException as e:
            status_code = getattr(e.response, "status_code", None)
            if not status_code:
                logger.exception(
                    "Unexpected error while validating league information."
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Internal server error: {str(e)}",
                )
            logger.exception("Error validating league: %s", str(e))
            raise HTTPException(
                status_code=status_code,
                detail=str(e),
            )
    else:
        log_message = "Platforms besides ESPN not currently supported."
        logger.warning(log_message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=log_message,
        )
