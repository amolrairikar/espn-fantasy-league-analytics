"""Script to compile aggregate standings from fantasy league scores."""

import logging
import math
import time
from decimal import Decimal
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
    """
    Generic helper to fetch items from DynamoDB for a given SK prefix.

    Args:
        league_id (str): The unique ID of the fantasy football league.
        platform (str): The platform the fantasy football league is on (e.g., ESPN, Sleeper).
        season (str): The season year for which data is being fetched.
        prefix (str): The SK prefix to filter items by.

    Returns:
        list[dict[str, Any]]: A list of dictionary mappings containing the fetched data.
    """
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
    season_group = compute_standings(
        df=season_long,
        group_cols=["season", "team_owner_id"],
        member_map=df_unique_members,
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
            "points_for_per_game",
            "points_against_per_game",
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
    df_members["season"] = df_members["PK"].str.split("#").str[-1]
    df_members["owner_id"] = df_members["owner_id"].apply(
        lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x
    )
    df_members["owner_id"] = df_members["owner_id"].astype(str)
    df_members = df_members[["season", "team_id", "owner_id", "owner_full_name"]]

    df_unique_members = (
        df_members[["owner_id", "owner_full_name"]]
        .drop_duplicates(subset="owner_id")
        .reset_index(drop=True)
    )

    # Long form of all matchups (each row is one team’s game)
    a_view = df_matchups.rename(
        columns={
            "team_a_owner_id": "team_owner_id",
            "team_b_owner_id": "opponent_owner_id",
            "team_a_score": "points_for",
            "team_b_score": "points_against",
        }
    )[
        [
            "season",
            "week",
            "team_owner_id",
            "opponent_owner_id",
            "points_for",
            "points_against",
            "winner",
            "loser",
        ]
    ]

    b_view = df_matchups.rename(
        columns={
            "team_b_owner_id": "team_owner_id",
            "team_a_owner_id": "opponent_owner_id",
            "team_b_score": "points_for",
            "team_a_score": "points_against",
        }
    )[
        [
            "season",
            "week",
            "team_owner_id",
            "opponent_owner_id",
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
    long_df = long_df.sort_values(by=["season", "team_owner_id", "week"])

    weekly_standings = long_df.groupby(
        ["season", "team_owner_id", "week"], as_index=False
    ).agg(
        wins=("win", "sum"),
        losses=("loss", "sum"),
        ties=("tie", "sum"),
        points_for=("points_for", "sum"),
        points_against=("points_against", "sum"),
    )

    # Get cumulative stats per week
    weekly_standings["cum_wins"] = weekly_standings.groupby(
        ["season", "team_owner_id"]
    )["wins"].cumsum()
    weekly_standings["cum_losses"] = weekly_standings.groupby(
        ["season", "team_owner_id"]
    )["losses"].cumsum()
    weekly_standings["cum_ties"] = weekly_standings.groupby(
        ["season", "team_owner_id"]
    )["ties"].cumsum()

    # Merge owner info
    weekly_standings = weekly_standings.merge(
        df_unique_members,
        left_on="team_owner_id",
        right_on="owner_id",
        how="left",
    ).drop(columns=["owner_id"])

    # Select required columns
    weekly_standings = weekly_standings[
        [
            "season",
            "team_owner_id",
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


def compile_all_time_records(
    matchup_data: list[dict[str, Any]],
    members_data: list[dict[str, Any]],
    championship_team_data: list[dict[str, Any]],
) -> tuple[list, list, list, list, list, list, list, list, list]:
    """
    Function to get all-time records including and excluding playoffs.

    Args:
        matchup_data (list[dict[str, Any]]): A list of dictionary mappings containing
            matchup scores.
        members_data (list[dict[str, Any]]): A list of dictionary mappings containing league
            member info.
        championship_team_data (list[dict[str, Any]]): A list of dictionary mappings containing
            championship winning team info for each season.

    Returns:
        tuple: A tuple of lists of dictionary mappings containing all-time records."""
    # Load matchups data into DataFrame
    df_matchups = pd.DataFrame(matchup_data)

    # Load championship team data into DataFrame
    df_championship_teams = pd.DataFrame(championship_team_data)

    # Load members data into DataFrames and perform pre-processing
    df_members = pd.DataFrame(members_data)
    df_members["season"] = df_members["PK"].str.split("#").str[-1]
    df_members["owner_id"] = df_members["owner_id"].apply(
        lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x
    )
    df_members["owner_id"] = df_members["owner_id"].astype(str)
    df_members = df_members[["season", "team_id", "owner_id", "owner_full_name"]]

    df_matchups_scores = df_matchups[
        [
            "season",
            "week",
            "team_a_owner_id",
            "team_a_owner_full_name",
            "team_a_score",
            "team_a_players",
            "team_b_owner_id",
            "team_b_owner_full_name",
            "team_b_score",
            "team_b_players",
        ]
    ]
    df_scores = pd.melt(
        df_matchups_scores,
        id_vars=["season", "week"],
        value_vars=["team_a_score", "team_b_score"],
        var_name="team_side",
        value_name="score",
    )
    df_names = pd.melt(
        df_matchups_scores,
        id_vars=["season", "week"],
        value_vars=["team_a_owner_full_name", "team_b_owner_full_name"],
        var_name="team_side",
        value_name="team_name",
    )
    df_owner_ids = pd.melt(
        df_matchups_scores,
        id_vars=["season", "week"],
        value_vars=["team_a_owner_id", "team_b_owner_id"],
        var_name="team_side",
        value_name="team_owner_id",
    )

    # Combine names and scores on matching rows
    df_combined = df_scores.copy()
    df_combined["owner_name"] = df_names["team_name"]
    df_combined["owner_id"] = df_owner_ids["team_owner_id"]

    # Get 10 highest and 10 lowest team scores
    top10 = df_combined.sort_values("score", ascending=False).head(10)
    top10 = top10[["season", "week", "owner_name", "owner_id", "score"]]
    bottom10 = df_combined.sort_values("score", ascending=True).head(10)
    bottom10 = bottom10[["season", "week", "owner_name", "owner_id", "score"]]

    # Create DataFrame with each player in a matchup being in their own row
    player_stats = []
    for matchup in matchup_data:
        for team_prefix in ["team_a", "team_b"]:
            owner_name = matchup.get(f"{team_prefix}_owner_full_name")
            owner_id = matchup.get(f"{team_prefix}_owner_id")
            players = matchup.get(f"{team_prefix}_players", [])
            if not owner_name or not owner_id or not players:
                continue
            for p in players:
                player_stats.append(
                    {
                        "season": matchup["season"],
                        "week": matchup["week"],
                        "owner_full_name": owner_name,
                        "owner_id": owner_id,
                        "player_id": p["player_id"],
                        "full_name": p["full_name"],
                        "points_scored": Decimal(p["points_scored"]),
                        "position": p["position"],
                    }
                )
    df_player_stats = pd.DataFrame(player_stats)
    df_player_stats_sorted = df_player_stats.sort_values(
        "points_scored", ascending=False
    )
    dfs_by_position = {
        pos: group.sort_values("points_scored", ascending=False)
        .head(10)
        .loc[
            :,
            [
                "season",
                "week",
                "owner_full_name",
                "owner_id",
                "player_id",
                "full_name",
                "points_scored",
                "position",
            ],
        ]
        for pos, group in df_player_stats_sorted.groupby("position")
    }
    df_qb = dfs_by_position["QB"]
    df_rb = dfs_by_position["RB"]
    df_wr = dfs_by_position["WR"]
    df_te = dfs_by_position["TE"]
    df_dst = dfs_by_position["D/ST"]
    df_k = dfs_by_position["K"]

    # Get total championships won per member for members that have won
    df_championship_teams_enriched = df_championship_teams.merge(
        right=df_members,
        how="inner",
        on=["season", "team_id"],
    )
    df_championships_aggregated = (
        df_championship_teams_enriched.groupby(by=["owner_full_name", "owner_id"])
        .agg(championships_won=("championship_status", "count"))
        .reset_index()
    )

    dict_championships_aggregated = df_championships_aggregated.to_dict(
        orient="records"
    )
    dict_top_10_scores = top10.to_dict(orient="records")
    dict_bottom_10_scores = bottom10.to_dict(orient="records")
    dict_top_10_qb_scores = df_qb.to_dict(orient="records")
    dict_top_10_rb_scores = df_rb.to_dict(orient="records")
    dict_top_10_wr_scores = df_wr.to_dict(orient="records")
    dict_top_10_te_scores = df_te.to_dict(orient="records")
    dict_top_10_dst_scores = df_dst.to_dict(orient="records")
    dict_top_10_k_scores = df_k.to_dict(orient="records")

    return (
        dict_championships_aggregated,
        dict_top_10_scores,
        dict_bottom_10_scores,
        dict_top_10_qb_scores,
        dict_top_10_rb_scores,
        dict_top_10_wr_scores,
        dict_top_10_te_scores,
        dict_top_10_dst_scores,
        dict_top_10_k_scores,
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
    base_pk = f"LEAGUE#{league_id}#PLATFORM#{platform}"
    if standings_type == "owners":
        return {
            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
            "SK": {"S": f"OWNERS#{item['owner_id']}"},
            "owner_full_name": {"S": item["owner_full_name"]},
            "owner_id": {"S": item["owner_id"]},
        }
    elif standings_type == "season":
        return {
            "PK": {"S": f"{base_pk}#SEASON#{item['season']}"},
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
            "points_for_per_game": {"N": str(item["points_for_per_game"])},
            "points_against_per_game": {"N": str(item["points_against_per_game"])},
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
    elif standings_type == "weekly":
        return {
            "PK": {
                "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{item['season']}#WEEK#{item['week']}"
            },
            "SK": {"S": f"STANDINGS#WEEKLY#{item['team_owner_id']}"},
            "season": {"S": item["season"]},
            "week": {"N": str(item["week"])},
            "owner_id": {"S": item["team_owner_id"]},
            "owner_full_name": {"S": item["owner_full_name"]},
            "wins": {"N": str(item["wins"])},
            "losses": {"N": str(item["losses"])},
            "ties": {"N": str(item["ties"])},
        }
    elif standings_type == "all_time_championships":
        return {
            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
            "SK": {"S": f"HALL_OF_FAME#CHAMPIONSHIPS#{item['owner_id']}"},
            "owner_id": {"S": item["owner_id"]},
            "owner_full_name": {"S": item["owner_full_name"]},
            "championships_won": {"N": str(item["championships_won"])},
        }
    elif standings_type == "top_10_scores":
        return {
            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
            "SK": {
                "S": f"HALL_OF_FAME#TOP10TEAMSCORES#{item['owner_id']}#{item['season']}#{item['week']}"
            },
            "owner_id": {"S": item["owner_id"]},
            "owner_full_name": {"S": item["owner_name"]},
            "season": {"S": item["season"]},
            "week": {"N": str(item["week"])},
            "points_scored": {"N": str(item["score"])},
        }
    elif standings_type == "bottom_10_scores":
        return {
            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
            "SK": {
                "S": f"HALL_OF_FAME#BOTTOM10TEAMSCORES#{item['owner_id']}#{item['season']}#{item['week']}"
            },
            "owner_id": {"S": item["owner_id"]},
            "owner_full_name": {"S": item["owner_name"]},
            "season": {"S": item["season"]},
            "week": {"N": str(item["week"])},
            "points_scored": {"N": str(item["score"])},
        }
    elif standings_type == "top_10_qb_scores":
        return {
            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
            "SK": {
                "S": f"HALL_OF_FAME#TOP10PERFORMANCES#QB#{item['player_id']}#{item['season']}#{item['week']}"
            },
            "season": {"S": item["season"]},
            "week": {"N": str(item["week"])},
            "owner_id": {"S": item["owner_id"]},
            "owner_full_name": {"S": item["owner_full_name"]},
            "player_name": {"S": item["full_name"]},
            "points_scored": {"N": str(item["points_scored"])},
            "position": {"S": item["position"]},
        }
    elif standings_type == "top_10_rb_scores":
        return {
            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
            "SK": {
                "S": f"HALL_OF_FAME#TOP10PERFORMANCES#RB#{item['player_id']}#{item['season']}#{item['week']}"
            },
            "season": {"S": item["season"]},
            "week": {"N": str(item["week"])},
            "owner_id": {"S": item["owner_id"]},
            "owner_full_name": {"S": item["owner_full_name"]},
            "player_name": {"S": item["full_name"]},
            "points_scored": {"N": str(item["points_scored"])},
            "position": {"S": item["position"]},
        }
    elif standings_type == "top_10_wr_scores":
        return {
            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
            "SK": {
                "S": f"HALL_OF_FAME#TOP10PERFORMANCES#WR#{item['player_id']}#{item['season']}#{item['week']}"
            },
            "season": {"S": item["season"]},
            "week": {"N": str(item["week"])},
            "owner_id": {"S": item["owner_id"]},
            "owner_full_name": {"S": item["owner_full_name"]},
            "player_name": {"S": item["full_name"]},
            "points_scored": {"N": str(item["points_scored"])},
            "position": {"S": item["position"]},
        }
    elif standings_type == "top_10_te_scores":
        return {
            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
            "SK": {
                "S": f"HALL_OF_FAME#TOP10PERFORMANCES#TE#{item['player_id']}#{item['season']}#{item['week']}"
            },
            "season": {"S": item["season"]},
            "week": {"N": str(item["week"])},
            "owner_id": {"S": item["owner_id"]},
            "owner_full_name": {"S": item["owner_full_name"]},
            "player_name": {"S": item["full_name"]},
            "points_scored": {"N": str(item["points_scored"])},
            "position": {"S": item["position"]},
        }
    elif standings_type == "top_10_dst_scores":
        return {
            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
            "SK": {
                "S": f"HALL_OF_FAME#TOP10PERFORMANCES#DST#{item['player_id']}#{item['season']}#{item['week']}"
            },
            "season": {"S": item["season"]},
            "week": {"N": str(item["week"])},
            "owner_id": {"S": item["owner_id"]},
            "owner_full_name": {"S": item["owner_full_name"]},
            "player_name": {"S": item["full_name"]},
            "points_scored": {"N": str(item["points_scored"])},
            "position": {"S": item["position"]},
        }
    elif standings_type == "top_10_k_scores":
        return {
            "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
            "SK": {
                "S": f"HALL_OF_FAME#TOP10PERFORMANCES#K#{item['player_id']}#{item['season']}#{item['week']}"
            },
            "season": {"S": item["season"]},
            "week": {"N": str(item["week"])},
            "owner_id": {"S": item["owner_id"]},
            "owner_full_name": {"S": item["owner_full_name"]},
            "player_name": {"S": item["full_name"]},
            "points_scored": {"N": str(item["points_scored"])},
            "position": {"S": item["position"]},
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
    (
        all_time_championships,
        top_10_scores,
        bottom_10_scores,
        top_10_qb_scores,
        top_10_rb_scores,
        top_10_wr_scores,
        top_10_te_scores,
        top_10_dst_scores,
        top_10_k_scores,
    ) = compile_all_time_records(
        matchup_data=all_matchups,
        members_data=all_members,
        championship_team_data=all_championship_teams,
    )
    standings_mapping = {
        "owners": unique_members,
        "season": season_standings,
        "weekly": weekly_standings,
        "all_time": alltime_standings,
        "all_time_playoffs": alltime_standings_playoffs,
        "h2h": h2h_standings,
        "all_time_championships": all_time_championships,
        "top_10_scores": top_10_scores,
        "bottom_10_scores": bottom_10_scores,
        "top_10_qb_scores": top_10_qb_scores,
        "top_10_rb_scores": top_10_rb_scores,
        "top_10_wr_scores": top_10_wr_scores,
        "top_10_te_scores": top_10_te_scores,
        "top_10_dst_scores": top_10_dst_scores,
        "top_10_k_scores": top_10_k_scores,
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
