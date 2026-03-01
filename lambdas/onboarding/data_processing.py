"""
Module for processing league data using DuckDB.
"""

from typing import Any

import duckdb
import pandas as pd

from utils.logging_config import logger

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


def join_league_members_to_teams(
    members: list[dict], teams: list[dict], season: str
) -> pd.DataFrame:
    """
    Helper function to join teams and members responses into one data structure.

    Args:
        members: A list of dictionaries containing info about each member.
        teams: A list of dictionaries containing info about each team.

    Returns:
        pd.DataFrame: The resulting dataframe from joined data.

    Raises:
        ValueError: If either list of members or list of teams is empty.
    """
    df_members = pd.json_normalize(members)[
        ["displayName", "firstName", "lastName", "id"]
    ]
    df_teams = pd.json_normalize(teams)[["abbrev", "id", "name", "owners"]]

    with duckdb.connect(":memory:") as conn:
        conn.register("df_members", df_members)
        conn.register("df_teams", df_teams)

        query = f"""
        SELECT 
            '{season}' AS season,
            m.firstName AS owner_first_name,
            m.lastName AS owner_last_name,
            CONCAT(m.firstName, m.lastName) AS owner_full_name,
            t.abbrev AS abbreviation,
            CAST(t.id AS STRING) AS team_id,
            t.name AS team_name,
            m.id AS owner_id
        FROM df_teams t
        CROSS JOIN UNNEST(t.owners) AS _unzipped(owner_id)
        INNER JOIN df_members m ON m.id = owner_id
        """

        return conn.execute(query).df()


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
        lineup_limits: Mapping of position ID to number of starting spots.
        starting_players: List of starting players with their stats.
        bench_players: List of bench players with their stats.
        team_score: Total points scored by the team in the matchup.

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

            # Get the highest scorer among eligible remaining players
            best_player = max(
                eligible_players, key=lambda x: float(x.get("points_scored", 0))
            )

            optimal_score += float(best_player.get("points_scored", 0))
            all_players.remove(best_player)

    return team_score / round(optimal_score, 2)


