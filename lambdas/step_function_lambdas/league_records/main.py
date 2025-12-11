"""Script to compile all-time league records from fantasy league matchups."""

from decimal import Decimal
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
    if standings_type == "all_time_championships":
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
    all_championship_teams = []
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
        championship_team = fetch_league_data(
            pk=f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}",
            sk_prefix="LEAGUE_CHAMPION#",
        )
        logger.info("Fetched league champion for season %s", season)
        all_championship_teams.extend(championship_team)
    if not any([all_matchups, all_members, all_championship_teams]):
        raise ValueError(
            "Empty list found for matchups, members, playoff teams, and/or championship teams."
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
