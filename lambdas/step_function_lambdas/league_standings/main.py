"""Script to compile aggregate standings from fantasy league scores."""

import logging
import math
import time
from typing import Any

import boto3
import botocore.exceptions
import pandas as pd
from boto3.dynamodb.types import TypeDeserializer

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

DYNAMODB_TABLE_NAME = "fantasy-analytics-app-db"
deserializer = TypeDeserializer()


def get_matchups(league_id: str, platform: str, season: str) -> list[dict[str, Any]]:
    """
    Fetch all matchups from the DynamoDB table for a given league.

    Args:
        league_id (str): The unique identifier for the fantasy league.
        platform (str): The platform the fantasy league is on (ESPN, Sleeper)
        season (str): The season to get matchups for

    Returns:
        list: A list of mappings with matchups info for the season
    """
    try:
        dynamodb = boto3.client("dynamodb")
        response = dynamodb.query(
            TableName=DYNAMODB_TABLE_NAME,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
            ExpressionAttributeValues={
                ":pk": {
                    "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}",
                },
                ":prefix": {
                    "S": "MATCHUP#",
                },
            },
        )
        matchups = [
            {
                **{k: deserializer.deserialize(v) for k, v in item.items()},
                "season": season,
            }
            for item in response.get("Items", [])
        ]
        return matchups
    except botocore.exceptions.ClientError:
        logger.exception("Unexpected error while fetching league matchups")
        raise


def get_league_members(
    league_id: str, platform: str, season: str
) -> list[dict[str, Any]]:
    """
    Fetch all league members in a given season for a given league and platform.

    Args:
        league_id (str): The unique identifier for the fantasy league.
        platform (str): The platform the fantasy league is on (ESPN, Sleeper)
        season (str): The season to get members for

    Returns:
        list: A list of mappings with members info for the season
    """
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
        members = [
            {
                **{k: deserializer.deserialize(v) for k, v in item.items()},
                "season": season,
            }
            for item in response.get("Items", [])
        ]
        return members
    except botocore.exceptions.ClientError:
        logger.exception("Unexpected error while fetching league members")
        raise


