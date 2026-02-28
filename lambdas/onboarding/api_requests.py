"""
Module for making ESPN Fantasy Football API requests to fetch league data.
"""

from typing import Optional

from utils.logging_config import logger
from utils.espn_api_request import make_espn_api_request


def get_league_members_and_teams(
    league_id: str,
    platform: str,
    season: str,
    swid_cookie: Optional[str] = None,
    espn_s2_cookie: Optional[str] = None,
) -> tuple[list, list]:
    """
    Fetch league members for a fantasy football league in a given season.

    Args:
        league_id: The unique ID of the fantasy football league.
        platform: The platform the fantasy football league is on (e.g., ESPN, Sleeper).
        season: The NFL season to get data for.
        swid_cookie: The SWID cookie used for getting ESPN private league data.
        espn_s2_cookie: The espn S2 cookie used for getting ESPN private league data.

    Returns:
        tuple: A pair of lists containing a mapping of info of league members and league teams.

    Raises:
        ValueError: If unsupported platform is specified, or if a required ESPN cookie is missing.
        Exception: If uncaught exception occurs.
    """
    if platform == "ESPN":
        if not swid_cookie or not espn_s2_cookie:
            raise ValueError("Missing required SWID and/or ESPN S2 cookies")

        # Send appropriate query params based on the season
        params = {
            "view": "mTeam",
        }
        if int(season) < 2018:
            params["seasonId"] = season

        response = make_espn_api_request(
            season=int(season),
            league_id=league_id,
            params=params,
            swid_cookie=swid_cookie,
            espn_s2_cookie=espn_s2_cookie,
        )
        logger.info("Successfully got league member and team info")

        # Extract members and teams from response
        members = response.get("members", [])
        teams = response.get("teams", [])
        logger.info(
            "Found %d members and %d teams in league for %s season",
            len(members),
            len(teams),
            season,
        )
        return members, teams
    else:
        raise ValueError("Unsupported platform. Only ESPN is currently supported.")
