"""
Module for making ESPN Fantasy Football API requests to fetch league data.
"""

import json
from typing import Any, Optional

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


def get_league_scores(
    league_id: str,
    platform: str,
    season: str,
    swid_cookie: Optional[str],
    espn_s2_cookie: Optional[str],
) -> list:
    """
    Fetch league matchup scores for a fantasy football league in a given season.

    Args:
        league_id (str): The unique ID of the fantasy football league.
        platform (str): The platform the fantasy football league is on (e.g., ESPN, Sleeper).
        season (str): The NFL season to get data for.
        swid_cookie (Optional[str]): The SWID cookie used for getting ESPN private league data.
        espn_s2_cookie (Optional[str]): The espn S2 cookie used for getting ESPN private league data.

    Returns:
        list: A list containing data for each matchup in the season.

    Raises:
        ValueError: If unsupported platform is specified, or if a required ESPN cookie is missing.
        requests.RequestException: If an error occurs while making API request.
        Exception: If uncaught exception occurs.
    """
    if platform == "ESPN":
        if not swid_cookie or not espn_s2_cookie:
            raise ValueError("Missing required SWID and/or ESPN S2 cookies")
        weeks = range(1, 18, 1) if int(season) < 2021 else range(1, 19, 1)
        scores: list[dict[str, Any]] = []
        for week in weeks:
            base_params = [
                ("scoringPeriodId", str(week)),
                ("view", "mBoxscore"),
                ("view", "mMatchupScore"),
            ]
            if int(season) >= 2018:
                params = [*base_params]
            else:
                params = [("seasonId", season), *base_params]
            response = make_espn_api_request(
                season=int(season),
                league_id=league_id,
                params=params,
                swid_cookie=swid_cookie,
                espn_s2_cookie=espn_s2_cookie,
            )
            logger.info("Successfully got league score info")
            weekly_scores = response.get("schedule", [])
            filtered_weekly_scores = [
                d for d in weekly_scores if d.get("matchupPeriodId") == week
            ]
            logger.info(
                "Found %d matchups in league for %s season week %s",
                len(filtered_weekly_scores),
                season,
                week,
            )
            scores.extend(filtered_weekly_scores)
        return scores
    else:
        raise ValueError("Unsupported platform. Only ESPN is currently supported.")


def get_league_lineup_settings(
    league_id: str,
    platform: str,
    season: str,
    swid_cookie: Optional[str],
    espn_s2_cookie: Optional[str],
) -> dict[str, int]:
    """
    Fetch league lineup settings for a fantasy football league in a given season.

    Args:
        league_id (str): The unique ID of the fantasy football league.
        platform (str): The platform the fantasy football league is on (e.g., ESPN, Sleeper).
        season (str): The NFL season to get data for.
        swid_cookie (Optional[str]): The SWID cookie used for getting ESPN private league data.
        espn_s2_cookie (Optional[str]): The espn S2 cookie used for getting ESPN private league data.

    Returns:
        dict: A mapping of position ID to number of starting spots.

    Raises:
        ValueError: If unsupported platform is specified, or if a required ESPN cookie is missing.
        requests.RequestException: If an error occurs while making API request.
        Exception: If uncaught exception occurs.
    """
    if platform == "ESPN":
        if not swid_cookie or not espn_s2_cookie:
            raise ValueError("Missing required SWID and/or ESPN S2 cookies")
        settings: dict[str, int] = {}
        base_params = [
            ("view", "mSettings"),
            ("view", "mTeam"),
        ]
        if int(season) >= 2018:
            params = [*base_params]
        else:
            params = [("seasonId", season), *base_params]
        response = make_espn_api_request(
            season=int(season),
            league_id=league_id,
            params=params,
            swid_cookie=swid_cookie,
            espn_s2_cookie=espn_s2_cookie,
        )
        logger.info("Successfully got league settings info")
        settings = (
            response.get("settings", {})
            .get("rosterSettings", {})
            .get("lineupSlotCounts", {})
        )
        return settings
    else:
        raise ValueError("Unsupported platform. Only ESPN is currently supported.")


