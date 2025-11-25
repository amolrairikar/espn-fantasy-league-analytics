"""Script to fetch draft results within an ESPN fantasy football league."""

import json
import logging
import math
import numpy as np
import time
from typing import Optional, Any

import boto3
import botocore.exceptions
import pandas as pd
from boto3.dynamodb.types import TypeDeserializer
from urllib3.util.retry import Retry

import requests
from requests.adapters import HTTPAdapter

# Set up standardized logger for Lambda
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(filename)s -  %(lineno)d - %(message)s"
)
console_handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(console_handler)

retry_strategy = Retry(
    total=3,
    backoff_factor=0.3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST", "PUT", "DELETE"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("http://", adapter)
session.mount("https://", adapter)

DYNAMODB_TABLE_NAME = "fantasy-analytics-app-db"
deserializer = TypeDeserializer()

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
        try:
            base_params = [
                ("view", "mDraftDetail"),
            ]
            if int(season) >= 2018:
                url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}"
                params = [*base_params]
            else:
                url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/leagueHistory/{league_id}"
                params = [("seasonId", season), *base_params]
            logger.info("Making request for league draft info to URL: %s", url)
            response = session.get(
                url=url,
                params=params,
                cookies={"SWID": swid_cookie, "espn_s2": espn_s2_cookie},
            )
            response.raise_for_status()
            logger.info("Successfully got league draft info")
            if int(season) >= 2018:
                all_picks = response.json()["draftDetail"].get("picks", [])
            else:
                all_picks = response.json()[0]["draftDetail"].get("picks", [])
            return all_picks
        except requests.RequestException:
            logger.exception("Request error while fetching draft results.")
            raise
        except Exception:
            logger.exception("Unexpected error while fetching draft results.")
            raise
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
        try:
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
                url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}"
                params = [*base_params]
            else:
                url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/leagueHistory/{league_id}"
                params = [("seasonId", season), *base_params]
            logger.info("Making request for player scoring totals to URL: %s", url)
            response = session.get(
                url=url,
                headers=headers,
                params=params,
                cookies={"SWID": swid_cookie, "espn_s2": espn_s2_cookie},
            )
            response.raise_for_status()
            logger.info("Successfully got player scoring totals")
            if int(season) >= 2018:
                player_totals = response.json().get("players", [])
            else:
                player_totals = response.json()[0].get("players", [])
            return player_totals
        except requests.RequestException:
            logger.exception("Request error while fetching player scoring totals.")
            raise
        except Exception:
            logger.exception("Unexpected error while fetching player scoring totals.")
            raise
    else:
        raise ValueError("Unsupported platform. Only ESPN is currently supported.")


def process_player_scoring_totals(
    player_totals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Process raw player scoring totals data to get relevant information.

    Args:
        player_totals (list[dict[str, Any]]): List of dictionaries containing fantasy scoring totals
            for each available player in the fantasy league.

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
            player_scoring_info["total_points"] = [
                item["appliedTotal"]
                for item in total["player"]["stats"]
                if len(str(item["appliedTotal"]).split(".")[1]) <= 2
            ][0]
            player_scoring_info["position"] = POSITION_ID_MAPPING[
                total["player"]["defaultPositionId"]
            ]
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
    )
    df_combined_draft_data["position_draft_rank"] = df_combined_draft_data[
        "position_draft_rank"
    ].astype("Int64")

    # Calculate expected and average values and the delta between those two values
    df_combined_draft_data["expected_value"] = 1 - (
        df_combined_draft_data["position_draft_rank"] - 1
    ) / (df_combined_draft_data["total_players_at_position"] - 1)
    df_combined_draft_data["actual_value"] = 1 - (
        df_combined_draft_data["position_rank"] - 1
    ) / (df_combined_draft_data["total_players_at_position"] - 1)
    df_combined_draft_data["performance_score"] = (
        df_combined_draft_data["actual_value"]
        - df_combined_draft_data["expected_value"]
    )

    # Calculate pick weight and draft value
    df_combined_draft_data["pick_weight"] = 1 / np.sqrt(
        df_combined_draft_data["overall_pick_number"]
    )
    df_combined_draft_data["draft_value"] = (
        df_combined_draft_data["performance_score"]
        * df_combined_draft_data["pick_weight"]
    )

    # Compute z-score for draft value by position
    df_combined_draft_data["dv_mean_pos"] = df_combined_draft_data.groupby("position")[
        "draft_value"
    ].transform("mean")
    df_combined_draft_data["dv_std_pos"] = df_combined_draft_data.groupby("position")[
        "draft_value"
    ].transform("std")
    df_combined_draft_data["dv_zscore"] = (
        df_combined_draft_data["draft_value"] - df_combined_draft_data["dv_mean_pos"]
    ) / df_combined_draft_data["dv_std_pos"]
    df_combined_draft_data["scaled_dv_zscore"] = (
        50 + 10 * df_combined_draft_data["dv_zscore"]
    )

    # Can drop nulls now as we have computed all draft metrics
    df_combined_draft_data_not_null = df_combined_draft_data.dropna()

    dict_draft_results = df_combined_draft_data_not_null.to_dict(orient="records")
    return dict_draft_results


