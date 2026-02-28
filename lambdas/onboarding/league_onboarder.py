"""
Module containing class definition for all onboarding logic.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from onboarding.api_requests import get_league_members_and_teams
from onboarding.data_processing import join_league_members_to_teams
from onboarding.write_data import write_to_duckdb_table, write_duckdb_file_to_s3
from utils.logging_config import logger


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
        print(df_members_and_teams.head(5))
        logger.info("Successfully fetched league members and teams.")

        # Step 2: [Future Step - e.g., Fetch Schedules]
        # self.fetch_league_schedules(league_metadata)

        # Write all data to DuckDB
        output_data = [
            ("league_members", df_members_and_teams),
        ]
        write_to_duckdb_table(data_to_write=output_data)
        write_duckdb_file_to_s3(bucket_name="", bucket_key="")

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

    def _get_teams_and_members_for_season(self, season: str) -> pd.DataFrame:
        """
        Internal helper to handle the fetch and join logic for a specific season.

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