def get_draft_results(
    league_id: str,
    platform: str,
    season: str,
    swid_cookie: Optional[str],
    espn_s2_cookie: Optional[str],
) -> list:
    """
    Fetch draft results for a fantasy football league in a given season.

    Args:
        league_id (str): The unique ID of the fantasy football league.
        platform (str): The platform the fantasy football league is on (e.g., ESPN, Sleeper).
        season (str): The NFL season to get data for.
        swid_cookie (Optional[str]): The SWID cookie used for getting ESPN private league data.
        espn_s2_cookie (Optional[str]): The espn S2 cookie used for getting ESPN private league data.

    Returns:
        list: A list containing data for each draft pick in the season's draft.

    Raises:
        ValueError: If unsupported platform is specified, or if a required ESPN cookie is missing.
        requests.RequestException: If an error occurs while making API request.
        Exception: If uncaught exception occurs.
    """
    if platform == "ESPN":
        if not swid_cookie or not espn_s2_cookie:
            raise ValueError("Missing required SWID and/or ESPN S2 cookies")
        base_params = [
            ("view", "mDraftDetail"),
        ]
        if int(season) >= 2018:
            params = [*base_params]
        else:
            params = [("seasonId", season), *base_params]
        response = make_espn_api_request(
            season=int(season),
            league_id=league_id,
            params=params,
            swid_cookie=swid_cookie,
            espn_s2_cookie=espn_s2_cookie,
        )
        logger.info("Successfully got league draft info")
        season_id = response["draftDetail"].get("seasonId")
        all_picks = response["draftDetail"].get("picks", [])
        for pick in all_picks:
            pick["season"] = season_id
        return all_picks
    else:
        raise ValueError("Unsupported platform. Only ESPN is currently supported.")


def get_player_season_totals(
    league_id: str,
    platform: str,
    season: str,
    swid_cookie: Optional[str],
    espn_s2_cookie: Optional[str],
) -> list:
    """
    Fetch player fantasy scoring totals for a fantasy football league in a given season.

    Args:
        league_id (str): The unique ID of the fantasy football league.
        platform (str): The platform the fantasy football league is on (e.g., ESPN, Sleeper).
        season (str): The NFL season to get data for.
        swid_cookie (Optional[str]): The SWID cookie used for getting ESPN private league data.
        espn_s2_cookie (Optional[str]): The espn S2 cookie used for getting ESPN private league data.

    Returns:
        list: A list containing fantasy scoring totals for each player.

    Raises:
        ValueError: If unsupported platform is specified, or if a required ESPN cookie is missing.
        requests.RequestException: If an error occurs while making API request.
        Exception: If uncaught exception occurs.
    """
    if platform == "ESPN":
        if not swid_cookie or not espn_s2_cookie:
            raise ValueError("Missing required SWID and/or ESPN S2 cookies")
        base_params = [
            ("view", "kona_player_info"),
        ]
        headers = {
            "X-Fantasy-Filter": json.dumps(
                {
                    "players": {
                        "limit": 1500,
                        "sortAppliedStatTotal": {
                            "sortAsc": False,
                            "sortPriority": 2,
                            "value": "002024",
                        },
                    }
                }
            )
        }
        if int(season) >= 2018:
            params = [*base_params]
        else:
            params = [("seasonId", season), *base_params]
        response = make_espn_api_request(
            season=int(season),
            league_id=league_id,
            params=params,
            headers=headers,
            swid_cookie=swid_cookie,
            espn_s2_cookie=espn_s2_cookie,
        )
        logger.info("Successfully got player scoring totals")
        player_totals = response.get("players", [])
        return player_totals
    else:
        raise ValueError("Unsupported platform. Only ESPN is currently supported.")
