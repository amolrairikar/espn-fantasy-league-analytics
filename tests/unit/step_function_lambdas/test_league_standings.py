import unittest
from unittest.mock import patch

import pandas as pd
import pytest

from lambdas.step_function_lambdas.league_standings.main import (
    outcome_row,
    compute_standings,
    calculate_weekly_vs_league_standings,
    compile_aggregate_standings_data,
    format_dynamodb_item,
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


class TestComputeWeeklyVsLeagueStandings(unittest.TestCase):
    """Class for testing calculate_weekly_vs_league_standings function."""

    def test_calculate_weekly_vs_league_standings_success(self):
        """Tests successful execution of calculate_weekly_vs_league_standings function."""
        # Set up test data
        input_df = pd.DataFrame(
            [
                {"team_owner_id": "1", "points_for": 150},
                {"team_owner_id": "2", "points_for": 120},
                {"team_owner_id": "3", "points_for": 100},
            ]
        )

        # Act
        result = calculate_weekly_vs_league_standings(group=input_df)

        # Assert
        assert result["ap_wins"].tolist() == [2, 1, 0]
        assert result["ap_losses"].tolist() == [0, 1, 2]


class TestCompileAggregateStandingsData(unittest.TestCase):
    """Class for testing compile_aggregate_standings_data function."""

    def test_compile_aggregate_standings_data_success(self):
        """Tests successful execution of compile_aggregate_standings_data function."""
        # Minimal members: two owners in one season
        members_data = [
            {
                "PK": "LEAGUE#L#PLATFORM#P#SEASON#2025",
                "team_id": "t1",
                "owner_id": "1",
                "owner_full_name": "Alice",
            },
            {
                "PK": "LEAGUE#L#PLATFORM#P#SEASON#2025",
                "team_id": "t2",
                "owner_id": "2",
                "owner_full_name": "Bob",
            },
        ]

        # One regular matchup (team 1 beats team 2) and one playoff matchup
        matchup_data = [
            {
                "playoff_tier_type": "NONE",
                "season": "2025",
                "week": 1,
                "team_a_owner_id": "1",
                "team_b_owner_id": "2",
                "team_a_score": 100,
                "team_b_score": 90,
                "winner": "1",
                "loser": "2",
            },
            {
                "playoff_tier_type": "WINNERS_BRACKET",
                "season": "2025",
                "week": 2,
                "team_a_owner_id": "1",
                "team_b_owner_id": "2",
                "team_a_score": 110,
                "team_b_score": 105,
                "winner": "1",
                "loser": "2",
            },
        ]

        playoff_teams_data = [
            {"season": "2025", "team_id": "t1", "playoff_status": "MADE_PLAYOFFS"}
        ]

        championship_team_data = [
            {"season": "2025", "team_id": "t1", "championship_status": "CHAMPION"}
        ]

        # Act
        (
            unique_members,
            season_standings,
            alltime_standings,
            alltime_standings_playoffs,
            h2h_standings,
        ) = compile_aggregate_standings_data(
            matchup_data=matchup_data,
            members_data=members_data,
            playoff_teams_data=playoff_teams_data,
            championship_team_data=championship_team_data,
        )

        # Assert

        # Assert unique members contains both owners
        assert any(
            m["owner_id"] == "1" and m["owner_full_name"] == "Alice"
            for m in unique_members
        )
        assert any(
            m["owner_id"] == "2" and m["owner_full_name"] == "Bob"
            for m in unique_members
        )

        # Assert season standings contains the expected record and playoff/championship flags
        season_item = next(
            (
                s
                for s in season_standings
                if s["season"] == "2025" and s["team_owner_id"] == "1"
            ),
            None,
        )
        assert season_item is not None
        assert season_item["wins"] == 1
        assert season_item["losses"] == 0
        assert season_item["all_play_wins"] >= 0
        assert season_item["playoff_status"] == "MADE_PLAYOFFS"
        assert season_item["championship_status"] == "CHAMPION"

        # Assert all-time standings includes owner 1 with at least one game played and a win
        alltime_item = next(
            (a for a in alltime_standings if a["team_owner_id"] == "1"), None
        )
        assert alltime_item is not None
        assert alltime_item["wins"] >= 1

        # Playoff all-time standings should include a playoff win for owner 1
        playoff_item = next(
            (p for p in alltime_standings_playoffs if p["team_owner_id"] == "1"), None
        )
        assert playoff_item is not None
        assert playoff_item["wins"] >= 1

        # H2H standings should have an entry for Alice vs Bob
        h2h_item = next(
            (
                h
                for h in h2h_standings
                if h["team_owner_id"] == "1" and h["opponent_owner_id"] == "2"
            ),
            None,
        )
        assert h2h_item is not None
        assert h2h_item["wins"] >= 1


class TestFormatDynamoDBItem(unittest.TestCase):
    """Class for testing format_dynamodb_item function."""

    def test_format_dynamodb_item_owners(self):
        """Tests format_dynamodb_item function for owners standings type."""
        # Set up test data
        item = {
            "owner_id": "1",
            "owner_full_name": "First Last",
        }
        expected_schema = {
            "PK": {"S": "LEAGUE#12345#PLATFORM#ESPN"},
            "SK": {"S": f"OWNERS#{item['owner_id']}"},
            "owner_full_name": {"S": item["owner_full_name"]},
            "owner_id": {"S": item["owner_id"]},
        }

        # Act
        schema = format_dynamodb_item(
            standings_type="owners",
            item=item,
            league_id="12345",
            platform="ESPN",
        )

        # Assert
        self.assertEqual(schema, expected_schema)

    def test_format_dynamodb_item_season_standings(self):
        """Tests format_dynamodb_item function for season standings type."""
        # Set up test data
        item = {
            "season": "2025",
            "team_owner_id": "1",
            "owner_full_name": "First Last",
            "wins": 10,
            "losses": 2,
            "ties": 1,
            "win_pct": 0.833,
            "all_play_wins": 8,
            "all_play_losses": 5,
            "points_for_total": 1500.0,
            "points_against_total": 1200.0,
            "point_differential": 300.0,
            "playoff_status": "MADE_PLAYOFFS",
            "championship_status": "",
        }
        expected_schema = {
            "PK": {"S": f"LEAGUE#12345#PLATFORM#ESPN#SEASON#{item['season']}"},
            "SK": {"S": f"STANDINGS#SEASON#{item['team_owner_id']}"},
            "GSI2PK": {
                "S": f"LEAGUE#12345#PLATFORM#ESPN#STANDINGS#SEASON#TEAM#{item['team_owner_id']}"
            },
            "GSI2SK": {"S": f"SEASON#{item['season']}"},
            "season": {"S": item["season"]},
            "owner_full_name": {"S": item["owner_full_name"]},
            "wins": {"N": str(item["wins"])},
            "losses": {"N": str(item["losses"])},
            "ties": {"N": str(item["ties"])},
            "win_pct": {"N": str(item["win_pct"])},
            "all_play_wins": {"N": str(item["all_play_wins"])},
            "all_play_losses": {"N": str(item["all_play_losses"])},
            "points_for": {"N": str(item["points_for_total"])},
            "points_against": {"N": str(item["points_against_total"])},
            "points_differential": {"N": str(item["point_differential"])},
            "playoff_status": {"S": item["playoff_status"]},
            "championship_status": {"S": item["championship_status"]},
        }

        # Act
        schema = format_dynamodb_item(
            standings_type="season",
            item=item,
            league_id="12345",
            platform="ESPN",
        )

        # Assert
        self.assertEqual(schema, expected_schema)

    def test_format_dynamodb_item_all_time(self):
        """Tests format_dynamodb_item function for all_time standings type."""
        item = {
            "team_owner_id": "1",
            "owner_full_name": "First Last",
            "games_played": 12,
            "wins": 8,
            "losses": 4,
            "ties": 0,
            "win_pct": 0.667,
            "points_for_per_game": 125.0,
            "points_against_per_game": 110.0,
        }
        expected_schema = {
            "PK": {"S": "LEAGUE#12345#PLATFORM#ESPN"},
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

        # Act
        schema = format_dynamodb_item(
            standings_type="all_time",
            item=item,
            league_id="12345",
            platform="ESPN",
        )

        # Assert
        self.assertEqual(schema, expected_schema)

    def test_format_dynamodb_item_all_time_playoffs(self):
        """Tests format_dynamodb_item function for all_time_playoffs standings type."""
        # Set up test data
        item = {
            "team_owner_id": "1",
            "owner_full_name": "First Last",
            "games_played": 2,
            "wins": 1,
            "losses": 1,
            "ties": 0,
            "win_pct": 0.5,
            "points_for_per_game": 110.0,
            "points_against_per_game": 105.0,
        }
        expected_schema = {
            "PK": {"S": "LEAGUE#12345#PLATFORM#ESPN"},
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

        # Act
        schema = format_dynamodb_item(
            standings_type="all_time_playoffs",
            item=item,
            league_id="12345",
            platform="ESPN",
        )

        # Assert
        self.assertEqual(schema, expected_schema)

    def test_format_dynamodb_item_h2h(self):
        """Tests format_dynamodb_item function for h2h standings type."""
        # Set up test data
        item = {
            "team_owner_id": "1",
            "opponent_owner_id": "2",
            "owner_full_name": "First Last",
            "opponent_full_name": "Second Person",
            "games_played": 3,
            "wins": 2,
            "losses": 1,
            "ties": 0,
            "win_pct": 0.667,
            "points_for_per_game": 120.0,
            "points_against_per_game": 115.0,
        }
        expected_schema = {
            "PK": {"S": "LEAGUE#12345#PLATFORM#ESPN"},
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

        # Act
        schema = format_dynamodb_item(
            standings_type="h2h",
            item=item,
            league_id="12345",
            platform="ESPN",
        )

        # Assert
        self.assertEqual(schema, expected_schema)

    def test_format_dynamodb_item_unsupported_standings(self):
        """Tests format_dynamodb_item function for unsupported standings type."""
        with pytest.raises(ValueError):
            format_dynamodb_item(
                standings_type="invalid",
                item={},
                league_id="12345",
                platform="ESPN",
            )


class TestLambdaHandler(unittest.TestCase):
    """Class for testing lambda_handler function."""

    @patch("lambdas.step_function_lambdas.league_standings.main.fetch_league_data")
    @patch(
        "lambdas.step_function_lambdas.league_standings.main.compile_aggregate_standings_data"
    )
    @patch("lambdas.step_function_lambdas.league_standings.main.format_dynamodb_item")
    @patch(
        "lambdas.step_function_lambdas.league_standings.main.batch_write_to_dynamodb"
    )
    def test_lambda_handler_success(
        self,
        mock_batch_write_to_dynamodb,
        mock_format_dynamodb_item,
        mock_compile_aggregate_standings_data,
        mock_fetch_data,
    ):
        """Tests happy path for lambda_handler."""
        # NOTE: This test is just for line coverage, the live dependency test
        # is a more accurate test for a handler function.

        # Mock dependencies
        mock_fetch_data.return_value = ["dummy_value"]
        mock_compile_aggregate_standings_data.return_value = (["test"], [], [], [], [])
        mock_format_dynamodb_item.return_value = {}
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
        # NOTE: No specific assertions for this one as the live dependency test will test the handler
        assert True

    @patch("lambdas.step_function_lambdas.league_standings.main.fetch_league_data")
    def test_lambda_handler_missing_input_data(self, mock_fetch_data):
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
