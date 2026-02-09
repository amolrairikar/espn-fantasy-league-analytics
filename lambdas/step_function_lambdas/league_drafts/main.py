"""Script to fetch draft results within an ESPN fantasy football league."""

import json
import os
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Any

import boto3
import botocore.exceptions
import pandas as pd
from boto3.dynamodb.types import TypeDeserializer

from common_utils.batch_write_dynamodb import batch_write_to_dynamodb
from common_utils.espn_api_request import make_espn_api_request
from common_utils.logging_config import logger
from common_utils.retryable_request_session import create_retry_session


session = create_retry_session()
deserializer = TypeDeserializer()
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "fantasy-recap-app-db-dev")
POSITION_ID_MAPPING = {
    1: "QB",
    2: "RB",
    3: "WR",
    4: "TE",
    5: "K",
    16: "D/ST",
}

# Mainly used for debugging purposes
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)


def get_teams(league_id: str, platform: str, season: str) -> list:
    """Get a list of all teams in the league for the season."""
    try:
        dynamodb = boto3.client("dynamodb")
        response = dynamodb.query(
            TableName=DYNAMODB_TABLE_NAME,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"},
                ":sk_prefix": {"S": "TEAM#"},
            },
        )
        teams = [
            {
                **{k: deserializer.deserialize(v) for k, v in item.items()},
                "season": season,
            }
            for item in response.get("Items", [])
        ]
        return teams
    except botocore.exceptions.ClientError:
        logger.exception("Unexpected error while fetching league members")
        raise


def get_draft_results(
    league_id: str,
    platform: str,
    privacy: str,
    season: str,
    swid_cookie: Optional[str],
    espn_s2_cookie: Optional[str],
) -> list:
    """
    Fetch draft results for a fantasy football league in a given season.

    Args:
        league_id (str): The unique ID of the fantasy football league.
        platform (str): The platform the fantasy football league is on (e.g., ESPN, Sleeper).
        privacy (str): The privacy setting of the league (e.g., public, private).
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
        if privacy == "private" and (not swid_cookie or not espn_s2_cookie):
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
        all_picks = response["draftDetail"].get("picks", [])
        return all_picks
    else:
        raise ValueError("Unsupported platform. Only ESPN is currently supported.")


def get_player_season_totals(
    league_id: str,
    platform: str,
    privacy: str,
    season: str,
    swid_cookie: Optional[str],
    espn_s2_cookie: Optional[str],
) -> list:
    """
    Fetch player fantasy scoring totals for a fantasy football league in a given season.

    Args:
        league_id (str): The unique ID of the fantasy football league.
        platform (str): The platform the fantasy football league is on (e.g., ESPN, Sleeper).
        privacy (str): The privacy setting of the league (e.g., public, private).
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
        if privacy == "private" and (not swid_cookie or not espn_s2_cookie):
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


def process_player_scoring_totals(
    player_totals: list[dict[str, Any]],
    season: str,
) -> list[dict[str, Any]]:
    """
    Process raw player scoring totals data to get relevant information.

    Args:
        player_totals (list[dict[str, Any]]): List of dictionaries containing fantasy scoring totals
            for each available player in the fantasy league.
        season (str): The NFL season the data is for.

    Returns:
        list: A list of processed player scoring total information with player metadata and total
            fantasy points scored
    """
    processed_totals = []
    for total in player_totals:
        if POSITION_ID_MAPPING.get(total["player"]["defaultPositionId"], ""):
            player_scoring_info = {}
            player_scoring_info["player_id"] = total["id"]
            player_scoring_info["player_name"] = total["player"]["fullName"]
            player_scoring_info["position"] = POSITION_ID_MAPPING[
                total["player"]["defaultPositionId"]
            ]
            if int(season) >= 2018:
                if total.get("ratings", {}):
                    player_scoring_info["total_points"] = round(
                        total["ratings"]["0"]["totalRating"], 2
                    )
                else:
                    continue  # No scoring data available for player, do not add to results
            else:
                player_scoring_info["total_points"] = round(
                    total["player"]["stats"][0]["appliedTotal"], 2
                )
            processed_totals.append(player_scoring_info)
    return processed_totals


