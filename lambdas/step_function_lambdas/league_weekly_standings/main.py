"""Script to compile weekly league standings snapshots from fantasy league scores."""

from typing import Any

import pandas as pd
from boto3.dynamodb.types import TypeDeserializer

from common_utils.batch_write_dynamodb import batch_write_to_dynamodb
from common_utils.logging_config import logger
from common_utils.query_dynamodb import fetch_league_data

deserializer = TypeDeserializer()
DYNAMODB_TABLE_NAME = "fantasy-analytics-app-db"

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
    for season in seasons:
        logger.info("Processing season %s", season)
        matchups = fetch_league_data(
            pk=f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}",
            sk_prefix="MATCHUP#TEAMS#",
        )
        logger.info("Fetched %d matchups for season %s", len(matchups), season)
        all_matchups.extend(matchups)
        members = fetch_league_data(
            pk=f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}",
            sk_prefix="TEAM#",
        )
        logger.info("Fetched %d league members for season %s", len(members), season)
        all_members.extend(members)
    if not any([all_matchups, all_members]):
        raise ValueError("Empty list found for matchups and/or members.")
    weekly_standings = compile_weekly_standings_snapshots(
        matchup_data=all_matchups,
        members_data=all_members,
    )
    batched_records = []
    for item in weekly_standings:
        batched_records.append(
            {
                "PutRequest": {
                    "Item": {
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
                }
            }
        )
    batch_write_to_dynamodb(
        batched_objects=batched_records,
        table_name=DYNAMODB_TABLE_NAME,
    )
    logger.info("Successfully wrote weekly standings data to DynamoDB.")
