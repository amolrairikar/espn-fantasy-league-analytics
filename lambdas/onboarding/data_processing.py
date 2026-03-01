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
        WITH owner_mapping AS (
            SELECT 
                firstName, 
                lastName, 
                id AS original_owner_id,
                ROW_NUMBER() OVER (PARTITION BY firstName, lastName ORDER BY id ASC) as rank
            FROM df_members
        )
        SELECT DISTINCT
            '{season}' AS season,
            m.firstName AS owner_first_name,
            m.lastName AS owner_last_name,
            CONCAT(m.firstName, ' ', m.lastName) AS owner_full_name,
            t.abbrev AS abbreviation,
            CAST(t.id AS STRING) AS team_id,
            t.name AS team_name,
            om.original_owner_id AS owner_id
        FROM df_teams t
        CROSS JOIN UNNEST(t.owners) AS _unzipped(o_id)
        INNER JOIN df_members m ON m.id = o_id
        INNER JOIN owner_mapping om ON m.firstName = om.firstName 
            AND m.lastName = om.lastName
        WHERE om.rank = 1
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
            CAST(m.home_team AS STRING) AS home_team_id,
            m.home_team_score,
            CAST(m.home_team_starting_players AS JSON) AS home_team_starting_players,
            CAST(m.home_team_bench_players AS JSON) AS home_team_bench_players,
            m.home_team_efficiency,
            CAST(m.away_team AS STRING) AS away_team_id,
            m.away_team_score,
            CAST(m.away_team_starting_players AS JSON) AS away_team_starting_players,
            CAST(m.away_team_bench_players AS JSON) AS away_team_bench_players,
            m.away_team_efficiency,
            mh.owner_full_name AS home_team_full_name,
            mh.team_name AS home_team_team_name,
            mh.owner_id AS home_team_owner_id,
            ma.owner_full_name AS away_team_full_name,
            ma.team_name AS away_team_team_name,
            ma.owner_id AS away_team_owner_id,
            m.playoff_tier_type AS playoff_tier_type,
            m.winner AS winner,
            m.loser AS loser,
            m.matchup_week AS week,
            m.season AS season
        FROM df_matchup_results m
        INNER JOIN df_members mh 
            ON CAST(m.home_team AS STRING) = CAST(mh.team_id AS STRING) 
            AND CAST(m.season AS STRING) = CAST(mh.season AS STRING)
        INNER JOIN df_members ma 
            ON CAST(m.away_team AS STRING) = CAST(ma.team_id AS STRING) 
            AND CAST(m.season AS STRING) = CAST(ma.season AS STRING)
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
            player_scoring_info["season"] = season
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
        query = f"""
        WITH processed_teams AS (
            SELECT 
                team_id,
                owner_full_name,
                season,
                df_teams.owner_id AS owner_id,
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
                t.owner_id,
                CASE 
                    WHEN d.autoDraftTypeId IS NOT NULL 
                    THEN ROW_NUMBER() OVER(PARTITION BY p.position ORDER BY d.overallPickNumber) 
                END AS position_draft_rank
            FROM ranked_players p
            LEFT JOIN draft_results d
                ON p.player_id = d.playerId
            LEFT JOIN processed_teams t
                ON d.memberId = t.owner_id
            WHERE CAST(p.season AS STRING) = '{season}'
            AND CAST(t.season AS STRING) = '{season}'
        )
        SELECT 
            *,
            (CAST(position_draft_rank AS INTEGER) - CAST(position_rank AS INTEGER)) AS draft_position_rank_delta
        FROM joined_data
        WHERE auto_draft_type_id IS NOT NULL 
        AND overall_pick_number IS NOT NULL
        """

        return conn.execute(query).df()


