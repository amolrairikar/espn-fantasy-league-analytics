import unittest
from unittest.mock import patch

import pandas as pd
import pytest

from lambdas.step_function_lambdas.league_weekly_standings.main import (
    outcome_row,
    compute_standings,
    compile_weekly_standings_snapshots,
    lambda_handler,
)


class TestOutcomeRow(unittest.TestCase):
    """Class for testing outcome_row function."""

    def test_outcome_row_winner(self):
        """Tests outcome_row when the team owner won."""
        # Set up test data
        input_data = {
            "winner": "1",
            "team_owner_id": "1",
        }
        input_row = pd.Series(data=input_data)
        expected_outcome = pd.Series({"win": 1, "loss": 0, "tie": 0})

        # Act
        outcome = outcome_row(r=input_row)

        # Assert
        pd.testing.assert_series_equal(outcome, expected_outcome)

    def test_outcome_row_loser(self):
        """Tests outcome_row when the team owner lost."""
        # Set up test data
        input_data = {
            "winner": "2",
            "loser": "1",
            "team_owner_id": "1",
        }
        input_row = pd.Series(data=input_data)
        expected_outcome = pd.Series({"win": 0, "loss": 1, "tie": 0})

        # Act
        outcome = outcome_row(r=input_row)

        # Assert
        pd.testing.assert_series_equal(outcome, expected_outcome)

    def test_outcome_row_tie(self):
        """Tests outcome_row when a tie occurred."""
        # Set up test data
        input_data = {
            "winner": "TIE",
        }
        input_row = pd.Series(data=input_data)
        expected_outcome = pd.Series({"win": 0, "loss": 0, "tie": 1})

        # Act
        outcome = outcome_row(r=input_row)

        # Assert
        pd.testing.assert_series_equal(outcome, expected_outcome)

    def test_outcome_row_no_outcome(self):
        """Tests outcome_row when no matchup occurred."""
        # Set up test data
        input_data = {
            "winner": "NONE",
            "loser": "NONE",
            "team_owner_id": "1",
        }
        input_row = pd.Series(data=input_data)
        expected_outcome = pd.Series({"win": 0, "loss": 0, "tie": 0})

        # Act
        outcome = outcome_row(r=input_row)

        # Assert
        pd.testing.assert_series_equal(outcome, expected_outcome)


class TestComputeStandings(unittest.TestCase):
    """Class for testing compute_standings_function."""

    def test_compute_standings_success(self):
        """Tests successful execution of compute_standings function."""
        # Set up test data
        # Minimal long-form dataframe: one team, one game, one win
        input_df = pd.DataFrame(
            [
                {
                    "team_owner_id": "1",
                    "points_for": 100,
                    "points_against": 90,
                    "win": 1,
                    "loss": 0,
                    "tie": 0,
                }
            ]
        )
        member_map = pd.DataFrame(
            [
                {
                    "owner_id": "1",
                    "owner_full_name": "First Last",
                }
            ]
        )
        expected = pd.DataFrame(
            [
                {
                    "team_owner_id": "1",
                    "wins": 1,
                    "losses": 0,
                    "ties": 0,
                    "games": 1,
                    "points_for_total": 100.0,
                    "points_against_total": 90.0,
                    "owner_id": "1",
                    "owner_full_name": "First Last",
                    "points_for_per_game": 100.0,
                    "points_against_per_game": 90.0,
                    "win_pct": 1.0,
                }
            ]
        )

        # Act
        result = compute_standings(
            df=input_df, group_cols=["team_owner_id"], member_map=member_map
        )

        # Assert
        pd.testing.assert_frame_equal(
            result.reset_index(drop=True), expected, check_like=True
        )


