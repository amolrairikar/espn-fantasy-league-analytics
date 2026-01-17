"""Script to fetch matchup scores within an ESPN fantasy football league."""

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
POSITION_LINEUP_SPOT_MAPPING = {
    0: ["QB"],
    2: ["RB"],
    4: ["WR"],
    6: ["TE"],
    16: ["D/ST"],
    17: ["K"],
    23: ["RB", "WR", "TE"],  # Assumes position ID 23 is regular FLEX
}
POSITION_LINEUP_SPOT_NAMES = {
    0: "QB",
    2: "RB",
    4: "WR",
    6: "TE",
    16: "D/ST",
    17: "K",
    23: "FLEX",
}


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


def create_team_id_member_id_mapping(
    members_mapping: list[dict[str, Any]],
) -> dict[str, str]:
    """
    Creates a mapping of a team ID to a member ID.

    Args:
        members_mapping (list[dict[str, Any]]): A list of mappings containing info about league members.

    Returns:
        dict: A mapping of team_id to member_id.
    """
    result: dict[str, str] = {}
    for mapping in members_mapping:
        team_id = mapping["SK"].split("#")[-1]
        owner_id = mapping["owner_id"][0]
        result[team_id] = owner_id
    return result


def get_league_scores(
    league_id: str,
    platform: str,
    privacy: str,
    season: str,
    swid_cookie: Optional[str],
    espn_s2_cookie: Optional[str],
) -> list:
    """
    Fetch league matchup scores for a fantasy football league in a given season.

    Args:
        league_id (str): The unique ID of the fantasy football league.
        platform (str): The platform the fantasy football league is on (e.g., ESPN, Sleeper).
        privacy (str): The privacy setting of the league (e.g., public, private).
        season (str): The NFL season to get data for.
        swid_cookie (Optional[str]): The SWID cookie used for getting ESPN private league data.
        espn_s2_cookie (Optional[str]): The espn S2 cookie used for getting ESPN private league data.

    Returns:
        list: A list containing data for each matchup in the season.

    Raises:
        ValueError: If unsupported platform is specified, or if a required ESPN cookie is missing.
        requests.RequestException: If an error occurs while making API request.
        Exception: If uncaught exception occurs.
    """
    if platform == "ESPN":
        if privacy == "private" and (not swid_cookie or not espn_s2_cookie):
            raise ValueError("Missing required SWID and/or ESPN S2 cookies")
        weeks = range(1, 18, 1) if int(season) < 2021 else range(1, 19, 1)
        scores: list[dict[str, Any]] = []
        for week in weeks:
            base_params = [
                ("scoringPeriodId", str(week)),
                ("view", "mBoxscore"),
                ("view", "mMatchupScore"),
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
            logger.info("Successfully got league score info")
            weekly_scores = response.get("schedule", [])
            filtered_weekly_scores = [
                d for d in weekly_scores if d.get("matchupPeriodId") == week
            ]
            logger.info(
                "Found %d matchups in league for %s season week %s",
                len(filtered_weekly_scores),
                season,
                week,
            )
            scores.extend(filtered_weekly_scores)
        return scores
    else:
        raise ValueError("Unsupported platform. Only ESPN is currently supported.")


def get_league_lineup_settings(
    league_id: str,
    platform: str,
    privacy: str,
    season: str,
    swid_cookie: Optional[str],
    espn_s2_cookie: Optional[str],
) -> dict[str, int]:
    """
    Fetch league lineup settings for a fantasy football league in a given season.

    Args:
        league_id (str): The unique ID of the fantasy football league.
        platform (str): The platform the fantasy football league is on (e.g., ESPN, Sleeper).
        privacy (str): The privacy setting of the league (e.g., public, private).
        season (str): The NFL season to get data for.
        swid_cookie (Optional[str]): The SWID cookie used for getting ESPN private league data.
        espn_s2_cookie (Optional[str]): The espn S2 cookie used for getting ESPN private league data.

    Returns:
        dict: A mapping of position ID to number of starting spots.

    Raises:
        ValueError: If unsupported platform is specified, or if a required ESPN cookie is missing.
        requests.RequestException: If an error occurs while making API request.
        Exception: If uncaught exception occurs.
    """
    if platform == "ESPN":
        if privacy == "private" and (not swid_cookie or not espn_s2_cookie):
            raise ValueError("Missing required SWID and/or ESPN S2 cookies")
        settings: dict[str, int] = {}
        base_params = [
            ("view", "mSettings"),
            ("view", "mTeam"),
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
        logger.info("Successfully got league settings info")
        settings = (
            response.get("settings", {})
            .get("rosterSettings", {})
            .get("lineupSlotCounts", {})
        )
        return settings
    else:
        raise ValueError("Unsupported platform. Only ESPN is currently supported.")


def safe_int(team_id: str) -> int:
    """
    Convert team_id to int if possible, else use a very large int.

    Args:
        team_id (str): The team_id to convert to an integer. Can be a valid number or empty string "".

    Returns:
        int: The team_id converted to its integer value or a large number.
    """
    try:
        return int(team_id)
    except (ValueError, TypeError):
        return 10**12


def calculate_lineup_efficiency(
    lineup_limits: dict[str, int],
    starting_players: list[dict[str, Any]],
    bench_players: list[dict[str, Any]],
    team_score: float,
) -> float:
    """
    Calculates lineup efficiency for a given team in a matchup by comparing starting lineup points
    to the optimal starting lineup.

    Args:
        lineup_limits (dict[str, int]): Mapping of position ID to number of starting spots.
        starting_players (list[dict[str, Any]]): List of starting players with their stats.
        bench_players (list[dict[str, Any]]): List of bench players with their stats.
        team_score (float): Total points scored by the team in the matchup.

    Returns:
        float: The lineup efficiency as a ratio of actual score to optimal score.
    """
    all_players = starting_players + bench_players
    if not all_players:
        return 1.0
    optimal_score: float = 0.0

    # Filter lineup spots to only those with non-zero limits
    lineup_limits = {k: v for k, v in lineup_limits.items() if v > 0}

    # Sort the lineup spots so slots with fewer eligible positions are filled first
    sorted_lineup_spots = sorted(
        lineup_limits.items(),
        key=lambda x: len(POSITION_LINEUP_SPOT_MAPPING.get(int(x[0]), [])),
    )

    for lineup_spot, num_spots in sorted_lineup_spots:
        if int(lineup_spot) not in POSITION_LINEUP_SPOT_MAPPING:
            continue
        valid_positions = POSITION_LINEUP_SPOT_MAPPING.get(int(lineup_spot), [])

        for _ in range(num_spots):
            # Re-filter and re-sort inside the loop to get the current best available
            eligible_players = [
                p for p in all_players if p["position"] in valid_positions
            ]

            if not eligible_players:
                break
            logger.info(
                "Eligible players for lineup spot %s: %s",
                POSITION_LINEUP_SPOT_NAMES[int(lineup_spot)],
                eligible_players,
            )

            # Get the highest scorer among eligible remaining players
            best_player = max(
                eligible_players, key=lambda x: float(x.get("points_scored", 0))
            )
            logger.info(
                "Selected player %s with score %s for lineup spot %s",
                best_player["full_name"],
                float(best_player.get("points_scored", 0)),
                POSITION_LINEUP_SPOT_NAMES[int(lineup_spot)],
            )

            optimal_score += float(best_player.get("points_scored", 0))
            all_players.remove(best_player)  # Mark as used

    return team_score / round(optimal_score, 2)


def process_league_scores(
    matchups: list[dict[str, Any]],
    members: list[dict[str, Any]],
    lineup_limits_data: dict[str, int],
    season: str,
) -> list:
    """
    Extracts relevant fields from fantasy matchup scores.

    Args:
        matchups (list[dict[str, Any]]): Raw list of dictionaries with all matchups
            for the league that season.
        members (list[dict[str, Any]]): Raw list of dictionaries with all members for
            the league that season.
        lineup_limits_data (dict[str, int]): Mapping of position ID to number of starting spots.
        season (str): The fantasy football season that matchups occurred in.

    Returns:
        list: Processed dictionary with relevant data from fantasy matchup scores.
    """
    processed_matchup_results = []
    for matchup in matchups:
        home_team = matchup.get("home", {}).get("teamId", "")
        home_score = matchup.get("home", {}).get("totalPoints", "0.00")
        away_team = matchup.get("away", {}).get("teamId", "")
        away_score = matchup.get("away", {}).get("totalPoints", "0.00")
        week = matchup.get("matchupPeriodId", "")

        # Get starting players and their stats
        starting_players_home = matchup.get("home", {}).get(
            "rosterForMatchupPeriod", {}
        )
        starting_players_home_stats: list[dict[str, Any]] = []
        starting_players_home_ids: list[str] = []
        starting_players_away = matchup.get("away", {}).get(
            "rosterForMatchupPeriod", {}
        )
        starting_players_away_stats: list[dict[str, Any]] = []
        starting_players_away_ids: list[str] = []
        for player in starting_players_home.get("entries", []):
            player_stats = {}
            player_stats["player_id"] = player["playerId"]
            player_stats["full_name"] = player["playerPoolEntry"]["player"]["fullName"]
            player_stats["points_scored"] = player["playerPoolEntry"][
                "appliedStatTotal"
            ]
            player_stats["position"] = POSITION_ID_MAPPING[
                player["playerPoolEntry"]["player"]["defaultPositionId"]
            ]
            starting_players_home_stats.append(player_stats)
            starting_players_home_ids.append(player["playerId"])
        for player in starting_players_away.get("entries", []):
            player_stats = {}
            player_stats["player_id"] = player["playerId"]
            player_stats["full_name"] = player["playerPoolEntry"]["player"]["fullName"]
            player_stats["points_scored"] = player["playerPoolEntry"][
                "appliedStatTotal"
            ]
            player_stats["position"] = POSITION_ID_MAPPING[
                player["playerPoolEntry"]["player"]["defaultPositionId"]
            ]
            starting_players_away_stats.append(player_stats)
            starting_players_away_ids.append(player["playerId"])

        # Get bench players and their stats
        bench_players_home = matchup.get("home", {}).get(
            "rosterForCurrentScoringPeriod", {}
        )
        bench_players_home_stats: list[dict[str, Any]] = []
        bench_players_away = matchup.get("away", {}).get(
            "rosterForCurrentScoringPeriod", {}
        )
        bench_players_away_stats: list[dict[str, Any]] = []
        for player in bench_players_home.get("entries", []):
            player_id = player["playerId"]
            if player_id in starting_players_home_ids:
                continue
            player_stats = {}
            player_stats["player_id"] = player_id
            player_stats["full_name"] = player["playerPoolEntry"]["player"]["fullName"]
            player_stats["points_scored"] = player["playerPoolEntry"][
                "appliedStatTotal"
            ]
            player_stats["position"] = POSITION_ID_MAPPING[
                player["playerPoolEntry"]["player"]["defaultPositionId"]
            ]
            bench_players_home_stats.append(player_stats)
        for player in bench_players_away.get("entries", []):
            player_id = player["playerId"]
            if player_id in starting_players_away_ids:
                continue
            player_stats = {}
            player_stats["player_id"] = player_id
            player_stats["full_name"] = player["playerPoolEntry"]["player"]["fullName"]
            player_stats["points_scored"] = player["playerPoolEntry"][
                "appliedStatTotal"
            ]
            player_stats["position"] = POSITION_ID_MAPPING[
                player["playerPoolEntry"]["player"]["defaultPositionId"]
            ]
            bench_players_away_stats.append(player_stats)

        # Skip matchups where both teams scored 0 (these are future weeks)
        if float(home_score) == 0.0 and float(away_score) == 0.0:
            logger.info(
                "Skipping matchups between team %s and team %s for week %s",
                home_team,
                away_team,
                week,
            )
            continue

        # Canonicalize: team_a ID < team_b ID
        team_a, team_b = sorted([home_team, away_team], key=safe_int)
        if team_a == home_team:
            team_a_score = home_score
            team_a_starting_players = starting_players_home_stats
            team_a_bench_players = bench_players_home_stats
            team_b_score = away_score
            team_b_starting_players = starting_players_away_stats
            team_b_bench_players = bench_players_away_stats
        else:
            team_a_score = away_score
            team_a_starting_players = starting_players_away_stats
            team_a_bench_players = bench_players_away_stats
            team_b_score = home_score
            team_b_starting_players = starting_players_home_stats
            team_b_bench_players = bench_players_home_stats

        # Determine winner in terms of team_a/team_b
        if float(team_a_score) > float(team_b_score):
            winner = team_a
            loser = team_b
        elif float(team_b_score) > float(team_a_score):
            winner = team_b
            loser = team_a
        else:
            winner = "TIE"
            loser = "TIE"

        # Calculate lineup efficiency for both teams
        if int(season) >= 2018:
            team_a_lineup_efficiency = calculate_lineup_efficiency(
                lineup_limits=lineup_limits_data,
                starting_players=team_a_starting_players,
                bench_players=team_a_bench_players,
                team_score=float(team_a_score),
            )
            team_b_lineup_efficiency = calculate_lineup_efficiency(
                lineup_limits=lineup_limits_data,
                starting_players=team_b_starting_players,
                bench_players=team_b_bench_players,
                team_score=float(team_b_score),
            )
        else:
            team_a_lineup_efficiency = 1.0
            team_b_lineup_efficiency = 1.0

        matchup_result = {
            "team_a": str(team_a),
            "team_b": str(team_b),
            "team_a_score": team_a_score,
            "team_b_score": team_b_score,
            "team_a_starting_players": team_a_starting_players,
            "team_a_bench_players": team_a_bench_players,
            "team_a_efficiency": team_a_lineup_efficiency,
            "team_b_starting_players": team_b_starting_players,
            "team_b_bench_players": team_b_bench_players,
            "team_b_efficiency": team_b_lineup_efficiency,
            "playoff_tier_type": matchup.get("playoffTierType", ""),
            "winner": winner,
            "loser": loser,
            "matchup_week": week,
        }
        processed_matchup_results.append(matchup_result)

    df_matchup_results = pd.DataFrame(processed_matchup_results)
    df_members = pd.DataFrame(members)
    df_members["full_name"] = (
        df_members["owner_first_name"] + " " + df_members["owner_last_name"]
    )
    df_matchup_results = df_matchup_results.merge(
        df_members[["team_id", "owner_full_name", "team_name"]],
        left_on="team_a",
        right_on="team_id",
        how="inner",
    )
    df_matchup_results = df_matchup_results.drop(columns=["team_id"])
    df_matchup_results = df_matchup_results.rename(
        columns={
            "full_name": "team_a_full_name",
            "team_name": "team_a_team_name",
        }
    )
    df_matchup_results = df_matchup_results.merge(
        df_members[["team_id", "full_name", "team_name"]],
        left_on="team_b",
        right_on="team_id",
        how="inner",
    )
    df_matchup_results = df_matchup_results.drop(columns=["team_id"])
    df_matchup_results = df_matchup_results.rename(
        columns={
            "full_name": "team_b_full_name",
            "team_name": "team_b_team_name",
        }
    )
    results = df_matchup_results.to_dict(orient="records")

    return results


def get_playoff_status(
    matchups: list[dict[str, Any]], season: str
) -> tuple[list, list]:
    """
    Gets playoff status for each team per season.

    Args:
        matchups (list[dict[str, Any]]): Raw list of dictionaries with all matchups
            for the league that season.
        season (str): The fantasy football season that matchups occurred in.

    Returns:
        tuple: Pair of list of dictionaries with playoff teams and league champion for a given season.
    """
    playoff_teams = []
    league_champion = []
    for matchup in matchups:
        if matchup.get("playoffTierType", "") != "NONE":
            if int(season) < 2021:
                if (
                    matchup.get("matchupPeriodId", 0) == 14
                    and matchup.get("playoffTierType", "") == "WINNERS_BRACKET"
                ):
                    first_round_home_team = {}
                    first_round_away_team = {}
                    home_team_id = matchup.get("home", {}).get("teamId", "")
                    away_team_id = matchup.get("away", {}).get("teamId", "")
                    if home_team_id and away_team_id:
                        first_round_home_team["team_id"] = home_team_id
                        first_round_home_team["playoff_status"] = "MADE_PLAYOFFS"
                        first_round_away_team["team_id"] = away_team_id
                        first_round_away_team["playoff_status"] = "MADE_PLAYOFFS"
                        playoff_teams.append(first_round_home_team)
                        playoff_teams.append(first_round_away_team)
                if (
                    matchup.get("matchupPeriodId", 0) == 15
                    and matchup.get("playoffTierType", "") == "WINNERS_BRACKET"
                ):
                    second_round_home_team = {}
                    second_round_home_team["team_id"] = matchup.get("home", {}).get(
                        "teamId", ""
                    )
                    second_round_home_team["playoff_status"] = (
                        "CLINCHED_FIRST_ROUND_BYE"
                    )
                    playoff_teams.append(second_round_home_team)
                if (
                    matchup.get("matchupPeriodId", 0) == 16
                    and matchup.get("playoffTierType", "") == "WINNERS_BRACKET"
                ):
                    championship_team = {}
                    home_team = matchup.get("home", {}).get("teamId", "")
                    home_score = matchup.get("home", {}).get("totalPoints", "0.00")
                    away_team = matchup.get("away", {}).get("teamId", "")
                    away_score = matchup.get("away", {}).get("totalPoints", "0.00")
                    if float(home_score) > float(away_score):
                        championship_team["team_id"] = home_team
                    else:
                        championship_team["team_id"] = away_team
                    championship_team["championship_status"] = "LEAGUE_CHAMPION"
                    league_champion.append(championship_team)
            if int(season) >= 2021:
                if (
                    matchup.get("matchupPeriodId", 0) == 15
                    and matchup.get("playoffTierType", "") == "WINNERS_BRACKET"
                ):
                    first_round_home_team = {}
                    first_round_away_team = {}
                    home_team_id = matchup.get("home", {}).get("teamId", "")
                    away_team_id = matchup.get("away", {}).get("teamId", "")
                    if home_team_id and away_team_id:
                        first_round_home_team["team_id"] = home_team_id
                        first_round_home_team["playoff_status"] = "MADE_PLAYOFFS"
                        first_round_away_team["team_id"] = away_team_id
                        first_round_away_team["playoff_status"] = "MADE_PLAYOFFS"
                        playoff_teams.append(first_round_home_team)
                        playoff_teams.append(first_round_away_team)
                if (
                    matchup.get("matchupPeriodId", 0) == 16
                    and matchup.get("playoffTierType", "") == "WINNERS_BRACKET"
                ):
                    second_round_home_team = {}
                    second_round_home_team["team_id"] = matchup.get("home", {}).get(
                        "teamId", ""
                    )
                    second_round_home_team["playoff_status"] = (
                        "CLINCHED_FIRST_ROUND_BYE"
                    )
                    playoff_teams.append(second_round_home_team)
                if (
                    matchup.get("matchupPeriodId", 0) == 17
                    and matchup.get("playoffTierType", "") == "WINNERS_BRACKET"
                ):
                    championship_team = {}
                    home_team = matchup.get("home", {}).get("teamId", "")
                    home_score = matchup.get("home", {}).get("totalPoints", "0.00")
                    away_team = matchup.get("away", {}).get("teamId", "")
                    away_score = matchup.get("away", {}).get("totalPoints", "0.00")
                    if float(home_score) > float(away_score):
                        championship_team["team_id"] = home_team
                    else:
                        championship_team["team_id"] = away_team
                    championship_team["championship_status"] = "LEAGUE_CHAMPION"
                    league_champion.append(championship_team)
    return playoff_teams, league_champion


def lambda_handler(event, context):
    """Lambda handler function to get league members and teams."""
    logger.info("Received event: %s", event)
    league_id = event["leagueId"]
    platform = event["platform"]
    privacy = event["privacy"]
    swid_cookie = event["swidCookie"]
    espn_s2_cookie = event["espnS2Cookie"]
    season = event["season"]

    members = get_league_members(
        league_id=league_id,
        platform=platform,
        season=season,
    )
    member_id_mapping = create_team_id_member_id_mapping(members_mapping=members)

    matchups = get_league_scores(
        league_id=league_id,
        platform=platform,
        privacy=privacy,
        season=season,
        swid_cookie=swid_cookie,
        espn_s2_cookie=espn_s2_cookie,
    )
    if not matchups:
        raise ValueError("'matchups' list must not be empty.")

    logger.info("Processing raw matchup data")
    lineup_limits_data = get_league_lineup_settings(
        league_id=league_id,
        platform=platform,
        privacy=privacy,
        season=season,
        swid_cookie=swid_cookie,
        espn_s2_cookie=espn_s2_cookie,
    )
    scores_data = process_league_scores(
        matchups=matchups,
        members=members,
        lineup_limits_data=lineup_limits_data,
        season=season,
    )
    playoff_teams, league_champion = get_playoff_status(
        matchups=matchups, season=season
    )
    data_mapping = {
        "matchups": scores_data,
        "playoff_teams": playoff_teams,
        "league_champion": league_champion,
    }
    for data_type, data in data_mapping.items():
        logger.info("Processing %s data", data_type)
        batched_objects = []
        for item in data:
            if data_type == "matchups":
                team_a_member_id = member_id_mapping.get(str(item["team_a"]), "")
                team_b_member_id = member_id_mapping.get(str(item["team_b"]), "")
                winning_member_id = member_id_mapping.get(str(item["winner"]), "")
                losing_member_id = member_id_mapping.get(str(item["loser"]), "")
                batched_objects.append(
                    {
                        "PutRequest": {
                            "Item": {
                                "PK": {
                                    "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"
                                },
                                "SK": {
                                    "S": f"MATCHUP#TEAMS#{team_a_member_id}-vs-{team_b_member_id}#WEEK#{str(item['matchup_week'])}"
                                },
                                "GSI1PK": {
                                    "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#MATCHUP#{team_a_member_id}-vs-{team_b_member_id}"
                                },
                                "GSI1SK": {
                                    "S": f"SEASON#{season}#WEEK#{item['matchup_week']}"
                                },
                                "GSI3PK": {
                                    "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}#WEEK#{item['matchup_week']}"
                                },
                                "GSI3SK": {
                                    "S": f"MATCHUP#{team_a_member_id}-vs-{team_b_member_id}"
                                },
                                "season": {"S": str(season)},
                                "week": {"S": str(item["matchup_week"])},
                                "playoff_tier_type": {"S": item["playoff_tier_type"]},
                                "winner": {"S": winning_member_id},
                                "loser": {"S": losing_member_id},
                                "team_a_id": {"S": str(item["team_a"])},
                                "team_a_owner_full_name": {
                                    "S": str(item["owner_full_name"])
                                },
                                "team_a_owner_id": {"S": team_a_member_id},
                                "team_a_team_name": {
                                    "S": str(item["team_a_team_name"])
                                },
                                "team_a_score": {
                                    "N": str(
                                        Decimal(item["team_a_score"]).quantize(
                                            Decimal("0.01"), rounding=ROUND_HALF_UP
                                        )
                                    ),
                                },
                                "team_a_starting_players": {
                                    "L": [
                                        {
                                            "M": {
                                                "player_id": {
                                                    "S": str(player["player_id"])
                                                },
                                                "full_name": {
                                                    "S": str(player["full_name"])
                                                },
                                                "points_scored": {
                                                    "N": str(
                                                        Decimal(
                                                            player["points_scored"]
                                                        ).quantize(
                                                            Decimal("0.01"),
                                                            rounding=ROUND_HALF_UP,
                                                        )
                                                    )
                                                },
                                                "position": {
                                                    "S": str(player["position"])
                                                },
                                            }
                                        }
                                        for player in item["team_a_starting_players"]
                                    ]
                                },
                                "team_a_bench_players": {
                                    "L": [
                                        {
                                            "M": {
                                                "player_id": {
                                                    "S": str(player["player_id"])
                                                },
                                                "full_name": {
                                                    "S": str(player["full_name"])
                                                },
                                                "points_scored": {
                                                    "N": str(
                                                        Decimal(
                                                            player["points_scored"]
                                                        ).quantize(
                                                            Decimal("0.01"),
                                                            rounding=ROUND_HALF_UP,
                                                        )
                                                    )
                                                },
                                                "position": {
                                                    "S": str(player["position"])
                                                },
                                            }
                                        }
                                        for player in item["team_a_bench_players"]
                                    ]
                                },
                                "team_a_efficiency": {
                                    "N": str(
                                        Decimal(item["team_a_efficiency"]).quantize(
                                            Decimal("0.0001"), rounding=ROUND_HALF_UP
                                        )
                                    ),
                                },
                                "team_b_id": {"S": str(item["team_b"])},
                                "team_b_owner_full_name": {
                                    "S": str(item["team_b_full_name"])
                                },
                                "team_b_owner_id": {"S": team_b_member_id},
                                "team_b_team_name": {
                                    "S": str(item["team_b_team_name"])
                                },
                                "team_b_score": {
                                    "N": str(
                                        Decimal(item["team_b_score"]).quantize(
                                            Decimal("0.01"), rounding=ROUND_HALF_UP
                                        )
                                    ),
                                },
                                "team_b_starting_players": {
                                    "L": [
                                        {
                                            "M": {
                                                "player_id": {
                                                    "S": str(player["player_id"])
                                                },
                                                "full_name": {
                                                    "S": str(player["full_name"])
                                                },
                                                "points_scored": {
                                                    "N": str(
                                                        Decimal(
                                                            player["points_scored"]
                                                        ).quantize(
                                                            Decimal("0.01"),
                                                            rounding=ROUND_HALF_UP,
                                                        )
                                                    )
                                                },
                                                "position": {
                                                    "S": str(player["position"])
                                                },
                                            }
                                        }
                                        for player in item["team_b_starting_players"]
                                    ]
                                },
                                "team_b_bench_players": {
                                    "L": [
                                        {
                                            "M": {
                                                "player_id": {
                                                    "S": str(player["player_id"])
                                                },
                                                "full_name": {
                                                    "S": str(player["full_name"])
                                                },
                                                "points_scored": {
                                                    "N": str(
                                                        Decimal(
                                                            player["points_scored"]
                                                        ).quantize(
                                                            Decimal("0.01"),
                                                            rounding=ROUND_HALF_UP,
                                                        )
                                                    )
                                                },
                                                "position": {
                                                    "S": str(player["position"])
                                                },
                                            }
                                        }
                                        for player in item["team_b_bench_players"]
                                    ]
                                },
                                "team_b_efficiency": {
                                    "N": str(
                                        Decimal(item["team_b_efficiency"]).quantize(
                                            Decimal("0.0001"), rounding=ROUND_HALF_UP
                                        )
                                    ),
                                },
                            }
                        }
                    }
                )
                # Create an individual record per team so that we can query a single team's games for a season
                batched_objects.append(
                    {
                        "PutRequest": {
                            "Item": {
                                "PK": {
                                    "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"
                                },
                                "SK": {
                                    "S": f"MATCHUP#TEAM#{team_a_member_id}#WEEK#{str(item['matchup_week'])}"
                                },
                                "GSI4PK": {
                                    "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#MATCHUP#TEAM#{team_a_member_id}"
                                },
                                "GSI4SK": {
                                    "S": f"SEASON#{season}#WEEK#{item['matchup_week']}"
                                },
                                "season": {"S": str(season)},
                                "week": {"S": str(item["matchup_week"])},
                                "playoff_tier_type": {"S": item["playoff_tier_type"]},
                                "winner": {"S": winning_member_id},
                                "loser": {"S": losing_member_id},
                                "team_a_id": {"S": str(item["team_a"])},
                                "team_a_owner_full_name": {
                                    "S": str(item["owner_full_name"])
                                },
                                "team_a_owner_id": {"S": team_a_member_id},
                                "team_a_team_name": {
                                    "S": str(item["team_a_team_name"])
                                },
                                "team_a_score": {
                                    "N": str(
                                        Decimal(item["team_a_score"]).quantize(
                                            Decimal("0.01"), rounding=ROUND_HALF_UP
                                        )
                                    ),
                                },
                                "team_a_starting_players": {
                                    "L": [
                                        {
                                            "M": {
                                                "player_id": {
                                                    "S": str(player["player_id"])
                                                },
                                                "full_name": {
                                                    "S": str(player["full_name"])
                                                },
                                                "points_scored": {
                                                    "N": str(
                                                        Decimal(
                                                            player["points_scored"]
                                                        ).quantize(
                                                            Decimal("0.01"),
                                                            rounding=ROUND_HALF_UP,
                                                        )
                                                    )
                                                },
                                                "position": {
                                                    "S": str(player["position"])
                                                },
                                            }
                                        }
                                        for player in item["team_a_starting_players"]
                                    ]
                                },
                                "team_a_bench_players": {
                                    "L": [
                                        {
                                            "M": {
                                                "player_id": {
                                                    "S": str(player["player_id"])
                                                },
                                                "full_name": {
                                                    "S": str(player["full_name"])
                                                },
                                                "points_scored": {
                                                    "N": str(
                                                        Decimal(
                                                            player["points_scored"]
                                                        ).quantize(
                                                            Decimal("0.01"),
                                                            rounding=ROUND_HALF_UP,
                                                        )
                                                    )
                                                },
                                                "position": {
                                                    "S": str(player["position"])
                                                },
                                            }
                                        }
                                        for player in item["team_a_bench_players"]
                                    ]
                                },
                                "team_a_efficiency": {
                                    "N": str(
                                        Decimal(item["team_a_efficiency"]).quantize(
                                            Decimal("0.0001"), rounding=ROUND_HALF_UP
                                        )
                                    ),
                                },
                                "team_b_id": {"S": str(item["team_b"])},
                                "team_b_owner_full_name": {
                                    "S": str(item["team_b_full_name"])
                                },
                                "team_b_owner_id": {"S": team_b_member_id},
                                "team_b_team_name": {
                                    "S": str(item["team_b_team_name"])
                                },
                                "team_b_score": {
                                    "N": str(
                                        Decimal(item["team_b_score"]).quantize(
                                            Decimal("0.01"), rounding=ROUND_HALF_UP
                                        )
                                    ),
                                },
                                "team_b_starting_players": {
                                    "L": [
                                        {
                                            "M": {
                                                "player_id": {
                                                    "S": str(player["player_id"])
                                                },
                                                "full_name": {
                                                    "S": str(player["full_name"])
                                                },
                                                "points_scored": {
                                                    "N": str(
                                                        Decimal(
                                                            player["points_scored"]
                                                        ).quantize(
                                                            Decimal("0.01"),
                                                            rounding=ROUND_HALF_UP,
                                                        )
                                                    )
                                                },
                                                "position": {
                                                    "S": str(player["position"])
                                                },
                                            }
                                        }
                                        for player in item["team_b_starting_players"]
                                    ]
                                },
                                "team_b_bench_players": {
                                    "L": [
                                        {
                                            "M": {
                                                "player_id": {
                                                    "S": str(player["player_id"])
                                                },
                                                "full_name": {
                                                    "S": str(player["full_name"])
                                                },
                                                "points_scored": {
                                                    "N": str(
                                                        Decimal(
                                                            player["points_scored"]
                                                        ).quantize(
                                                            Decimal("0.01"),
                                                            rounding=ROUND_HALF_UP,
                                                        )
                                                    )
                                                },
                                                "position": {
                                                    "S": str(player["position"])
                                                },
                                            }
                                        }
                                        for player in item["team_b_bench_players"]
                                    ]
                                },
                                "team_b_efficiency": {
                                    "N": str(
                                        Decimal(item["team_b_efficiency"]).quantize(
                                            Decimal("0.0001"), rounding=ROUND_HALF_UP
                                        )
                                    ),
                                },
                            }
                        }
                    }
                )
                batched_objects.append(
                    {
                        "PutRequest": {
                            "Item": {
                                "PK": {
                                    "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"
                                },
                                "SK": {
                                    "S": f"MATCHUP#TEAM#{team_b_member_id}#WEEK#{str(item['matchup_week'])}"
                                },
                                "GSI4PK": {
                                    "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#MATCHUP#TEAM#{team_b_member_id}"
                                },
                                "GSI4SK": {
                                    "S": f"SEASON#{season}#WEEK#{item['matchup_week']}"
                                },
                                "season": {"S": str(season)},
                                "week": {"S": str(item["matchup_week"])},
                                "playoff_tier_type": {"S": item["playoff_tier_type"]},
                                "winner": {"S": winning_member_id},
                                "loser": {"S": losing_member_id},
                                "team_a_id": {"S": str(item["team_a"])},
                                "team_a_owner_full_name": {
                                    "S": str(item["owner_full_name"])
                                },
                                "team_a_owner_id": {"S": team_a_member_id},
                                "team_a_team_name": {
                                    "S": str(item["team_a_team_name"])
                                },
                                "team_a_score": {
                                    "N": str(
                                        Decimal(item["team_a_score"]).quantize(
                                            Decimal("0.01"), rounding=ROUND_HALF_UP
                                        )
                                    ),
                                },
                                "team_a_starting_players": {
                                    "L": [
                                        {
                                            "M": {
                                                "player_id": {
                                                    "S": str(player["player_id"])
                                                },
                                                "full_name": {
                                                    "S": str(player["full_name"])
                                                },
                                                "points_scored": {
                                                    "N": str(
                                                        Decimal(
                                                            player["points_scored"]
                                                        ).quantize(
                                                            Decimal("0.01"),
                                                            rounding=ROUND_HALF_UP,
                                                        )
                                                    )
                                                },
                                                "position": {
                                                    "S": str(player["position"])
                                                },
                                            }
                                        }
                                        for player in item["team_a_starting_players"]
                                    ]
                                },
                                "team_a_bench_players": {
                                    "L": [
                                        {
                                            "M": {
                                                "player_id": {
                                                    "S": str(player["player_id"])
                                                },
                                                "full_name": {
                                                    "S": str(player["full_name"])
                                                },
                                                "points_scored": {
                                                    "N": str(
                                                        Decimal(
                                                            player["points_scored"]
                                                        ).quantize(
                                                            Decimal("0.01"),
                                                            rounding=ROUND_HALF_UP,
                                                        )
                                                    )
                                                },
                                                "position": {
                                                    "S": str(player["position"])
                                                },
                                            }
                                        }
                                        for player in item["team_a_bench_players"]
                                    ]
                                },
                                "team_a_efficiency": {
                                    "N": str(
                                        Decimal(item["team_a_efficiency"]).quantize(
                                            Decimal("0.0001"), rounding=ROUND_HALF_UP
                                        )
                                    ),
                                },
                                "team_b_id": {"S": str(item["team_b"])},
                                "team_b_owner_full_name": {
                                    "S": str(item["team_b_full_name"])
                                },
                                "team_b_owner_id": {"S": team_b_member_id},
                                "team_b_team_name": {
                                    "S": str(item["team_b_team_name"])
                                },
                                "team_b_score": {
                                    "N": str(
                                        Decimal(item["team_b_score"]).quantize(
                                            Decimal("0.01"), rounding=ROUND_HALF_UP
                                        )
                                    ),
                                },
                                "team_b_starting_players": {
                                    "L": [
                                        {
                                            "M": {
                                                "player_id": {
                                                    "S": str(player["player_id"])
                                                },
                                                "full_name": {
                                                    "S": str(player["full_name"])
                                                },
                                                "points_scored": {
                                                    "N": str(
                                                        Decimal(
                                                            player["points_scored"]
                                                        ).quantize(
                                                            Decimal("0.01"),
                                                            rounding=ROUND_HALF_UP,
                                                        )
                                                    )
                                                },
                                                "position": {
                                                    "S": str(player["position"])
                                                },
                                            }
                                        }
                                        for player in item["team_b_starting_players"]
                                    ]
                                },
                                "team_b_bench_players": {
                                    "L": [
                                        {
                                            "M": {
                                                "player_id": {
                                                    "S": str(player["player_id"])
                                                },
                                                "full_name": {
                                                    "S": str(player["full_name"])
                                                },
                                                "points_scored": {
                                                    "N": str(
                                                        Decimal(
                                                            player["points_scored"]
                                                        ).quantize(
                                                            Decimal("0.01"),
                                                            rounding=ROUND_HALF_UP,
                                                        )
                                                    )
                                                },
                                                "position": {
                                                    "S": str(player["position"])
                                                },
                                            }
                                        }
                                        for player in item["team_b_bench_players"]
                                    ]
                                },
                                "team_b_efficiency": {
                                    "N": str(
                                        Decimal(item["team_b_efficiency"]).quantize(
                                            Decimal("0.0001"), rounding=ROUND_HALF_UP
                                        )
                                    ),
                                },
                            }
                        }
                    }
                )
            elif data_type == "playoff_teams":
                batched_objects.append(
                    {
                        "PutRequest": {
                            "Item": {
                                "PK": {
                                    "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"
                                },
                                "SK": {"S": f"PLAYOFF_TEAM#TEAM#{item['team_id']}"},
                                "team_id": {"S": str(item["team_id"])},
                                "season": {"S": str(season)},
                                "playoff_status": {"S": str(item["playoff_status"])},
                            }
                        }
                    }
                )
            elif data_type == "league_champion":
                batched_objects.append(
                    {
                        "PutRequest": {
                            "Item": {
                                "PK": {
                                    "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"
                                },
                                "SK": {"S": f"LEAGUE_CHAMPION#TEAM#{item['team_id']}"},
                                "team_id": {"S": str(item["team_id"])},
                                "season": {"S": str(season)},
                                "championship_status": {
                                    "S": str(item["championship_status"])
                                },
                            }
                        }
                    }
                )
        batch_write_to_dynamodb(
            batched_objects=batched_objects, table_name=DYNAMODB_TABLE_NAME
        )
        logger.info("Successfully processed %s data", data_type)
    logger.info("Successfully wrote data to DynamoDB.")