def get_playoff_and_champion_teams(df_matchups: pd.DataFrame) -> pd.DataFrame:
    """
    Get the playoff teams (first round and clinched bye) and league champion over all seasons.

    Args:
        df_matchups: A dataframe of all matchups in the league history

    Returns:
        pd.DataFrame: Dataframe containing draft results and player finishes for season.
    """
    with duckdb.connect(":memory:") as conn:
        conn.register("df_matchups", df_matchups)
        query = """
        WITH base_matchups AS (
            SELECT 
                season,
                week,
                playoff_tier_type,
                home_team_id,
                away_team_id,
                home_team_score,
                away_team_score,
                CASE 
                    WHEN (CAST(season AS INTEGER) < 2021 AND CAST(week AS INTEGER) = 14) OR (CAST(season AS INTEGER) >= 2021 AND CAST(week AS INTEGER) = 15) THEN 'RD1'
                    WHEN (CAST(season AS INTEGER) < 2021 AND CAST(week AS INTEGER) = 15) OR (CAST(season AS INTEGER) >= 2021 AND CAST(week AS INTEGER) = 16) THEN 'RD2'
                    WHEN (CAST(season AS INTEGER) < 2021 AND CAST(week AS INTEGER) = 16) OR (CAST(season AS INTEGER) >= 2021 AND CAST(week AS INTEGER) = 17) THEN 'FINALS'
                    ELSE 'OTHER'
                END AS round_type
            FROM df_matchups
            WHERE playoff_tier_type = 'WINNERS_BRACKET'
        ),
        playoff_status AS (
            SELECT season, home_team_id AS team_id, 'MADE_PLAYOFFS' AS status
            FROM base_matchups WHERE round_type = 'RD1' AND home_team_id IS NOT NULL AND away_team_id IS NOT NULL
            UNION ALL
            SELECT season, away_team_id AS team_id, 'MADE_PLAYOFFS' AS status
            FROM base_matchups WHERE round_type = 'RD1' AND home_team_id IS NOT NULL AND away_team_id IS NOT NULL
            UNION ALL
            SELECT season, home_team_id AS team_id, 'CLINCHED_FIRST_ROUND_BYE' AS status
            FROM base_matchups WHERE round_type = 'RD2'
            UNION ALL
            SELECT 
                season, 
                CASE WHEN CAST(home_team_score AS DOUBLE) > CAST(away_team_score AS DOUBLE) THEN home_team_id ELSE away_team_id END AS team_id,
                'LEAGUE_CHAMPION' AS status
            FROM base_matchups WHERE round_type = 'FINALS'
        )
        SELECT * FROM playoff_status;
        """

        return conn.execute(query).df()