def compile_standings_data(
    matchup_data: list[dict[str, Any]],
    members_data: list[dict[str, Any]],
) -> tuple[list, list, list, list]:
    """
    Calculates all-time league standings based on fantasy matchup scores.

    Args:
        matchup_data (list[dict[str, Any]]): A list of dictionary mappings containing
            matchup scores.

    Returns:
        tuple: A tuple of list of dictionary mappings containing unique league members,
            standings for each season, all-time, and head to head all-time.
    """
    # Mainly used for debugging/printing
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)

    # Load matchups data into DataFrames and perform pre-processing
    df_matchups = pd.DataFrame(matchup_data)
    df_matchups = df_matchups[df_matchups["playoff_tier_type"] == "NONE"]

    # Load members data into DataFrames and perform pre-processing
    df_members = pd.DataFrame(members_data)
    df_members["team_id"] = df_members["SK"].str.split("#").str[1]
    df_members["owner_full_name"] = (
        df_members["firstName"] + " " + df_members["lastName"]
    )
    df_members["memberId"] = df_members["memberId"].apply(
        lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x
    )
    df_members["memberId"] = df_members["memberId"].astype(str)
    df_members = df_members[["season", "team_id", "memberId", "owner_full_name"]]

    # Get a mapping of unique members within the league
    df_unique_members = (
        df_members[["memberId", "owner_full_name"]]
        .drop_duplicates(subset="memberId")
        .reset_index(drop=True)
    )
    df_unique_members = df_unique_members.drop_duplicates(
        subset="owner_full_name"
    ).reset_index(drop=True)

    # Get data into long form (one row per team per matchup)
    a_view = df_matchups[
        [
            "season",
            "week",
            "team_a_member_id",
            "team_b_member_id",
            "team_a_score",
            "team_b_score",
            "winner",
            "loser",
        ]
    ].rename(
        columns={
            "team_a_member_id": "team_member_id",
            "team_b_member_id": "opponent_member_id",
            "team_a_score": "points_for",
            "team_b_score": "points_against",
        }
    )
    b_view = df_matchups[
        [
            "season",
            "week",
            "team_b_member_id",
            "team_a_member_id",
            "team_b_score",
            "team_a_score",
            "winner",
            "loser",
        ]
    ].rename(
        columns={
            "team_b_member_id": "team_member_id",
            "team_a_member_id": "opponent_member_id",
            "team_b_score": "points_for",
            "team_a_score": "points_against",
        }
    )
    long_df = pd.concat([a_view, b_view], ignore_index=True)

    # Get win/loss/tie columns
    def outcome_row(r):
        w = r["winner"]
        if isinstance(w, str) and w.upper() == "TIE":
            return pd.Series({"win": 0, "loss": 0, "tie": 1})
        if str(w) == str(r["team_member_id"]):
            return pd.Series({"win": 1, "loss": 0, "tie": 0})
        if str(r.get("loser")) == str(r["team_member_id"]):
            return pd.Series({"win": 0, "loss": 1, "tie": 0})
        return pd.Series({"win": 0, "loss": 0, "tie": 0})

    long_df[["win", "loss", "tie"]] = long_df.apply(outcome_row, axis=1)

    # Season standings
    season_long = long_df[~long_df["team_member_id"].isna()].copy()
    season_group = (
        season_long.groupby(["season", "team_member_id"], dropna=False)
        .agg(
            wins=("win", "sum"),
            losses=("loss", "sum"),
            ties=("tie", "sum"),
            games=("points_for", "count"),
            points_for_total=("points_for", "sum"),
            points_against_total=("points_against", "sum"),
        )
        .reset_index()
    )
    season_group = season_group.merge(
        df_unique_members,
        how="inner",
        left_on="team_member_id",
        right_on="memberId",
    )
    season_group = season_group.drop(columns=["memberId"])
    season_group["points_for_per_game"] = (
        season_group.apply(
            lambda r: (r["points_for_total"] / r["games"]) if r["games"] > 0 else 0.0,
            axis=1,
        )
        .astype(float)
        .round(1)
    )
    season_group["points_against_per_game"] = (
        season_group.apply(
            lambda r: (r["points_against_total"] / r["games"])
            if r["games"] > 0
            else 0.0,
            axis=1,
        )
        .astype(float)
        .round(1)
    )
    season_group["win_pct"] = season_group.apply(
        lambda r: (r["wins"] / (r["wins"] + r["losses"]))
        if (r["wins"] + r["losses"]) > 0
        else 0.0,
        axis=1,
    ).round(3)
    season_standings = season_group[
        [
            "season",
            "owner_full_name",
            "team_member_id",
            "wins",
            "losses",
            "win_pct",
            "points_for_per_game",
            "points_against_per_game",
        ]
    ]

    # All-time standings (aggregate across seasons)
    alltime_long = long_df[~long_df["team_member_id"].isna()].copy()
    alltime_group = (
        alltime_long.groupby(["team_member_id"], dropna=False)
        .agg(
            wins=("win", "sum"),
            losses=("loss", "sum"),
            ties=("tie", "sum"),
            games=("points_for", "count"),
            points_for_total=("points_for", "sum"),
            points_against_total=("points_against", "sum"),
        )
        .reset_index()
    )
    alltime_group = alltime_group.merge(
        df_unique_members,
        how="inner",
        left_on="team_member_id",
        right_on="memberId",
    )
    alltime_group["points_for_per_game"] = (
        alltime_group.apply(
            lambda r: (r["points_for_total"] / r["games"]) if r["games"] > 0 else 0.0,
            axis=1,
        )
        .astype(float)
        .round(1)
    )
    alltime_group["points_against_per_game"] = (
        alltime_group.apply(
            lambda r: (r["points_against_total"] / r["games"])
            if r["games"] > 0
            else 0.0,
            axis=1,
        )
        .astype(float)
        .round(1)
    )
    alltime_group["win_pct"] = alltime_group.apply(
        lambda r: (r["wins"] / (r["wins"] + r["losses"]))
        if (r["wins"] + r["losses"]) > 0
        else 0.0,
        axis=1,
    ).round(3)
    alltime_group["games_played"] = alltime_group["wins"] + alltime_group["losses"]
    alltime_standings = alltime_group[
        [
            "owner_full_name",
            "team_member_id",
            "games_played",
            "wins",
            "losses",
            "win_pct",
            "points_for_per_game",
            "points_against_per_game",
        ]
    ]

    # H2H (all-time) between owners
    h2h_long = long_df[
        ~long_df["team_member_id"].isna() & ~long_df["opponent_member_id"].isna()
    ].copy()
    h2h_group = (
        h2h_long.groupby(
            [
                "team_member_id",
                "opponent_member_id",
            ],
            dropna=False,
        )
        .agg(
            wins=("win", "sum"),
            losses=("loss", "sum"),
            ties=("tie", "sum"),
            games=("points_for", "count"),
            points_for_total=("points_for", "sum"),
            points_against_total=("points_against", "sum"),
        )
        .reset_index()
    )
    h2h_group = h2h_group.merge(
        df_unique_members,
        how="inner",
        left_on="team_member_id",
        right_on="memberId",
    )
    h2h_group = h2h_group.merge(
        df_unique_members,
        how="inner",
        left_on="opponent_member_id",
        right_on="memberId",
        suffixes=("", "_opponent"),
    )
    h2h_group["points_for_per_game"] = (
        h2h_group.apply(
            lambda r: (r["points_for_total"] / r["games"]) if r["games"] > 0 else 0.0,
            axis=1,
        )
        .astype(float)
        .round(1)
    )
    h2h_group["points_against_per_game"] = (
        h2h_group.apply(
            lambda r: (r["points_against_total"] / r["games"])
            if r["games"] > 0
            else 0.0,
            axis=1,
        )
        .astype(float)
        .round(1)
    )
    h2h_group["win_pct"] = h2h_group.apply(
        lambda r: (r["wins"] / (r["wins"] + r["losses"]))
        if (r["wins"] + r["losses"]) > 0
        else 0.0,
        axis=1,
    ).round(3)
    h2h_group["games_played"] = h2h_group["wins"] + h2h_group["losses"]
    h2h_group = h2h_group.drop(columns=["memberId", "memberId_opponent"])
    h2h_standings = h2h_group.rename(
        columns={
            "owner_full_name_opponent": "opponent_full_name",
        }
    )[
        [
            "owner_full_name",
            "team_member_id",
            "opponent_full_name",
            "opponent_member_id",
            "games_played",
            "wins",
            "losses",
            "win_pct",
            "points_for_per_game",
            "points_against_per_game",
        ]
    ]

    # Convert dataframes to list of dict
    dict_unique_members = df_unique_members.to_dict(orient="records")
    dict_season_standings = season_standings.to_dict(orient="records")
    dict_alltime_standings = alltime_standings.to_dict(orient="records")
    dict_h2h_standings = h2h_standings.to_dict(orient="records")

    return (
        dict_unique_members,
        dict_season_standings,
        dict_alltime_standings,
        dict_h2h_standings,
    )


