"""Common utility to query data from DynamoDB."""

from typing import Any, Dict, List, Optional, Tuple

import requests

from common_utils.logging_config import logger
from common_utils.retryable_request_session import create_retry_session

session = create_retry_session()


def get_base_api_url(
    season: int,
    league_id: str,
) -> str:
    """
    Get the base API URL for ESPN fantasy football league data. The API URL structure changed in 2018.

    Args:
        season (int): The NFL season year.
        league_id (str): The unique ID of the fantasy football league.

    Returns:
        str: The base API URL.
    """
    if season >= 2018:
        return f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}"
    return f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/leagueHistory/{league_id}"


def make_espn_api_request(
    season: int,
    league_id: str,
    params: Dict[str, str] | List[Tuple[str, str]],
    swid_cookie: Optional[str] = None,
    espn_s2_cookie: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Make an API request to the ESPN fantasy football league API.

    Args:
        season (int): The NFL season year.
        league_id (str): The unique ID of the fantasy football league.
        params (dict | list): The query parameters for the API request.
        swid_cookie (Optional[str]): The SWID cookie for authentication.
        espn_s2_cookie (Optional[str]): The ESPN S2 cookie for authentication.
        **kwargs: Additional keyword arguments for the API request. Current supported
            arguments include 'headers'.

    Returns:
        dict: The JSON response from the API.

    Raises:
        requests.RequestException: If an error occurs while making the API request.
    """
    base_url = get_base_api_url(season=season, league_id=league_id)
    logger.info("Making request to URL: %s", base_url)
    try:
        if season >= 2018:
            if swid_cookie and espn_s2_cookie:
                response = session.get(
                    url=base_url,
                    params=params,
                    headers=kwargs.get("headers", {}),
                    cookies={"SWID": swid_cookie, "espn_s2": espn_s2_cookie},
                )
                response.raise_for_status()
                return response.json()
            else:
                response = session.get(
                    url=base_url,
                    params=params,
                    headers=kwargs.get("headers", {}),
                )
                response.raise_for_status()
                return response.json()

        # For seasons < 2018, the response dict object is wrapped in a list
        if swid_cookie and espn_s2_cookie:
            response = session.get(
                url=base_url,
                params=params,
                headers=kwargs.get("headers", {}),
                cookies={"SWID": swid_cookie, "espn_s2": espn_s2_cookie},
            )
            response.raise_for_status()
            return response.json()[0]
        else:
            response = session.get(
                url=base_url,
                params=params,
                headers=kwargs.get("headers", {}),
            )
            response.raise_for_status()
            return response.json()[0]

    except requests.RequestException:
        logger.exception(
            "Error while making ESPN API request to URL: %s with params: %s",
            base_url,
            params,
        )
        raise
