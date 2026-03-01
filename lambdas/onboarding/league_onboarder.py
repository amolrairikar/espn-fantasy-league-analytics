"""
Module containing class definition for all onboarding logic.
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from dotenv import load_dotenv

from onboarding.api_requests import (
    get_league_members_and_teams,
    get_league_scores,
    get_league_lineup_settings,
    get_draft_results,
    get_player_season_totals,
)
from onboarding.data_processing import (
    join_league_members_to_teams,
    process_league_scores,
    process_player_scoring_totals,
    enrich_draft_data,
    get_playoff_and_champion_teams,
    calculate_regular_season_standings,
    calculate_all_time_regular_season_standings,
    calculate_all_time_h2h_standings,
    calculate_playoff_standings,
    calculate_weekly_standings_snapshots,
    calculate_top_and_bottom_team_scores,
    calculate_top_player_performances,
)
from onboarding.write_data import write_to_duckdb_table, write_duckdb_file_to_s3
from utils.logging_config import logger

load_dotenv()


class LeagueOnboarder:
    def __init__(self, league_id, platform, swid_cookie, espn_s2_cookie, seasons):
        self.league_id = league_id
        self.platform = platform
        self.swid_cookie = swid_cookie
        self.espn_s2_cookie = espn_s2_cookie
        self.seasons = seasons

    def run_onboarding_process(self) -> dict:
        """
        Main orchestration method that executes the onboarding steps in order.

        Returns:
            dict: A success status with the league ID and number of seasons processed.
        """
        logger.info(f"Starting onboarding for league {self.league_id}")

        df_members_and_teams = self._fetch_league_members_and_teams()
        logger.info("Successfully fetched league members and teams.")

        df_league_matchups, df_league_draft_results = (
            self._fetch_league_matchups_and_draft_results(
                df_members=df_members_and_teams
            )
        )
        logger.info("Successfully fetched matchup and draft results.")

        (
            df_playoff_and_champion_teams,
            df_regular_season_standings,
            df_all_time_standings,
            df_h2h_standings,
            df_playoff_standings,
            df_weekly_standings,
            df_top_and_bottom_scores,
            df_top_player_performances,
        ) = self._fetch_aggregate_calculations(df_matchups=df_league_matchups)
        logger.info("Successfully calculated aggregate metrics.")

        # Write all data to DuckDB
        output_data = [
            ("league_members", df_members_and_teams),
            ("league_matchups", df_league_matchups),
            ("league_draft_results", df_league_draft_results),
            ("league_postseason_teams", df_playoff_and_champion_teams),
            ("league_regular_season_standings", df_regular_season_standings),
            ("league_all_time_standings", df_all_time_standings),
            ("league_h2h_standings", df_h2h_standings),
            ("league_playoff_standings", df_playoff_standings),
            ("league_weekly_standings", df_weekly_standings),
            ("league_top_and_bottom_scores", df_top_and_bottom_scores),
            ("league_top_player_performances", df_top_player_performances),
        ]
        bucket_name_add_on = "-dev" if os.environ["ENVIRONMENT"] == "DEV" else ""
        bucket_name = f"{os.environ['ACCOUNT_NUMBER']}-fantasy-recap-app-duckdb-storage{bucket_name_add_on}"
        write_to_duckdb_table(data_to_write=output_data)
        write_duckdb_file_to_s3(
            bucket_name=bucket_name, bucket_key=f"{self.league_id}.duckdb"
        )

        return {
            "status": "success",
            "league_id": self.league_id,
            "seasons_processed": len(self.seasons),
        }

    def _fetch_league_members_and_teams(self) -> pd.DataFrame:
        """
        Orchestrates the multi-threaded fetching and joining of league member
        and team data across multiple seasons.

        Returns:
            pd.DataFrame: A dataframe containing league members and teams per season.
        """
        result_dataframes = []

        with ThreadPoolExecutor() as executor:
            # Mapping the helper function to seasons
            future_to_season = {
                executor.submit(self._get_teams_and_members_for_season, season): season
                for season in self.seasons
            }

            for future in as_completed(future_to_season):
                season = future_to_season[future]
                try:
                    season_joined_data = future.result()
                    result_dataframes.append(season_joined_data)
                except Exception as e:
                    logger.error(f"Season {season} generated an exception: {e}")
                    raise e

        df_members_and_teams = pd.concat(result_dataframes, ignore_index=True)

        return df_members_and_teams

    def _fetch_league_matchups_and_draft_results(
        self, df_members: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Orchestrates the multi-threaded fetching of league matchups and draft
        results over multiple seasons.

        Args:
            df_members: A dataframe containing league members/team information

        Returns:
            tuple: A tuple of dataframes, one for league matchups and one for league
                draft results.
        """
        matchup_futures = []
        draft_futures = []

        with ThreadPoolExecutor() as executor:
            for season in self.seasons:
                matchup_futures.append(
                    executor.submit(self._get_matchups_for_season, season, df_members)
                )
            for season in self.seasons:
                draft_futures.append(
                    executor.submit(
                        self._get_draft_results_for_season, season, df_members
                    )
                )

            matchup_dfs = [f.result() for f in as_completed(matchup_futures)]
            draft_dfs = [f.result() for f in as_completed(draft_futures)]
            df_league_matchups = pd.concat(matchup_dfs, ignore_index=True)
            df_league_draft_results = pd.concat(draft_dfs, ignore_index=True)

        return df_league_matchups, df_league_draft_results

    def _fetch_aggregate_calculations(self, df_matchups: pd.DataFrame) -> tuple:
        """
        Computes aggregations such as standings, playoff teams/champion, etc.

        Args:
            df_matchups: Dataframe containing all league matchup history.

        Returns:
            tuple: Tuple of dataframes containing aggregated standings data.
        """
        with ThreadPoolExecutor() as executor:
            playoff_future = executor.submit(
                get_playoff_and_champion_teams, df_matchups
            )
            regular_season_standings_future = executor.submit(
                calculate_regular_season_standings, df_matchups
            )
            all_time_standings_future = executor.submit(
                calculate_all_time_regular_season_standings, df_matchups
            )
            h2h_standings_future = executor.submit(
                calculate_all_time_h2h_standings, df_matchups
            )
            playoff_standings_future = executor.submit(
                calculate_playoff_standings, df_matchups
            )
            weekly_standings_future = executor.submit(
                calculate_weekly_standings_snapshots, df_matchups
            )
            top_and_bottom_scores_future = executor.submit(
                calculate_top_and_bottom_team_scores, df_matchups
            )
            top_player_performances_future = executor.submit(
                calculate_top_player_performances, df_matchups
            )
            try:
                df_playoff_and_champion_teams = playoff_future.result()
                df_regular_season_standings = regular_season_standings_future.result()
                df_all_time_standings = all_time_standings_future.result()
                df_h2h_standings = h2h_standings_future.result()
                df_playoff_standings = playoff_standings_future.result()
                df_weekly_standings = weekly_standings_future.result()
                df_top_and_bottom_scores = top_and_bottom_scores_future.result()
                df_top_player_performances = top_player_performances_future.result()
                return (
                    df_playoff_and_champion_teams,
                    df_regular_season_standings,
                    df_all_time_standings,
                    df_h2h_standings,
                    df_playoff_standings,
                    df_weekly_standings,
                    df_top_and_bottom_scores,
                    df_top_player_performances,
                )
            except Exception as e:
                logger.error("Error occurred while computing aggregations: %s", e)
                raise

    def _get_teams_and_members_for_season(self, season: str) -> pd.DataFrame:
        """
        Internal helper to get teams and league members for a specific season.

        Args:
            season: The season to get teams and league members for.

        Returns:
            pd.DataFrame: A dataframe containing league members and teams for that season.
        """
        members, teams = get_league_members_and_teams(
            league_id=self.league_id,
            platform=self.platform,
            season=season,
            swid_cookie=self.swid_cookie,
            espn_s2_cookie=self.espn_s2_cookie,
        )

        if not members or not teams:
            logger.error(f"No data found for season {season}")
            raise ValueError(f"Missing data for {season} season.")

        return join_league_members_to_teams(members=members, teams=teams, season=season)

    def _get_matchups_for_season(
        self, season: str, df_members: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Internal helper to get matchups for a specific season.

        Args:
            season: The season to get matchups for.

        Returns:
            pd.DataFrame: A dataframe containing all matchups for the season.
        """
        matchups = get_league_scores(
            league_id=self.league_id,
            platform=self.platform,
            season=season,
            swid_cookie=self.swid_cookie,
            espn_s2_cookie=self.espn_s2_cookie,
        )
        lineup_settings = get_league_lineup_settings(
            league_id=self.league_id,
            platform=self.platform,
            season=season,
            swid_cookie=self.swid_cookie,
            espn_s2_cookie=self.espn_s2_cookie,
        )

        if not matchups or not lineup_settings:
            logger.error(
                f"No matchup and/or lineup settings data found for season {season}"
            )
            raise ValueError(
                f"Missing matchup and/or lineup settings data for {season} season."
            )

        return process_league_scores(
            matchups=matchups,
            df_members=df_members,
            lineup_limits_data=lineup_settings,
            season=season,
        )

    def _get_draft_results_for_season(
        self, season: str, df_members: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Internal helper to get draft results for a specific season.

        Args:
            season: The season to get matchups for.

        Returns:
            pd.DataFrame: A dataframe containing all matchups for the season.
        """
        draft_results = get_draft_results(
            league_id=self.league_id,
            platform=self.platform,
            season=season,
            swid_cookie=self.swid_cookie,
            espn_s2_cookie=self.espn_s2_cookie,
        )
        player_totals = get_player_season_totals(
            league_id=self.league_id,
            platform=self.platform,
            season=season,
            swid_cookie=self.swid_cookie,
            espn_s2_cookie=self.espn_s2_cookie,
        )
        if not draft_results or not player_totals:
            logger.error(
                f"No draft results and/or player scoring totals data found for season {season}"
            )
            raise ValueError(
                f"Missing draft results and/or player scoring totals data for {season} season."
            )

        processed_player_totals = process_player_scoring_totals(
            player_totals=player_totals,
            season=season,
        )

        return enrich_draft_data(
            draft_results=draft_results,
            player_totals=processed_player_totals,
            df_teams=df_members,
            season=season,
        )