def batch_write_to_dynamodb(
    data_to_write: list[dict[str, Any]],
    standings_data_type: str,
    league_id: str,
    platform: str,
) -> None:
    """
    Writes data in batches to DynamoDB with retries of unprocessed items using
    exponential backoff.

    Args:
        data_to_write (list[dict[str, Any]]): Output data to write to DynamoDB.
        standings_data_type: (dict[str, Any]): The type of standings data (season, H2H, all-time).
        league_id (str): The unique ID of the fantasy football league.
        platform (str): The platform the fantasy football league is on (e.g., ESPN, Sleeper).
        season (str): The NFL season to get data for.
    """
    batched_objects = []
    for item in data_to_write:
        if standings_data_type == "members":
            batched_objects.append(
                {
                    "PutRequest": {
                        "Item": {
                            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
                            "SK": {"S": f"MEMBERS#{item['memberId']}"},
                            "name": {"S": item["owner_full_name"]},
                            "member_id": {"S": item["memberId"]},
                        }
                    }
                }
            )
        elif standings_data_type == "season":
            batched_objects.append(
                {
                    "PutRequest": {
                        "Item": {
                            "PK": {
                                "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{item['season']}"
                            },
                            "SK": {"S": f"STANDINGS#SEASON#{item['team_member_id']}"},
                            "GSI2PK": {
                                "S": f"STANDINGS#SEASON#TEAM#{item['team_member_id']}"
                            },
                            "GSI2SK": {
                                "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{item['season']}"
                            },
                            "season": {"S": item["season"]},
                            "owner_full_name": {"S": item["owner_full_name"]},
                            "wins": {"N": str(item["wins"])},
                            "losses": {"N": str(item["losses"])},
                            "win_pct": {"N": str(item["win_pct"])},
                            "points_for_per_game": {
                                "N": str(item["points_for_per_game"])
                            },
                            "points_against_per_game": {
                                "N": str(item["points_against_per_game"])
                            },
                        }
                    }
                }
            )
        elif standings_data_type == "all-time":
            batched_objects.append(
                {
                    "PutRequest": {
                        "Item": {
                            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
                            "SK": {"S": f"STANDINGS#ALL-TIME#{item['team_member_id']}"},
                            "owner_full_name": {"S": item["owner_full_name"]},
                            "games_played": {"N": str(item["games_played"])},
                            "wins": {"N": str(item["wins"])},
                            "losses": {"N": str(item["losses"])},
                            "win_pct": {"N": str(item["win_pct"])},
                            "points_for_per_game": {
                                "N": str(item["points_for_per_game"])
                            },
                            "points_against_per_game": {
                                "N": str(item["points_against_per_game"])
                            },
                        }
                    }
                }
            )
        else:
            batched_objects.append(
                {
                    "PutRequest": {
                        "Item": {
                            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
                            "SK": {
                                "S": f"STANDINGS#H2H#{item['team_member_id']}-vs-{item['opponent_member_id']}"
                            },
                            "owner_full_name": {"S": item["owner_full_name"]},
                            "opponent_full_name": {"S": item["opponent_full_name"]},
                            "games_played": {"N": str(item["games_played"])},
                            "wins": {"N": str(item["wins"])},
                            "losses": {"N": str(item["losses"])},
                            "win_pct": {"N": str(item["win_pct"])},
                            "points_for_per_game": {
                                "N": str(item["points_for_per_game"])
                            },
                            "points_against_per_game": {
                                "N": str(item["points_against_per_game"])
                            },
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
        logger.exception("Error writing member and team data to DynamoDB")
        raise


def lambda_handler(event, context):
    """Lambda handler function to get league members and teams."""
    logger.info("Received event: %s", event)
    league_id = event[0]["leagueId"]
    platform = event[0]["platform"]
    seasons = [e["season"] for e in event]
    if not seasons:
        raise ValueError("'seasons' list must not be empty.")

    all_matchups = []
    all_members = []
    for season in seasons:
        logger.info("Processing season %s", season)
        matchups = get_matchups(league_id=league_id, platform=platform, season=season)
        logger.info("Fetched %d matchups for season %s", len(matchups), season)
        all_matchups.extend(matchups)
        members = get_league_members(
            league_id=league_id, platform=platform, season=season
        )
        logger.info("Fetched %d league members for season %s", len(members), season)
        all_members.extend(members)
    if not all_matchups or not all_members:
        raise ValueError("'all_matchups' and/or 'all_members' lists must not be empty.")
    unique_members, season_standings, alltime_standings, h2h_standings = (
        compile_standings_data(matchup_data=all_matchups, members_data=all_members)
    )
    standings_mapping = {
        "members": unique_members,
        "season": season_standings,
        "all-time": alltime_standings,
        "h2h": h2h_standings,
    }
    for standings_type, standings_data in standings_mapping.items():
        logger.info("Processing %s data", standings_type)
        batch_write_to_dynamodb(
            data_to_write=standings_data,
            standings_data_type=standings_type,
            league_id=league_id,
            platform=platform,
        )
        logger.info("Successfully processed %s data", standings_type)
    logger.info("Successfully wrote data to DynamoDB.")