def process_league_scores(
    matchups: list[dict[str, Any]],
    df_members: pd.DataFrame,
    lineup_limits_data: dict[str, int],
    season: str,
) -> pd.DataFrame:
    """
    Extracts relevant fields from fantasy matchup scores.

    Args:
        matchups: Raw list of dictionaries with all matchups for the league that season.
        members: Dataframe with league member and team information.
        lineup_limits_data: Mapping of position ID to number of starting spots.
        season: The fantasy football season that matchups occurred in.

    Returns:
        pd.DataFrame: Dataframe containing fantasy matchups for season.
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

        # Determine winner in terms of home/away team
        if float(home_score) > float(away_score):
            winner = home_team
            loser = away_team
        elif float(home_score) > float(away_score):
            winner = away_team
            loser = home_team
        else:
            winner = "TIE"
            loser = "TIE"

        # Calculate lineup efficiency for both teams
        if int(season) >= 2018:
            home_team_lineup_efficiency = calculate_lineup_efficiency(
                lineup_limits=lineup_limits_data,
                starting_players=starting_players_home_stats,
                bench_players=bench_players_home_stats,
                team_score=float(home_score),
            )
            away_team_lineup_efficiency = calculate_lineup_efficiency(
                lineup_limits=lineup_limits_data,
                starting_players=starting_players_away_stats,
                bench_players=bench_players_away_stats,
                team_score=float(away_score),
            )
        else:
            home_team_lineup_efficiency = 1.0
            away_team_lineup_efficiency = 1.0

        matchup_result = {
            "home_team": str(home_team),
            "home_team_score": home_score,
            "home_team_starting_players": starting_players_home_stats,
            "home_team_bench_players": bench_players_home_stats,
            "home_team_efficiency": home_team_lineup_efficiency,
            "away_team": str(away_team),
            "away_team_score": away_score,
            "away_team_starting_players": starting_players_away_stats,
            "away_team_bench_players": bench_players_away_stats,
            "away_team_efficiency": away_team_lineup_efficiency,
            "playoff_tier_type": matchup.get("playoffTierType", ""),
            "winner": winner,
            "loser": loser,
            "matchup_week": week,
            "season": season,
        }
        processed_matchup_results.append(matchup_result)

    df_matchup_results = pd.DataFrame(processed_matchup_results)

    with duckdb.connect(":memory:") as conn:
        conn.register("df_matchup_results", df_matchup_results)
        conn.register("df_members", df_members)
        query = """
        SELECT 
            CAST(m.home_team AS STRING),
            m.home_team_score,
            CAST(m.home_team_starting_players AS JSON) AS home_team_starting_players,
            CAST(m.home_team_bench_players AS JSON) AS home_team_bench_players,
            m.home_team_efficiency,
            CAST(m.away_team AS STRING),
            m.away_team_score,
            CAST(m.away_team_starting_players AS JSON) AS away_team_starting_players,
            CAST(m.away_team_bench_players AS JSON) AS away_team_bench_players,
            m.away_team_efficiency,
            mh.owner_full_name AS home_team_full_name,
            mh.team_name AS home_team_team_name,
            ma.owner_full_name AS away_team_full_name,
            ma.team_name AS away_team_team_name
        FROM df_matchup_results m
        INNER JOIN df_members mh ON m.home_team = mh.team_id
        INNER JOIN df_members ma ON m.away_team = ma.team_id
        """

        return conn.execute(query).df()


def process_player_scoring_totals(
    player_totals: list[dict[str, Any]],
    season: str,
) -> list[dict[str, Any]]:
    """
    Process raw player scoring totals data to get relevant information.

    Args:
        player_totals: List of dictionaries containing fantasy scoring totals
            for each available player in the fantasy league.
        season: The NFL season the data is for.

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
    df_teams: pd.DataFrame,
    season: str,
) -> pd.DataFrame:
    """
    Join draft results for season with player scoring totals to get comparison of player draft position
        to final season rank among position and overall. Additionally, join data with league owner ID
        mapping to associate an owner name with a draft pick.

    Args:
        draft_results: List of dictionary mappings containing league draft results.
        player_totals: List of dictionary mappings containing player scoring totals.
        teams: Dataframe with league member and team information.
        season: The fantasy football season that the draft was for.

    Returns:
        pd.DataFrame: Dataframe containing draft results and player finishes for season.
    """
    # Read source data into dataframes
    df_draft_results = pd.DataFrame(draft_results)
    df_player_totals = pd.DataFrame(player_totals)

    with duckdb.connect(":memory:") as conn:
        conn.register("draft_results", df_draft_results)
        conn.register("player_totals", df_player_totals)
        conn.register("df_teams", df_teams)
        query = """
        WITH processed_teams AS (
            SELECT 
                team_id,
                owner_full_name,
                CASE 
                    WHEN CAST(typeof(df_teams.owner_id) AS VARCHAR) LIKE 'LIST%'
                    THEN df_teams.owner_id[1]
                    ELSE df_teams.owner_id 
                END AS cleaned_owner_id
            FROM df_teams
        ),
        ranked_players AS (
            SELECT *,
                DENSE_RANK() OVER(PARTITION BY position ORDER BY total_points DESC) as position_rank,
                COUNT(*) OVER(PARTITION BY position) as total_players_at_position
            FROM player_totals
        ),
        joined_data AS (
            SELECT 
                p.*,
                d.autoDraftTypeId AS auto_draft_type_id,
                d.bidAmount AS bid_amount,
                d.overallPickNumber AS overall_pick_number,
                d.reservedForKeeper AS reserved_for_keeper,
                d.roundId AS round,
                d.roundPickNumber AS round_pick_number,
                d.tradeLocked AS trade_locked,
                t.owner_full_name,
                t.cleaned_owner_id AS owner_id,
                CASE 
                    WHEN d.autoDraftTypeId IS NOT NULL 
                    THEN ROW_NUMBER() OVER(PARTITION BY p.position ORDER BY d.overallPickNumber) 
                END AS position_draft_rank
            FROM ranked_players p
            LEFT JOIN draft_results d ON p.player_id = d.playerId
            LEFT JOIN processed_teams t ON CAST(d.teamId AS VARCHAR) = CAST(t.team_id AS VARCHAR)
        )
        SELECT 
            *,
            (CAST(position_draft_rank AS INTEGER) - CAST(position_rank AS INTEGER)) AS draft_position_rank_delta
        FROM joined_data
        WHERE auto_draft_type_id IS NOT NULL 
        AND overall_pick_number IS NOT NULL
        """

        return conn.execute(query).df()
