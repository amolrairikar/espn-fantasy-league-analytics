"""Script to compile aggregate standings from fantasy league scores."""

import os
from typing import Any

import pandas as pd
from boto3.dynamodb.types import TypeDeserializer

from common_utils.batch_write_dynamodb import batch_write_to_dynamodb
from common_utils.logging_config import logger
from common_utils.query_dynamodb import fetch_league_data

deserializer = TypeDeserializer()
DYNAMODB_TABLE_NAME = os.environ["DYNAMODB_TABLE_NAME"]

# Mainly used for debugging purposes
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)


def outcome_row(r) -> pd.Series:
    """
    Determine win/loss/tie outcome for a given matchup row.

    Args:
        r (pd.Series): A row from the matchup DataFrame.

    Returns:
        pd.Series: A Series with 'win', 'loss', and 'tie' counts.
    """
    w = r["winner"]
    if isinstance(w, str) and w.upper() == "TIE":
        return pd.Series({"win": 0, "loss": 0, "tie": 1})
    if str(w) == str(r["team_owner_id"]):
        return pd.Series({"win": 1, "loss": 0, "tie": 0})
    if str(r.get("loser")) == str(r["team_owner_id"]):
        return pd.Series({"win": 0, "loss": 1, "tie": 0})
    return pd.Series({"win": 0, "loss": 0, "tie": 0})