def calculate_regular_season_standings(df_matchups: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate regular season standings across all seasons.

    Args:
        df_matchups: A dataframe of all matchups in the league history

    Returns:
        pd.DataFrame: Dataframe containing regular season standings per season.
    """
    with duckdb.connect(":memory:") as conn:
        conn.register("df_matchups", df_matchups)
        query = """
        WITH weekly_stats AS (
            SELECT 
                season, week, playoff_tier_type,
                home_team_owner_id AS owner_id, 
                home_team_full_name AS team_name, 
                home_team_score AS points_for,
                CAST(away_team_score AS DOUBLE) AS points_against
            FROM df_matchups
            UNION ALL
            SELECT 
                season, week, playoff_tier_type,
                away_team_owner_id AS owner_id, 
                away_team_full_name AS team_name, 
                CAST(away_team_score AS DOUBLE) AS points_for,
                home_team_score AS points_against
            FROM df_matchups
        ),
        league_rankings AS (
            SELECT 
                *,
                RANK() OVER (PARTITION BY season, week ORDER BY points_for DESC) as weekly_rank,
                COUNT(*) OVER (PARTITION BY season, week) as total_teams_that_week
            FROM weekly_stats
            WHERE playoff_tier_type = 'NONE'
        ),
        processed_performance AS (
            SELECT 
                season,
                owner_id,
                team_name,
                points_for,
                points_against,
                CASE WHEN points_for > points_against THEN 1 ELSE 0 END AS win,
                CASE WHEN points_for < points_against THEN 1 ELSE 0 END AS loss,
                CASE WHEN points_for = points_against THEN 1 ELSE 0 END AS tie,
                (total_teams_that_week - weekly_rank) AS vs_league_wins,
                (weekly_rank - 1) AS vs_league_losses
            FROM league_rankings
        )
        SELECT 
            season,
            owner_id,
            team_name,
            COUNT(*) AS games_played,
            SUM(win) AS wins,
            SUM(loss) AS losses,
            SUM(tie) AS ties,
            ROUND(SUM(win) / COUNT(*)::DOUBLE, 3) AS win_pct,
            SUM(vs_league_wins) AS total_vs_league_wins,
            SUM(vs_league_losses) AS total_vs_league_losses,
            ROUND(SUM(vs_league_wins) / (SUM(vs_league_wins) + SUM(vs_league_losses))::DOUBLE, 3) AS all_play_win_pct,
            SUM(points_for) AS total_pf,
            SUM(points_against) AS total_pa,
            ROUND(AVG(points_for), 2) AS avg_pf
        FROM processed_performance
        GROUP BY season, owner_id, team_name
        ORDER BY season DESC, wins DESC, total_pf DESC;
        """

        return conn.execute(query).df()


def calculate_all_time_regular_season_standings(
    df_matchups: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate all-time regular season standings.

    Args:
        df_matchups: A dataframe of all matchups in the league history

    Returns:
        pd.DataFrame: Dataframe containing all-time regular season standings.
    """
    with duckdb.connect(":memory:") as conn:
        conn.register("df_matchups", df_matchups)
        query = """
        WITH team_performances AS (
            SELECT 
                season,
                home_team_owner_id AS owner_id,
                home_team_full_name AS team_name,
                home_team_score AS points_for,
                CAST(away_team_score AS DOUBLE) AS points_against,
                CASE WHEN home_team_score > CAST(away_team_score AS DOUBLE) THEN 1 ELSE 0 END AS win,
                CASE WHEN home_team_score < CAST(away_team_score AS DOUBLE) THEN 1 ELSE 0 END AS loss,
                CASE WHEN home_team_score = CAST(away_team_score AS DOUBLE) THEN 1 ELSE 0 END AS tie
            FROM df_matchups
            WHERE playoff_tier_type = 'NONE'
            UNION ALL
            SELECT 
                season,
                away_team_owner_id AS owner_id,
                away_team_full_name AS team_name,
                CAST(away_team_score AS DOUBLE) AS points_for,
                home_team_score AS points_against,
                CASE WHEN CAST(away_team_score AS DOUBLE) > home_team_score THEN 1 ELSE 0 END AS win,
                CASE WHEN CAST(away_team_score AS DOUBLE) < home_team_score THEN 1 ELSE 0 END AS loss,
                CASE WHEN CAST(away_team_score AS DOUBLE) = home_team_score THEN 1 ELSE 0 END AS tie
            FROM df_matchups
            WHERE playoff_tier_type = 'NONE'
        )
        SELECT 
            owner_id,
            COUNT(*) AS games_played,
            SUM(win) AS wins,
            SUM(loss) AS losses,
            SUM(tie) AS ties,
            ROUND(SUM(win) / COUNT(*)::DOUBLE, 3) AS win_pct,
            SUM(points_for) AS total_pf,
            SUM(points_against) AS total_pa,
            ROUND(AVG(points_for), 2) AS avg_pf,
            ROUND(AVG(points_against), 2) AS avg_pa
        FROM team_performances
        GROUP BY owner_id
        ORDER BY wins DESC, total_pf DESC;
        """

        return conn.execute(query).df()


def calculate_all_time_h2h_standings(df_matchups: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all-time H2H standings for a team vs. other teams in the league.

    Args:
        df_matchups: A dataframe of all matchups in the league history

    Returns:
        pd.DataFrame: Dataframe containing head-to-head standings.
    """
    with duckdb.connect(":memory:") as conn:
        conn.register("df_matchups", df_matchups)
        query = """
        WITH matchups_flat AS (
            SELECT 
                home_team_owner_id AS owner_id,
                away_team_owner_id AS opponent_id,
                home_team_full_name AS owner_name,
                away_team_full_name AS opponent_name,
                CASE 
                    WHEN CAST(home_team_score AS DOUBLE) > CAST(away_team_score AS DOUBLE) THEN 1 
                    ELSE 0 
                END AS win,
                CASE 
                    WHEN CAST(home_team_score AS DOUBLE) < CAST(away_team_score AS DOUBLE) THEN 1 
                    ELSE 0 
                END AS loss,
                CASE 
                    WHEN CAST(home_team_score AS DOUBLE) = CAST(away_team_score AS DOUBLE) THEN 1 
                    ELSE 0 
                END AS tie,
                CAST(home_team_score AS DOUBLE) AS pf,
                CAST(away_team_score AS DOUBLE) AS pa
            FROM df_matchups
            WHERE playoff_tier_type = 'NONE'
            UNION ALL
            SELECT 
                away_team_owner_id AS owner_id,
                home_team_owner_id AS opponent_id,
                away_team_full_name AS owner_name,
                home_team_full_name AS opponent_name,
                CASE 
                    WHEN CAST(away_team_score AS DOUBLE) > CAST(home_team_score AS DOUBLE) THEN 1 
                    ELSE 0 
                END AS win,
                CASE 
                    WHEN CAST(away_team_score AS DOUBLE) < CAST(home_team_score AS DOUBLE) THEN 1 
                    ELSE 0 
                END AS loss,
                CASE 
                    WHEN CAST(away_team_score AS DOUBLE) = CAST(home_team_score AS DOUBLE) THEN 1 
                    ELSE 0 
                END AS tie,
                CAST(away_team_score AS DOUBLE) AS pf,
                CAST(home_team_score AS DOUBLE) AS pa
            FROM df_matchups
            WHERE playoff_tier_type = 'NONE'
        )
        SELECT 
            owner_id,
            opponent_id,
            COUNT(*) AS matchups,
            SUM(win) AS wins,
            SUM(loss) AS losses,
            SUM(tie) AS ties,
            ROUND(SUM(win) / COUNT(*)::DOUBLE, 3) AS win_pct,
            SUM(pf) AS total_pf,
            SUM(pa) AS total_pa,
        FROM matchups_flat
        GROUP BY owner_id, opponent_id
        ORDER BY owner_id DESC
        """

        return conn.execute(query).df()


def calculate_playoff_standings(df_matchups: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate playoff standings across all seasons.

    Args:
        df_matchups: A dataframe of all matchups in the league history

    Returns:
        pd.DataFrame: Dataframe containing all-time playoff standings.
    """
    with duckdb.connect(":memory:") as conn:
        conn.register("df_matchups", df_matchups)
        query = """
        WITH team_performances AS (
            SELECT 
                season,
                home_team_owner_id AS owner_id,
                home_team_full_name AS team_name,
                home_team_score AS points_for,
                CAST(away_team_score AS DOUBLE) AS points_against,
                CASE WHEN home_team_score > CAST(away_team_score AS DOUBLE) THEN 1 ELSE 0 END AS win,
                CASE WHEN home_team_score < CAST(away_team_score AS DOUBLE) THEN 1 ELSE 0 END AS loss,
                CASE WHEN home_team_score = CAST(away_team_score AS DOUBLE) THEN 1 ELSE 0 END AS tie
            FROM df_matchups
            WHERE playoff_tier_type != 'NONE' AND playoff_tier_type == 'WINNERS_BRACKET'
            UNION ALL
            SELECT 
                season,
                away_team_owner_id AS owner_id,
                away_team_full_name AS team_name,
                CAST(away_team_score AS DOUBLE) AS points_for,
                home_team_score AS points_against,
                CASE WHEN CAST(away_team_score AS DOUBLE) > home_team_score THEN 1 ELSE 0 END AS win,
                CASE WHEN CAST(away_team_score AS DOUBLE) < home_team_score THEN 1 ELSE 0 END AS loss,
                CASE WHEN CAST(away_team_score AS DOUBLE) = home_team_score THEN 1 ELSE 0 END AS tie
            FROM df_matchups
            WHERE playoff_tier_type != 'NONE' AND playoff_tier_type == 'WINNERS_BRACKET'
        )
        SELECT 
            owner_id,
            COUNT(*) AS games_played,
            SUM(win) AS wins,
            SUM(loss) AS losses,
            SUM(tie) AS ties,
            ROUND(SUM(win) / COUNT(*)::DOUBLE, 3) AS win_pct,
            SUM(points_for) AS total_pf,
            SUM(points_against) AS total_pa,
            ROUND(AVG(points_for), 2) AS avg_pf,
            ROUND(AVG(points_against), 2) AS avg_pa
        FROM team_performances
        GROUP BY owner_id
        ORDER BY wins DESC, total_pf DESC;
        """

        return conn.execute(query).df()


def calculate_weekly_standings_snapshots(df_matchups: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates a team's record as a snapshot at every week.

    Args:
        df_matchups: A dataframe of all matchups in the league history

    Returns:
        pd.DataFrame: Dataframe containing weekly record snapshots.
    """
    with duckdb.connect(":memory:") as conn:
        conn.register("df_matchups", df_matchups)
        query = """
        WITH weekly_stats AS (
            SELECT 
                season, 
                week,
                home_team_owner_id AS owner_id, 
                home_team_full_name AS team_name, 
                home_team_score AS points_for,
                CAST(away_team_score AS DOUBLE) AS points_against
            FROM df_matchups
            WHERE playoff_tier_type = 'NONE'
            UNION ALL
            SELECT 
                season, 
                week,
                away_team_owner_id AS owner_id, 
                away_team_full_name AS team_name, 
                CAST(away_team_score AS DOUBLE) AS points_for,
                home_team_score AS points_against
            FROM df_matchups
            WHERE playoff_tier_type = 'NONE'
        ),
        weekly_outcomes AS (
            SELECT 
                *,
                CASE WHEN points_for > points_against THEN 1 ELSE 0 END AS win,
                CASE WHEN points_for < points_against THEN 1 ELSE 0 END AS loss,
                CASE WHEN points_for = points_against THEN 1 ELSE 0 END AS tie
            FROM weekly_stats
        )
        SELECT 
            season,
            week,
            owner_id,
            team_name,
            SUM(win) OVER (PARTITION BY season, owner_id ORDER BY week) AS wins,
            SUM(loss) OVER (PARTITION BY season, owner_id ORDER BY week) AS losses,
            SUM(tie) OVER (PARTITION BY season, owner_id ORDER BY week) AS ties,
            ROUND(SUM(points_for) OVER (PARTITION BY season, owner_id ORDER BY week), 2) AS cumulative_pf,
            ROUND(SUM(points_against) OVER (PARTITION BY season, owner_id ORDER BY week), 2) AS cumulative_pa
        FROM weekly_outcomes
        ORDER BY season DESC, week ASC, wins DESC, cumulative_pf DESC;
        """

        return conn.execute(query).df()


def calculate_top_and_bottom_team_scores(df_matchups: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates top and bottom 10 team scoring performances.

    Args:
        df_matchups: A dataframe of all matchups in the league history

    Returns:
        pd.DataFrame: Dataframe containing top and bottom 10 team scoring performances.
    """
    with duckdb.connect(":memory:") as conn:
        conn.register("df_matchups", df_matchups)
        query = """
        WITH all_scores AS (
            SELECT 
                season,
                week,
                home_team_full_name AS owner_name,
                home_team_owner_id AS owner_id,
                CAST(home_team_score AS DOUBLE) AS score,
                away_team_full_name AS opponent_name,
                away_team_owner_id AS opponent_owner_id
            FROM df_matchups
            UNION ALL
            SELECT 
                season,
                week,
                away_team_full_name AS owner_name,
                away_team_owner_id AS owner_id,
                CAST(away_team_score AS DOUBLE) AS score,
                home_team_full_name AS opponent_name,
                home_team_owner_id AS opponent_owner_id
            FROM df_matchups
        ),
        ranked_scores AS (
            SELECT 
                *,
                ROW_NUMBER() OVER(ORDER BY score DESC) as top_rank,
                ROW_NUMBER() OVER(ORDER BY score ASC) as bottom_rank
            FROM all_scores
        )
        SELECT
            'TOP 10' AS category,
            top_rank AS rank,
            season,
            week,
            owner_name,
            owner_id,
            score,
            opponent_name,
            opponent_owner_id,
        FROM ranked_scores WHERE top_rank <= 10
        UNION ALL
        SELECT
            'BOTTOM 10' AS category,
            bottom_rank AS rank,
            season,
            week,
            owner_name,
            owner_id,
            score,
            opponent_name,
            opponent_owner_id
        FROM ranked_scores WHERE bottom_rank <= 10
        ORDER BY category DESC, rank ASC;        
        """

        return conn.execute(query).df()


def calculate_top_player_performances(df_matchups: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates top 10 and player scoring performances by position.

    Args:
        df_matchups: A dataframe of all matchups in the league history

    Returns:
        pd.DataFrame: Dataframe containing top 10 player scoring performances by position.
    """
    with duckdb.connect(":memory:") as conn:
        conn.register("df_matchups", df_matchups)
        query = """
        WITH flattened_players AS (
            SELECT 
                season,
                week,
                home_team_full_name AS owner_name,
                home_team_owner_id AS owner_id,
                CAST(p->>'player_id' AS INTEGER) AS player_id,
                p->>'full_name' AS full_name,
                p->>'position' AS position,
                CAST(p->>'points_scored' AS DOUBLE) AS points
            FROM (
                SELECT 
                    season,
                    week,
                    home_team_full_name,
                    home_team_owner_id,
                    UNNEST(CAST(home_team_starting_players AS JSON[])) AS p 
                FROM df_matchups
            )
            UNION ALL
            SELECT 
                season,
                week,
                away_team_full_name AS owner_name,
                away_team_owner_id AS owner_id,
                CAST(p->>'player_id' AS INTEGER) AS player_id,
                p->>'full_name' AS full_name,
                p->>'position' AS position,
                CAST(p->>'points_scored' AS DOUBLE) AS points
            FROM (
                SELECT 
                    season,
                    week,
                    away_team_full_name,
                    away_team_owner_id,
                    UNNEST(CAST(away_team_starting_players AS JSON[])) AS p 
                FROM df_matchups
            )
        ),
        position_rankings AS (
            SELECT 
                *,
                DENSE_RANK() OVER(PARTITION BY position ORDER BY points DESC) as pos_rank
            FROM flattened_players
            WHERE position IN ('QB', 'RB', 'WR', 'TE', 'D/ST', 'K')
        )
        SELECT 
            pos_rank AS rank,
            position,
            full_name,
            points,
            owner_name,
            owner_id,
            season,
            week
        FROM position_rankings
        WHERE pos_rank <= 10
        ORDER BY 
            CASE position 
                WHEN 'QB' THEN 1 WHEN 'RB' THEN 2 WHEN 'WR' THEN 3 
                WHEN 'TE' THEN 4 WHEN 'D/ST' THEN 5 WHEN 'K' THEN 6 
            END, 
            pos_rank ASC;
        """

        return conn.execute(query).df()
