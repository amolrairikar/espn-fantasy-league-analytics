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

# Mainly used for debugging purposes
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)


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
                    "S": "MATCHUP#TEAMS#",
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


def compile_aggregate_standings_data(
    matchup_data: list[dict[str, Any]],
    members_data: list[dict[str, Any]],
) -> tuple[list, list, list, list, list]:
    """
    Calculates all-time league standings based on fantasy matchup scores.

    Args:
        matchup_data (list[dict[str, Any]]): A list of dictionary mappings containing
            matchup scores.

    Returns:
        tuple: A tuple of list of dictionary mappings containing unique league members,
            standings for each season, all-time (incl. playoffs), and head to head all-time.
    """
    # Load matchups data into DataFrames and perform pre-processing
    df_matchups_raw = pd.DataFrame(matchup_data)
    df_matchups = df_matchups_raw[df_matchups_raw["playoff_tier_type"] == "NONE"]

    # Note that these are non toilet bowl playoff matchups
    df_playoff_matchups = df_matchups_raw[
        df_matchups_raw["playoff_tier_type"] == "WINNERS_BRACKET"
    ]

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
    a_view_playoff = df_playoff_matchups[
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
    b_view_playoff = df_playoff_matchups[
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
    long_df_playoff = pd.concat([a_view_playoff, b_view_playoff], ignore_index=True)

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
    long_df_playoff[["win", "loss", "tie"]] = long_df_playoff.apply(outcome_row, axis=1)

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
            "ties",
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
            "ties",
            "win_pct",
            "points_for_per_game",
            "points_against_per_game",
        ]
    ]

    # All-time standings for playoffs (winners bracket only)
    alltime_long_playoffs = long_df_playoff[
        ~long_df_playoff["team_member_id"].isna()
    ].copy()
    alltime_group_playoff = (
        alltime_long_playoffs.groupby(["team_member_id"], dropna=False)
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
    alltime_group_playoff = alltime_group_playoff.merge(
        df_unique_members,
        how="inner",
        left_on="team_member_id",
        right_on="memberId",
    )
    alltime_group_playoff["points_for_per_game"] = (
        alltime_group_playoff.apply(
            lambda r: (r["points_for_total"] / r["games"]) if r["games"] > 0 else 0.0,
            axis=1,
        )
        .astype(float)
        .round(1)
    )
    alltime_group_playoff["points_against_per_game"] = (
        alltime_group_playoff.apply(
            lambda r: (r["points_against_total"] / r["games"])
            if r["games"] > 0
            else 0.0,
            axis=1,
        )
        .astype(float)
        .round(1)
    )
    alltime_group_playoff["win_pct"] = alltime_group_playoff.apply(
        lambda r: (r["wins"] / (r["wins"] + r["losses"]))
        if (r["wins"] + r["losses"]) > 0
        else 0.0,
        axis=1,
    ).round(3)
    alltime_group_playoff["games_played"] = (
        alltime_group_playoff["wins"] + alltime_group_playoff["losses"]
    )
    alltime_standings_playoff = alltime_group_playoff[
        [
            "owner_full_name",
            "team_member_id",
            "games_played",
            "wins",
            "losses",
            "ties",
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
        lambda r: (r["wins"] / (r["wins"] + r["losses"] + r["ties"]))
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
            "ties",
            "win_pct",
            "points_for_per_game",
            "points_against_per_game",
        ]
    ]

    # Convert dataframes to list of dict
    dict_unique_members = df_unique_members.to_dict(orient="records")
    dict_season_standings = season_standings.to_dict(orient="records")
    dict_alltime_standings = alltime_standings.to_dict(orient="records")
    dict_alltime_standings_playoffs = alltime_standings_playoff.to_dict(
        orient="records"
    )
    dict_h2h_standings = h2h_standings.to_dict(orient="records")

    return (
        dict_unique_members,
        dict_season_standings,
        dict_alltime_standings,
        dict_alltime_standings_playoffs,
        dict_h2h_standings,
    )


def compile_weekly_standings_snapshots(
    matchup_data: list[dict[str, Any]],
    members_data: list[dict[str, Any]],
) -> list:
    """
    Calculates cumulative standings at the end of each week for each team.

    Args:
        matchup_data (list[dict[str, Any]]): List of matchups for all seasons.
        members_data (list[dict[str, Any]]): List of league members with season/team mapping.

    Returns:
        list: A list of weekly standings records, one per (season, week, team).
    """
    df_matchups_raw = pd.DataFrame(matchup_data)
    df_matchups = df_matchups_raw[df_matchups_raw["playoff_tier_type"] == "NONE"]

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

    df_unique_members = (
        df_members[["memberId", "owner_full_name"]]
        .drop_duplicates(subset="memberId")
        .reset_index(drop=True)
    )

    # Long form of all matchups (each row is one team’s game)
    a_view = df_matchups.rename(
        columns={
            "team_a_member_id": "team_member_id",
            "team_b_member_id": "opponent_member_id",
            "team_a_score": "points_for",
            "team_b_score": "points_against",
        }
    )[
        [
            "season",
            "week",
            "team_member_id",
            "opponent_member_id",
            "points_for",
            "points_against",
            "winner",
            "loser",
        ]
    ]

    b_view = df_matchups.rename(
        columns={
            "team_b_member_id": "team_member_id",
            "team_a_member_id": "opponent_member_id",
            "team_b_score": "points_for",
            "team_a_score": "points_against",
        }
    )[
        [
            "season",
            "week",
            "team_member_id",
            "opponent_member_id",
            "points_for",
            "points_against",
            "winner",
            "loser",
        ]
    ]

    long_df = pd.concat([a_view, b_view], ignore_index=True)
    long_df["week"] = pd.to_numeric(long_df["week"], errors="coerce")

    # Calculate win/loss/tie columns
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

    # Calculate weekly cumulative standings
    # For each season, team, and week, compute running totals
    long_df = long_df.sort_values(by=["season", "team_member_id", "week"])

    weekly_standings = long_df.groupby(
        ["season", "team_member_id", "week"], as_index=False
    ).agg(
        wins=("win", "sum"),
        losses=("loss", "sum"),
        ties=("tie", "sum"),
        points_for=("points_for", "sum"),
        points_against=("points_against", "sum"),
    )

    # Get cumulative stats per week
    weekly_standings["cum_wins"] = weekly_standings.groupby(
        ["season", "team_member_id"]
    )["wins"].cumsum()
    weekly_standings["cum_losses"] = weekly_standings.groupby(
        ["season", "team_member_id"]
    )["losses"].cumsum()
    weekly_standings["cum_ties"] = weekly_standings.groupby(
        ["season", "team_member_id"]
    )["ties"].cumsum()

    # Merge owner info
    weekly_standings = weekly_standings.merge(
        df_unique_members,
        left_on="team_member_id",
        right_on="memberId",
        how="left",
    ).drop(columns=["memberId"])

    # Select required columns
    weekly_standings = weekly_standings[
        [
            "season",
            "team_member_id",
            "week",
            "cum_wins",
            "cum_losses",
            "cum_ties",
            "owner_full_name",
        ]
    ]
    weekly_standings = weekly_standings.rename(
        columns={
            "cum_wins": "wins",
            "cum_losses": "losses",
            "cum_ties": "ties",
        }
    )

    # Return as list of dicts
    return weekly_standings.to_dict(orient="records")


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
                                "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#STANDINGS#SEASON#TEAM#{item['team_member_id']}"
                            },
                            "GSI2SK": {"S": f"SEASON#{item['season']}"},
                            "season": {"S": item["season"]},
                            "owner_full_name": {"S": item["owner_full_name"]},
                            "wins": {"N": str(item["wins"])},
                            "losses": {"N": str(item["losses"])},
                            "ties": {"N": str(item["ties"])},
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
                            "ties": {"N": str(item["ties"])},
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
        elif standings_data_type == "all-time-playoffs":
            batched_objects.append(
                {
                    "PutRequest": {
                        "Item": {
                            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
                            "SK": {
                                "S": f"STANDINGS#ALL-TIME-PLAYOFFS#{item['team_member_id']}"
                            },
                            "owner_full_name": {"S": item["owner_full_name"]},
                            "games_played": {"N": str(item["games_played"])},
                            "wins": {"N": str(item["wins"])},
                            "losses": {"N": str(item["losses"])},
                            "ties": {"N": str(item["ties"])},
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
        elif standings_data_type == "h2h":
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
                            "ties": {"N": str(item["ties"])},
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
        elif standings_data_type == "weekly":
            batched_objects.append(
                {
                    "PutRequest": {
                        "Item": {
                            "PK": {
                                "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{item['season']}#WEEK#{item['week']}"
                            },
                            "SK": {"S": f"STANDINGS#WEEKLY#{item['team_member_id']}"},
                            "season": {"S": item["season"]},
                            "week": {"N": str(item["week"])},
                            "team_member_id": {"S": item["team_member_id"]},
                            "owner_full_name": {"S": item["owner_full_name"]},
                            "wins": {"N": str(item["wins"])},
                            "losses": {"N": str(item["losses"])},
                            "ties": {"N": str(item["ties"])},
                        }
                    }
                }
            )
        else:
            raise ValueError(f"Unknown standings data type: {standings_data_type}")
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
    (
        unique_members,
        season_standings,
        alltime_standings,
        alltime_standings_playoffs,
        h2h_standings,
    ) = compile_aggregate_standings_data(
        matchup_data=all_matchups, members_data=all_members
    )
    weekly_standings = compile_weekly_standings_snapshots(
        matchup_data=all_matchups,
        members_data=all_members,
    )
    standings_mapping = {
        "members": unique_members,
        "season": season_standings,
        "weekly": weekly_standings,
        "all-time": alltime_standings,
        "all-time-playoffs": alltime_standings_playoffs,
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


lambda_handler(
    event=[
        {
            "leagueId": "1770206",
            "platform": "ESPN",
            "season": "2025",
        },
        {
            "leagueId": "1770206",
            "platform": "ESPN",
            "season": "2024",
        },
        {
            "leagueId": "1770206",
            "platform": "ESPN",
            "season": "2023",
        },
        {
            "leagueId": "1770206",
            "platform": "ESPN",
            "season": "2022",
        },
        {
            "leagueId": "1770206",
            "platform": "ESPN",
            "season": "2021",
        },
        {
            "leagueId": "1770206",
            "platform": "ESPN",
            "season": "2020",
        },
        {
            "leagueId": "1770206",
            "platform": "ESPN",
            "season": "2019",
        },
        {
            "leagueId": "1770206",
            "platform": "ESPN",
            "season": "2018",
        },
        {
            "leagueId": "1770206",
            "platform": "ESPN",
            "season": "2017",
        },
        {
            "leagueId": "1770206",
            "platform": "ESPN",
            "season": "2016",
        },
    ],
    context="",
)
