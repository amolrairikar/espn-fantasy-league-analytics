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


def fetch_league_data(
    league_id: str, platform: str, season: str, prefix: str
) -> list[dict[str, Any]]:
    """Generic helper to fetch items from DynamoDB for a given SK prefix."""
    try:
        dynamodb = boto3.client("dynamodb")
        response = dynamodb.query(
            TableName=DYNAMODB_TABLE_NAME,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"},
                ":prefix": {"S": prefix},
            },
        )
        items = [
            {k: deserializer.deserialize(v) for k, v in item.items()}
            for item in response.get("Items", [])
        ]
        return items
    except botocore.exceptions.ClientError:
        logger.exception(f"Unexpected error while fetching {prefix} data")
        raise


def outcome_row(r):
    w = r["winner"]
    if isinstance(w, str) and w.upper() == "TIE":
        return pd.Series({"win": 0, "loss": 0, "tie": 1})
    if str(w) == str(r["team_member_id"]):
        return pd.Series({"win": 1, "loss": 0, "tie": 0})
    if str(r.get("loser")) == str(r["team_member_id"]):
        return pd.Series({"win": 0, "loss": 1, "tie": 0})
    return pd.Series({"win": 0, "loss": 0, "tie": 0})


def compute_standings(
    df: pd.DataFrame, group_cols: list[str], member_map: pd.DataFrame
) -> pd.DataFrame:
    """Compute basic win/loss/tie/points stats and join member info."""
    group = (
        df.groupby(group_cols, dropna=False)
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

    group = group.merge(
        member_map, how="inner", left_on=group_cols[-1], right_on="memberId"
    )
    group["points_for_total"] = group["points_for_total"].astype(float)
    group["points_against_total"] = group["points_against_total"].astype(float)
    group["points_for_per_game"] = (
        (group["points_for_total"] / group["games"]).fillna(0).round(1)
    )
    group["points_against_per_game"] = (
        (group["points_against_total"] / group["games"]).fillna(0).round(1)
    )
    group["win_pct"] = (
        (group["wins"] / (group["wins"] + group["losses"]).replace(0, pd.NA))
        .fillna(0)
        .round(3)
    )
    return group


def compile_aggregate_standings_data(
    matchup_data: list[dict[str, Any]],
    members_data: list[dict[str, Any]],
    playoff_teams_data: list[dict[str, Any]],
    championship_team_data: list[dict[str, Any]],
) -> tuple[list, list, list, list, list]:
    """
    Calculates all-time league standings based on fantasy matchup scores.

    Args:
        matchup_data (list[dict[str, Any]]): A list of dictionary mappings containing
            matchup scores.
        members_data (list[dict[str, Any]]): A list of dictionary mappings containing league
            member info.
        playoff_teams_data (list[dict[str, Any]]): A list of dictionary mappings containing
            playoff team info for each season.
        championship_team_data (list[dict[str, Any]]): A list of dictionary mappings containing
            championship winning team info for each season.

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

    # Load playoff and championship team data into DataFrames
    df_playoff_teams = pd.DataFrame(playoff_teams_data)
    df_championship_teams = pd.DataFrame(championship_team_data)

    # Load members data into DataFrames and perform pre-processing
    df_members = pd.DataFrame(members_data)
    df_members["team_id"] = df_members["SK"].str.split("#").str[1]
    df_members["season"] = df_members["PK"].str.split("#").str[-1]
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

    # Join the member info to the playoff team and championship team data to associate team ID with member ID
    df_playoff_teams_enriched = df_playoff_teams.merge(
        right=df_members,
        how="inner",
        on=["season", "team_id"],
    )

    df_championship_teams_enriched = df_championship_teams.merge(
        right=df_members,
        how="inner",
        on=["season", "team_id"],
    )

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
    long_df[["win", "loss", "tie"]] = long_df.apply(outcome_row, axis=1)
    long_df_playoff[["win", "loss", "tie"]] = long_df_playoff.apply(outcome_row, axis=1)

    season_long = long_df[~long_df["team_member_id"].isna()].copy()
    season_group = compute_standings(
        df=season_long,
        group_cols=["season", "team_member_id"],
        member_map=df_unique_members,
    )
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

    # Merge information about playoff teams
    season_standings = season_standings.merge(
        right=df_playoff_teams_enriched[["season", "memberId", "playoff_status"]],
        how="left",
        left_on=["season", "team_member_id"],
        right_on=["season", "memberId"],
    )

    season_standings = season_standings.drop(columns=["memberId"])
    season_standings.fillna("MISSED_PLAYOFFS", inplace=True)

    # Merge information about championship winner
    season_standings = season_standings.merge(
        right=df_championship_teams_enriched[
            ["season", "memberId", "championship_status"]
        ],
        how="left",
        left_on=["season", "team_member_id"],
        right_on=["season", "memberId"],
    )
    season_standings.fillna("", inplace=True)
    season_standings = season_standings.drop(columns=["memberId"])

    alltime_long = long_df[~long_df["team_member_id"].isna()].copy()
    alltime_group = compute_standings(
        df=alltime_long, group_cols=["team_member_id"], member_map=df_unique_members
    )
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

    alltime_long_playoffs = long_df_playoff[
        ~long_df_playoff["team_member_id"].isna()
    ].copy()
    alltime_group_playoff = compute_standings(
        df=alltime_long_playoffs,
        group_cols=["team_member_id"],
        member_map=df_unique_members,
    )
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
    df_members["season"] = df_members["PK"].str.split("#").str[-1]
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


def format_dynamodb_item(
    standings_type: str, item: dict[str, Any], league_id: str, platform: str
) -> dict:
    base_pk = f"LEAGUE#{league_id}#PLATFORM#{platform}"
    if standings_type == "members":
        return {
            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
            "SK": {"S": f"MEMBERS#{item['memberId']}"},
            "name": {"S": item["owner_full_name"]},
            "member_id": {"S": item["memberId"]},
        }
    elif standings_type == "season":
        return {
            "PK": {"S": f"{base_pk}#SEASON#{item['season']}"},
            "SK": {"S": f"STANDINGS#SEASON#{item['team_member_id']}"},
            "season": {"S": item["season"]},
            "owner_full_name": {"S": item["owner_full_name"]},
            "wins": {"N": str(item["wins"])},
            "losses": {"N": str(item["losses"])},
            "ties": {"N": str(item["ties"])},
            "win_pct": {"N": str(item["win_pct"])},
        }
    elif standings_type == "all-time":
        return {
            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
            "SK": {"S": f"STANDINGS#ALL-TIME#{item['team_member_id']}"},
            "owner_full_name": {"S": item["owner_full_name"]},
            "games_played": {"N": str(item["games_played"])},
            "wins": {"N": str(item["wins"])},
            "losses": {"N": str(item["losses"])},
            "ties": {"N": str(item["ties"])},
            "win_pct": {"N": str(item["win_pct"])},
            "points_for_per_game": {"N": str(item["points_for_per_game"])},
            "points_against_per_game": {"N": str(item["points_against_per_game"])},
        }
    elif standings_type == "all-time-playoffs":
        return {
            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
            "SK": {"S": f"STANDINGS#ALL-TIME-PLAYOFFS#{item['team_member_id']}"},
            "owner_full_name": {"S": item["owner_full_name"]},
            "games_played": {"N": str(item["games_played"])},
            "wins": {"N": str(item["wins"])},
            "losses": {"N": str(item["losses"])},
            "ties": {"N": str(item["ties"])},
            "win_pct": {"N": str(item["win_pct"])},
            "points_for_per_game": {"N": str(item["points_for_per_game"])},
            "points_against_per_game": {"N": str(item["points_against_per_game"])},
        }
    elif standings_type == "h2h":
        return {
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
            "points_for_per_game": {"N": str(item["points_for_per_game"])},
            "points_against_per_game": {"N": str(item["points_against_per_game"])},
        }
    elif standings_type == "weekly":
        return {
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
    raise ValueError(f"Unsupported standings type: {standings_type}")


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
    """
    batched_objects = []
    for item in data_to_write:
        batched_objects = [
            {
                "PutRequest": {
                    "Item": format_dynamodb_item(
                        standings_type=standings_data_type,
                        item=item,
                        league_id=league_id,
                        platform=platform,
                    )
                }
            }
            for item in data_to_write
        ]
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
    all_playoff_teams = []
    all_championship_teams = []
    for season in seasons:
        logger.info("Processing season %s", season)
        matchups = fetch_league_data(
            league_id=league_id,
            platform=platform,
            season=season,
            prefix="MATCHUP#TEAMS#",
        )
        logger.info("Fetched %d matchups for season %s", len(matchups), season)
        all_matchups.extend(matchups)
        members = fetch_league_data(
            league_id=league_id, platform=platform, season=season, prefix="TEAM#"
        )
        logger.info("Fetched %d league members for season %s", len(members), season)
        all_members.extend(members)
        playoff_teams = fetch_league_data(
            league_id=league_id,
            platform=platform,
            season=season,
            prefix="PLAYOFF_TEAM#",
        )
        logger.info(
            "Fetched %d playoff teams for season %s", len(playoff_teams), season
        )
        all_playoff_teams.extend(playoff_teams)
        championship_team = fetch_league_data(
            league_id=league_id,
            platform=platform,
            season=season,
            prefix="LEAGUE_CHAMPION#",
        )
        logger.info("Fetched league champion for season %s", season)
        all_championship_teams.extend(championship_team)
    if not any([all_matchups, all_members, all_playoff_teams, all_championship_teams]):
        raise ValueError(
            "Empty list found for matchups, members, playoff teams, and/or championship teams."
        )
    (
        unique_members,
        season_standings,
        alltime_standings,
        alltime_standings_playoffs,
        h2h_standings,
    ) = compile_aggregate_standings_data(
        matchup_data=all_matchups,
        members_data=all_members,
        playoff_teams_data=all_playoff_teams,
        championship_team_data=all_championship_teams,
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