def batch_write_to_dynamodb(
    data_to_write: list[dict[str, Any]], league_id: str, platform: str, season: str
) -> None:
    """
    Writes data in batches to DynamoDB with retries of unprocessed items using
    exponential backoff.

    Args:
        data_to_write (dict[str, str]): Output data to write to DynamoDB.
        league_id (str): The unique ID of the fantasy football league.
        platform (str): The platform the fantasy football league is on (e.g., ESPN, Sleeper).
        season (str): The NFL season to get data for.
    """
    batched_objects = []
    for item in data_to_write:
        batched_objects.append(
            {
                "PutRequest": {
                    "Item": {
                        "PK": {
                            "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"
                        },
                        "SK": {"S": f"DRAFT#{item['overall_pick_number']}"},
                        "round": {"S": str(item["round"])},
                        "pick_number": {"S": str(item["round_pick_number"])},
                        "overall_pick_number": {"S": str(item["overall_pick_number"])},
                        "reserved_for_keeper": {"BOOL": item["reserved_for_keeper"]},
                        "bid_amount": {"S": str(item["bid_amount"])},
                        "keeper": {"BOOL": item["keeper"]},
                        "player_id": {"S": str(item["player_id"])},
                        "player_full_name": {"S": item["player_name"]},
                        "position": {"S": item["position"]},
                        "points_scored": {"N": str(item["total_points"])},
                        "position_rank": {"N": str(item["position_rank"])},
                        "drafted_position_rank": {
                            "N": str(item["position_draft_rank"])
                        },
                        "raw_draft_value": {"N": str(item["dv_zscore"])},
                        "scaled_draft_value": {"N": str(item["scaled_dv_zscore"])},
                        "owner_id": {"S": str(item["owner_id"])},
                        "owner_full_name": {"S": item["owner_full_name"]},
                    }
                }
            }
        )
    dynamodb = boto3.client("dynamodb")
    try:
        backoff = 1.0
        max_retries = 5

        # BatchWriteItem has max limit of 25 items
        batch_number = 0
        for i in range(0, len(batched_objects), 25):
            logger.info(
                "Processing batch %d/%d",
                batch_number + 1,
                math.ceil(len(batched_objects) / 25),
            )
            batch = batched_objects[i : i + 25]
            request_items = {DYNAMODB_TABLE_NAME: batch}
            retries = 0
            while True:
                logger.info("Attempt number: %d", retries + 1)
                response = dynamodb.batch_write_item(RequestItems=request_items)
                unprocessed = response.get("UnprocessedItems", {})
                if not unprocessed.get(DYNAMODB_TABLE_NAME):
                    batch_number += 1
                    break  # success, go to next batch

                if retries >= max_retries:
                    raise RuntimeError(
                        f"Max retries exceeded. Still unprocessed: {unprocessed}"
                    )

                logger.info(
                    "Failed to write %d items, retrying unprocessed items...",
                    len(unprocessed),
                )
                retries += 1
                sleep_time = backoff * (2 ** (retries - 1))
                time.sleep(sleep_time)

                # Retry only the failed items
                request_items = unprocessed

    except botocore.exceptions.ClientError:
        logger.exception("Error writing draft data to DynamoDB")
        raise


def lambda_handler(event, context):
    """Lambda handler function to get league members and teams."""
    logger.info("Received event: %s", event)
    league_id = event["leagueId"]
    platform = event["platform"]
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
        season=season,
        swid_cookie=swid_cookie,
        espn_s2_cookie=espn_s2_cookie,
    )
    player_scoring_totals = get_player_season_totals(
        league_id=league_id,
        platform=platform,
        season=season,
        swid_cookie=swid_cookie,
        espn_s2_cookie=espn_s2_cookie,
    )
    processed_player_totals = process_player_scoring_totals(
        player_totals=player_scoring_totals
    )
    joined_draft_data = enrich_draft_data(
        draft_results=draft_picks,
        player_totals=processed_player_totals,
        teams=teams,
    )
    batch_write_to_dynamodb(
        data_to_write=joined_draft_data,
        league_id=league_id,
        platform=platform,
        season=season,
    )
    logger.info("Successfully wrote data to DynamoDB.")