class TestCompileWeeklyStandingsSnapshots(unittest.TestCase):
    """Class for testing compile_weekly_standings_snapshots function."""

    def test_compile_weekly_standings_snapshots(self):
        """Tests successful execution of compile_weekly_standings_snapshots function."""
        # Set up test data

        # Minimal matchup data: one matchup between two owners in week 1
        matchup_data = [
            {
                "season": "2025",
                "week": "1",
                "team_a_owner_id": "owner1",
                "team_b_owner_id": "owner2",
                "team_a_score": 100,
                "team_b_score": 90,
                "winner": "owner1",
                "loser": "owner2",
                "playoff_tier_type": "NONE",
            }
        ]

        # Minimal members data mapping owners to names
        members_data = [
            {
                "PK": "TEAM#team1#2025",
                "team_id": "team1",
                "owner_id": "owner1",
                "owner_full_name": "Owner One",
            },
            {
                "PK": "TEAM#team2#2025",
                "team_id": "team2",
                "owner_id": "owner2",
                "owner_full_name": "Owner Two",
            },
        ]

        # Expect two records (one per owner) with cumulative win/loss
        expected = (
            pd.DataFrame(
                [
                    {
                        "season": "2025",
                        "team_owner_id": "owner1",
                        "week": 1,
                        "wins": 1,
                        "losses": 0,
                        "ties": 0,
                        "owner_full_name": "Owner One",
                    },
                    {
                        "season": "2025",
                        "team_owner_id": "owner2",
                        "week": 1,
                        "wins": 0,
                        "losses": 1,
                        "ties": 0,
                        "owner_full_name": "Owner Two",
                    },
                ]
            )
            .sort_values(by=["team_owner_id"])
            .reset_index(drop=True)
        )

        # Act
        result = compile_weekly_standings_snapshots(
            matchup_data=matchup_data, members_data=members_data
        )

        # Assert
        res_df = (
            pd.DataFrame(result)
            .sort_values(by=["team_owner_id"])
            .reset_index(drop=True)
        )
        pd.testing.assert_frame_equal(
            res_df.reset_index(drop=True),
            expected.reset_index(drop=True),
            check_dtype=False,
        )


class TestLambdaHandler(unittest.TestCase):
    """Test lambda_handler function."""

    @patch(
        "lambdas.step_function_lambdas.league_weekly_standings.main.fetch_league_data"
    )
    @patch(
        "lambdas.step_function_lambdas.league_weekly_standings.main.compile_weekly_standings_snapshots"
    )
    @patch(
        "lambdas.step_function_lambdas.league_weekly_standings.main.batch_write_to_dynamodb"
    )
    def test_lambda_handler_success(
        self,
        mock_batch_write_to_dynamodb,
        mock_compile_weekly_standings_snapshots,
        mock_fetch_data,
    ):
        """Tests happy path for lambda_handler execution."""
        # NOTE: This test is just for line coverage, the live dependency test
        # is a more accurate test for a handler function.

        # Mock dependencies
        mock_fetch_data.return_value = ["dummy_value"]
        mock_compile_weekly_standings_snapshots.return_value = [
            {
                "team_owner_id": "2",
                "owner_full_name": "First Last",
                "season": "2023",
                "week": "3",
                "wins": 5,
                "losses": 4,
                "ties": 0,
            },
        ]
        mock_batch_write_to_dynamodb.return_value = None

        # Act
        lambda_handler(
            event=[
                [
                    {
                        "leagueId": "12345",
                        "platform": "ESPN",
                        "privacy": "private",
                        "swidCookie": None,
                        "espnS2Cookie": None,
                        "season": "2023",
                    },
                ],
            ],
            context={},
        )

        # Assert
        mock_batch_write_to_dynamodb.assert_called_once_with(
            batched_objects=[
                {
                    "PutRequest": {
                        "Item": {
                            "PK": {
                                "S": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2023#WEEK#3"
                            },
                            "SK": {"S": "STANDINGS#WEEKLY#2"},
                            "GSI5PK": {"S": "LEAGUE#12345"},
                            "GSI5SK": {"S": "FOR_DELETION_USE_ONLY"},
                            "season": {"S": "2023"},
                            "week": {"N": "3"},
                            "owner_id": {"S": "2"},
                            "owner_full_name": {"S": "First Last"},
                            "wins": {"N": "5"},
                            "losses": {"N": "4"},
                            "ties": {"N": "0"},
                        },
                    },
                },
            ],
            table_name="fantasy-recap-app-db-dev",
        )

    @patch(
        "lambdas.step_function_lambdas.league_weekly_standings.main.fetch_league_data"
    )
    def test_lambda_handler_missing_data(self, mock_fetch_data):
        """Tests lambda_handler error handling when some input data is missing."""
        # Mock dependencies
        mock_fetch_data.return_value = []

        # Act
        with pytest.raises(ValueError):
            lambda_handler(
                event=[
                    [
                        {
                            "leagueId": "12345",
                            "platform": "ESPN",
                            "privacy": "private",
                            "swidCookie": None,
                            "espnS2Cookie": None,
                            "season": "2023",
                        },
                    ],
                ],
                context={},
            )