def enrich_draft_data(
    draft_results: list[dict[str, Any]],
    player_totals: list[dict[str, Any]],
    teams: list[dict[str, Any]],
) -> list:
    """
    Join draft results for season with player scoring totals to get comparison of player draft position
        to final season rank among position and overall. Additionally, join data with league owner ID
        mapping to associate an owner name with a draft pick.

    Args:
        draft_results (list[dict[str, Any]]): List of dictionary mappings containing league draft results.
        player_totals (list[dict[str, Any]]): List of dictionary mappings containing player scoring totals.
        teams (list[dict[str, Any]]): List of dictionary mappings containing teams in league for the season.

    Returns:
        list: List of dictionary mappings with draft results combined with player scoring totals
    """
    # Read source data into dataframes
    df_draft_results = pd.DataFrame(draft_results)
    df_player_totals = pd.DataFrame(player_totals)
    df_teams = pd.DataFrame(teams)

    # Cast teamId column
    df_draft_results["teamId"] = df_draft_results["teamId"].astype(str)

    # Compute positional rankings
    df_player_totals["position_rank"] = (
        df_player_totals.groupby("position")["total_points"]
        .rank(ascending=False, method="dense")
        .astype(int)
    )
    df_player_totals["total_players_at_position"] = df_player_totals.groupby(
        "position"
    )["position"].transform("count")

    # Only take first owner_id if multiple present
    df_teams = df_teams[["team_id", "owner_full_name", "owner_id"]]
    df_teams["owner_id"] = df_teams["owner_id"].apply(
        lambda v: v[0] if isinstance(v, (list, tuple)) and len(v) > 0 else v
    )

    # Join player scoring data to draft results data
    df_combined_draft_data = pd.merge(
        left=df_player_totals,
        right=df_draft_results,
        how="left",
        left_on="player_id",
        right_on="playerId",
    )
    df_combined_draft_data = pd.merge(
        left=df_combined_draft_data,
        right=df_teams,
        how="left",
        left_on="teamId",
        right_on="team_id",
    )

    # Refine columns
    df_combined_draft_data = df_combined_draft_data.drop(
        columns=[
            "playerId",
            "teamId",
            "memberId",
            "nominatingTeamId",
            "lineupSlotId",
            "id",
        ]
    )
    df_combined_draft_data = df_combined_draft_data.rename(
        columns={
            "autoDraftTypeId": "auto_draft_type_id",
            "bidAmount": "bid_amount",
            "overallPickNumber": "overall_pick_number",
            "reservedForKeeper": "reserved_for_keeper",
            "roundId": "round",
            "roundPickNumber": "round_pick_number",
            "tradeLocked": "trade_locked",
        }
    )

    # Refine data types
    df_combined_draft_data["auto_draft_type_id"] = df_combined_draft_data[
        "auto_draft_type_id"
    ].astype("Int64")
    df_combined_draft_data["overall_pick_number"] = df_combined_draft_data[
        "overall_pick_number"
    ].astype("Int64")
    df_combined_draft_data["round"] = df_combined_draft_data["round"].astype("Int64")
    df_combined_draft_data["round_pick_number"] = df_combined_draft_data[
        "round_pick_number"
    ].astype("Int64")

    # Calculate the rank of where a player was drafted for their position
    df_combined_draft_data["position_draft_rank"] = (
        df_combined_draft_data[df_combined_draft_data["auto_draft_type_id"].notnull()]
        .groupby("position")["overall_pick_number"]
        .rank(method="first")
        .reindex(df_combined_draft_data.index)
    ).astype("Int64")

    # Calculate the delta between actual and draft rank. Positive value indicates outperformance.
    df_combined_draft_data["draft_position_rank_delta"] = (
        df_combined_draft_data["position_draft_rank"]
        - df_combined_draft_data["position_rank"]
    ).astype("Int64")

    # Can drop nulls now as we have computed all draft metrics
    df_combined_draft_data_not_null = df_combined_draft_data.dropna()

    dict_draft_results = df_combined_draft_data_not_null.to_dict(orient="records")
    return dict_draft_results


def lambda_handler(event, context):
    """Lambda handler function to get league members and teams."""
    logger.info("Received event: %s", event)
    league_id = event["leagueId"]
    platform = event["platform"]
    privacy = event["privacy"]
    swid_cookie = event["swidCookie"]
    espn_s2_cookie = event["espnS2Cookie"]
    season = event["season"]

    teams = get_teams(
        league_id=league_id,
        platform=platform,
        season=season,
    )
    draft_picks = get_draft_results(
        league_id=league_id,
        platform=platform,
        privacy=privacy,
        season=season,
        swid_cookie=swid_cookie,
        espn_s2_cookie=espn_s2_cookie,
    )
    player_scoring_totals = get_player_season_totals(
        league_id=league_id,
        platform=platform,
        privacy=privacy,
        season=season,
        swid_cookie=swid_cookie,
        espn_s2_cookie=espn_s2_cookie,
    )
    processed_player_totals = process_player_scoring_totals(
        player_totals=player_scoring_totals,
        season=season,
    )
    joined_draft_data = enrich_draft_data(
        draft_results=draft_picks,
        player_totals=processed_player_totals,
        teams=teams,
    )
    batched_objects = []
    for item in joined_draft_data:
        batched_objects.append(
            {
                "PutRequest": {
                    "Item": {
                        "PK": {
                            "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"
                        },
                        "SK": {"S": f"DRAFT#{item['overall_pick_number']}"},
                        "GSI5PK": {"S": f"LEAGUE#{league_id}"},
                        "GSI5SK": {"S": "FOR_DELETION_USE_ONLY"},
                        "round": {"S": str(item["round"])},
                        "pick_number": {"S": str(item["round_pick_number"])},
                        "overall_pick_number": {"S": str(item["overall_pick_number"])},
                        "reserved_for_keeper": {"BOOL": item["reserved_for_keeper"]},
                        "bid_amount": {"S": str(item["bid_amount"])},
                        "keeper": {"BOOL": item["keeper"]},
                        "player_id": {"S": str(item["player_id"])},
                        "player_full_name": {"S": item["player_name"]},
                        "position": {"S": item["position"]},
                        "points_scored": {
                            "N": str(
                                Decimal(item["total_points"]).quantize(
                                    Decimal("0.01"),
                                    rounding=ROUND_HALF_UP,
                                )
                            )
                        },
                        "position_rank": {"N": str(item["position_rank"])},
                        "drafted_position_rank": {
                            "N": str(item["position_draft_rank"])
                        },
                        "draft_delta": {"N": str(item["draft_position_rank_delta"])},
                        "owner_id": {"S": str(item["owner_id"])},
                        "owner_full_name": {"S": item["owner_full_name"]},
                    }
                }
            }
        )
    batch_write_to_dynamodb(
        batched_objects=batched_objects,
        table_name=DYNAMODB_TABLE_NAME,
    )
    logger.info("Successfully wrote data to DynamoDB.")