def compute_standings(
    df: pd.DataFrame, group_cols: list[str], member_map: pd.DataFrame
) -> pd.DataFrame:
    """
    Compute basic win/loss/tie/points stats and join member info.

    Args:
        df (pd.DataFrame): DataFrame containing long form matchup data.
        group_cols (list[str]): List of columns to group by (e.g., season, team_member_id).
        member_map (pd.DataFrame): DataFrame mapping member IDs to owner full names.

    Returns:
        pd.DataFrame: DataFrame containing computed standings with member info.
    """
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
        member_map, how="inner", left_on=group_cols[-1], right_on="owner_id"
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
    df_members["season"] = df_members["PK"].str.split("#").str[-1]
    df_members["owner_id"] = df_members["owner_id"].apply(
        lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x
    )
    df_members["owner_id"] = df_members["owner_id"].astype(str)
    df_members = df_members[["season", "team_id", "owner_id", "owner_full_name"]]

    # Get a mapping of unique members within the league
    df_unique_members = (
        df_members[["owner_id", "owner_full_name"]]
        .drop_duplicates(subset="owner_id")
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
            "team_a_owner_id",
            "team_b_owner_id",
            "team_a_score",
            "team_b_score",
            "winner",
            "loser",
        ]
    ].rename(
        columns={
            "team_a_owner_id": "team_owner_id",
            "team_b_owner_id": "opponent_owner_id",
            "team_a_score": "points_for",
            "team_b_score": "points_against",
        }
    )
    a_view_playoff = df_playoff_matchups[
        [
            "season",
            "week",
            "team_a_owner_id",
            "team_b_owner_id",
            "team_a_score",
            "team_b_score",
            "winner",
            "loser",
        ]
    ].rename(
        columns={
            "team_a_owner_id": "team_owner_id",
            "team_b_owner_id": "opponent_owner_id",
            "team_a_score": "points_for",
            "team_b_score": "points_against",
        }
    )
    b_view = df_matchups[
        [
            "season",
            "week",
            "team_b_owner_id",
            "team_a_owner_id",
            "team_b_score",
            "team_a_score",
            "winner",
            "loser",
        ]
    ].rename(
        columns={
            "team_b_owner_id": "team_owner_id",
            "team_a_owner_id": "opponent_owner_id",
            "team_b_score": "points_for",
            "team_a_score": "points_against",
        }
    )
    b_view_playoff = df_playoff_matchups[
        [
            "season",
            "week",
            "team_b_owner_id",
            "team_a_owner_id",
            "team_b_score",
            "team_a_score",
            "winner",
            "loser",
        ]
    ].rename(
        columns={
            "team_b_owner_id": "team_owner_id",
            "team_a_owner_id": "opponent_owner_id",
            "team_b_score": "points_for",
            "team_a_score": "points_against",
        }
    )
    long_df = pd.concat([a_view, b_view], ignore_index=True)
    long_df_playoff = pd.concat([a_view_playoff, b_view_playoff], ignore_index=True)
    long_df[["win", "loss", "tie"]] = long_df.apply(outcome_row, axis=1)
    long_df_playoff[["win", "loss", "tie"]] = long_df_playoff.apply(outcome_row, axis=1)

    season_long = long_df[~long_df["team_owner_id"].isna()].copy()
    season_group = (
        season_long.groupby(["season", "team_owner_id"], dropna=False)
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
        df_unique_members, how="inner", left_on="team_owner_id", right_on="owner_id"
    )
    season_group["win_pct"] = (
        (
            season_group["wins"]
            / (season_group["wins"] + season_group["losses"]).replace(0, pd.NA)
        )
        .fillna(0)
        .round(3)
    )
    season_group["point_differential"] = (
        season_group["points_for_total"] - season_group["points_against_total"]
    )
    season_standings = season_group[
        [
            "season",
            "owner_full_name",
            "team_owner_id",
            "wins",
            "losses",
            "ties",
            "win_pct",
            "points_for_total",
            "points_against_total",
            "point_differential",
        ]
    ]

    # Merge information about playoff teams
    season_standings = season_standings.merge(
        right=df_playoff_teams_enriched[["season", "owner_id", "playoff_status"]],
        how="left",
        left_on=["season", "team_owner_id"],
        right_on=["season", "owner_id"],
    )

    season_standings = season_standings.drop(columns=["owner_id"])
    season_standings.fillna("MISSED_PLAYOFFS", inplace=True)

    # Merge information about championship winner
    season_standings = season_standings.merge(
        right=df_championship_teams_enriched[
            ["season", "owner_id", "championship_status"]
        ],
        how="left",
        left_on=["season", "team_owner_id"],
        right_on=["season", "owner_id"],
    )
    season_standings.fillna("", inplace=True)
    season_standings = season_standings.drop(columns=["owner_id"])

    alltime_long = long_df[~long_df["team_owner_id"].isna()].copy()
    alltime_group = compute_standings(
        df=alltime_long, group_cols=["team_owner_id"], member_map=df_unique_members
    )
    alltime_group["games_played"] = alltime_group["wins"] + alltime_group["losses"]
    alltime_standings = alltime_group[
        [
            "owner_full_name",
            "team_owner_id",
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
        ~long_df_playoff["team_owner_id"].isna()
    ].copy()
    alltime_group_playoff = compute_standings(
        df=alltime_long_playoffs,
        group_cols=["team_owner_id"],
        member_map=df_unique_members,
    )
    alltime_group_playoff["games_played"] = (
        alltime_group_playoff["wins"] + alltime_group_playoff["losses"]
    )
    alltime_standings_playoff = alltime_group_playoff[
        [
            "owner_full_name",
            "team_owner_id",
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
        ~long_df["team_owner_id"].isna() & ~long_df["opponent_owner_id"].isna()
    ].copy()
    h2h_group = (
        h2h_long.groupby(
            [
                "team_owner_id",
                "opponent_owner_id",
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
        left_on="team_owner_id",
        right_on="owner_id",
    )
    h2h_group = h2h_group.merge(
        df_unique_members,
        how="inner",
        left_on="opponent_owner_id",
        right_on="owner_id",
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
    h2h_group = h2h_group.drop(columns=["owner_id", "owner_id_opponent"])
    h2h_standings = h2h_group.rename(
        columns={
            "owner_full_name_opponent": "opponent_full_name",
        }
    )[
        [
            "owner_full_name",
            "team_owner_id",
            "opponent_full_name",
            "opponent_owner_id",
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


def format_dynamodb_item(
    standings_type: str, item: dict[str, Any], league_id: str, platform: str
) -> dict:
    """
    Formats an item into a DynamoDB schema for the given standings type.

    Args:
        standings_type (str): The type of standings data (season, H2H, all-time).
        item (dict[str, Any]): The item data to format.
        league_id (str): The unique ID of the fantasy football league.
        platform (str): The platform the fantasy football league is on (e.g., ESPN, Sleeper).

    Returns:
        dict: Formatted DynamoDB item.
    """
    if standings_type == "owners":
        return {
            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
            "SK": {"S": f"OWNERS#{item['owner_id']}"},
            "owner_full_name": {"S": item["owner_full_name"]},
            "owner_id": {"S": item["owner_id"]},
        }
    elif standings_type == "season":
        return {
            "PK": {
                "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{item['season']}"
            },
            "SK": {"S": f"STANDINGS#SEASON#{item['team_owner_id']}"},
            "GSI2PK": {
                "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#STANDINGS#SEASON#TEAM#{item['team_owner_id']}"
            },
            "GSI2SK": {"S": f"SEASON#{item['season']}"},
            "season": {"S": item["season"]},
            "owner_full_name": {"S": item["owner_full_name"]},
            "wins": {"N": str(item["wins"])},
            "losses": {"N": str(item["losses"])},
            "ties": {"N": str(item["ties"])},
            "win_pct": {"N": str(item["win_pct"])},
            "points_for": {"N": str(item["points_for_total"])},
            "points_against": {"N": str(item["points_against_total"])},
            "points_differential": {"N": str(item["point_differential"])},
            "playoff_status": {"S": item["playoff_status"]},
            "championship_status": {"S": item["championship_status"]},
        }
    elif standings_type == "all_time":
        return {
            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
            "SK": {"S": f"STANDINGS#ALL-TIME#{item['team_owner_id']}"},
            "owner_full_name": {"S": item["owner_full_name"]},
            "games_played": {"N": str(item["games_played"])},
            "wins": {"N": str(item["wins"])},
            "losses": {"N": str(item["losses"])},
            "ties": {"N": str(item["ties"])},
            "win_pct": {"N": str(item["win_pct"])},
            "points_for_per_game": {"N": str(item["points_for_per_game"])},
            "points_against_per_game": {"N": str(item["points_against_per_game"])},
        }
    elif standings_type == "all_time_playoffs":
        return {
            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
            "SK": {"S": f"STANDINGS#ALL-TIME-PLAYOFFS#{item['team_owner_id']}"},
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
                "S": f"STANDINGS#H2H#{item['team_owner_id']}-vs-{item['opponent_owner_id']}"
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
    raise ValueError(f"Unsupported standings type: {standings_type}")


def lambda_handler(event, context):
    """Lambda handler function to get league members and teams."""
    logger.info("Received event: %s", event)

    league_id = event[0][0]["leagueId"]
    platform = event[0][0]["platform"]
    seasons = [e[0]["season"] for e in event]
    if not seasons:
        raise ValueError("'seasons' list must not be empty.")
    logger.info("Processing seasons %s", seasons)

    all_matchups = []
    all_members = []
    all_playoff_teams = []
    all_championship_teams = []
    for season in seasons:
        logger.info("Processing season %s", season)
        matchups = fetch_league_data(
            table_name=DYNAMODB_TABLE_NAME,
            pk=f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}",
            sk_prefix="MATCHUP#TEAMS#",
        )
        logger.info("Fetched %d matchups for season %s", len(matchups), season)
        all_matchups.extend(matchups)
        members = fetch_league_data(
            table_name=DYNAMODB_TABLE_NAME,
            pk=f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}",
            sk_prefix="TEAM#",
        )
        logger.info("Fetched %d league members for season %s", len(members), season)
        all_members.extend(members)
        playoff_teams = fetch_league_data(
            table_name=DYNAMODB_TABLE_NAME,
            pk=f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}",
            sk_prefix="PLAYOFF_TEAM#",
        )
        logger.info(
            "Fetched %d playoff teams for season %s", len(playoff_teams), season
        )
        all_playoff_teams.extend(playoff_teams)
        championship_team = fetch_league_data(
            table_name=DYNAMODB_TABLE_NAME,
            pk=f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}",
            sk_prefix="LEAGUE_CHAMPION#",
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
    standings_mapping = {
        "owners": unique_members,
        "season": season_standings,
        "all_time": alltime_standings,
        "all_time_playoffs": alltime_standings_playoffs,
        "h2h": h2h_standings,
    }
    for standings_type, standings_data in standings_mapping.items():
        logger.info("Processing %s data", standings_type)
        batched_objects = []
        for item in standings_data:
            formatted_item = {
                "PutRequest": {
                    "Item": format_dynamodb_item(
                        standings_type=standings_type,
                        item=item,
                        league_id=league_id,
                        platform=platform,
                    )
                }
            }
            batched_objects.append(formatted_item)
        batch_write_to_dynamodb(
            batched_objects=batched_objects,
            table_name=DYNAMODB_TABLE_NAME,
        )
        logger.info("Successfully processed %s data", standings_type)
    logger.info("Successfully wrote data to DynamoDB.")
