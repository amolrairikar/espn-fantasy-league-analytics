"""Script to fetch members within an ESPN fantasy football league."""

import os
from typing import Optional

import pandas as pd

from common_utils.batch_write_dynamodb import batch_write_to_dynamodb
from common_utils.espn_api_request import make_espn_api_request
from common_utils.logging_config import logger

DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "fantasy-recap-app-db-dev")


def get_league_members_and_teams(
    league_id: str,
    platform: str,
    privacy: str,
    season: str,
    swid_cookie: Optional[str] = None,
    espn_s2_cookie: Optional[str] = None,
) -> tuple[list, list]:
    """
    Fetch league members for a fantasy football league in a given season.

    Args:
        league_id (str): The unique ID of the fantasy football league.
        platform (str): The platform the fantasy football league is on (e.g., ESPN, Sleeper).
        privacy (str): The privacy setting of the league (e.g., public, private).
        season (str): The NFL season to get data for.
        swid_cookie (Optional[str]): The SWID cookie used for getting ESPN private league data.
        espn_s2_cookie (Optional[str]): The espn S2 cookie used for getting ESPN private league data.

    Returns:
        tuple: A pair of lists containing a mapping of info of league members and league teams.

    Raises:
        ValueError: If unsupported platform is specified, or if a required ESPN cookie is missing.
        Exception: If uncaught exception occurs.
    """
    if platform == "ESPN":
        if privacy == "private" and (not swid_cookie or not espn_s2_cookie):
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
        logger.info("Found %d members and %d teams in league", len(members), len(teams))
        return members, teams
    else:
        raise ValueError("Unsupported platform. Only ESPN is currently supported.")


def join_league_members_to_teams(
    members: list[dict[str, str]], teams: list[dict[str, str]]
) -> list:
    """
    Helper function to join teams and members responses into one data structure.

    Args:
        members (list[dict[str, str]]): A list of dictionaries containing info
            about each league member.
        teams (list[dict[str, str]]): A list of dictionaries containing info
            about each league team.

    Returns:
        list: A list of dictionaries with each dictionary containing combined
            details for a league member and their associated team.

    Raises:
        ValueError: If either list of members or list of teams is empty.
    """
    # Load data with relevant columns
    df_members = pd.DataFrame(data=members)
    df_members_refined = df_members[["displayName", "firstName", "lastName", "id"]]
    df_teams = pd.DataFrame(data=teams)
    df_teams_refined = df_teams[["abbrev", "id", "name", "owners"]]

    # Creates a row per owner for a team
    df_teams_exploded = df_teams_refined.explode(column="owners")

    # Join members and teams data
    df_members_and_teams = pd.merge(
        left=df_members_refined,
        right=df_teams_exploded,
        how="inner",
        left_on="id",
        right_on="owners",
    )

    # Refine joined data
    df_members_and_teams = df_members_and_teams.rename(
        columns={"id_x": "memberId", "id_y": "teamId", "name": "teamName"}
    )
    df_members_and_teams = df_members_and_teams.drop(columns=["owners"])
    df_consolidated = df_members_and_teams.groupby(
        ["firstName", "lastName", "abbrev", "teamId", "teamName"], as_index=False
    ).agg(lambda x: list(x.unique()))

    dict_members_and_teams = df_consolidated.to_dict(orient="records")
    return dict_members_and_teams


def lambda_handler(event, context):
    """Lambda handler function to get league members and teams."""
    logger.info("Received event: %s", event)
    league_id = event["leagueId"]
    platform = event["platform"]
    privacy = event["privacy"]
    swid_cookie = event["swidCookie"]
    espn_s2_cookie = event["espnS2Cookie"]
    season = event["season"]

    members, teams = get_league_members_and_teams(
        league_id=league_id,
        platform=platform,
        privacy=privacy,
        season=season,
        swid_cookie=swid_cookie,
        espn_s2_cookie=espn_s2_cookie,
    )
    if not members or not teams:
        raise ValueError("'members' or 'teams' lists must not be empty.")

    logger.info("Creating consolidated members and teams dataframe")
    output_data = join_league_members_to_teams(members=members, teams=teams)
    batched_objects = []
    for item in output_data:
        batched_objects.append(
            {
                "PutRequest": {
                    "Item": {
                        "PK": {
                            "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"
                        },
                        "SK": {"S": f"TEAM#{item['teamId']}"},
                        "GSI5PK": {"S": f"LEAGUE#{league_id}"},
                        "GSI5SK": {"S": "FOR_DELETION_USE_ONLY"},
                        "owner_full_name": {
                            "S": f"{item['firstName']} {item['lastName']}"
                        },
                        "owner_first_name": {"S": item["firstName"]},
                        "owner_last_name": {"S": item["lastName"]},
                        "owner_id": {
                            "L": [{"S": member_id} for member_id in item["memberId"]]
                        },
                        "team_id": {"S": str(item["teamId"])},
                        "team_name": {"S": item["teamName"]},
                        "team_abbreviation": {"S": item["abbrev"]},
                    }
                }
            }
        )
    batch_write_to_dynamodb(
        batched_objects=batched_objects, table_name=DYNAMODB_TABLE_NAME
    )
    logger.info("Successfully wrote data to DynamoDB.")
