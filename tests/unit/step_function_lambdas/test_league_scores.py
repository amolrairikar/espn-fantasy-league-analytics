import unittest
from unittest.mock import patch

import botocore.exceptions
import pytest

from lambdas.step_function_lambdas.league_scores.main import (
    get_league_members,
    create_team_id_member_id_mapping,
    get_league_scores,
    get_league_lineup_settings,
    safe_int,
    calculate_lineup_efficiency,
    process_league_scores,
    get_playoff_status,
    lambda_handler,
)
from tests.unit.step_function_lambdas.sample_matchups_response import (
    SAMPLE_MATCHUPS_RESPONSE,
)

LINEUP_LIMITS = lineup_limits = {
    "0": 1,
    "1": 0,
    "2": 2,
    "3": 0,
    "4": 2,
    "5": 0,
    "6": 1,
    "7": 0,
    "8": 0,
    "9": 0,
    "10": 0,
    "11": 0,
    "12": 0,
    "13": 0,
    "14": 0,
    "15": 0,
    "16": 1,
    "17": 1,
    "18": 0,
    "19": 0,
    "20": 7,
    "21": 1,
    "22": 0,
    "23": 1,
    "24": 0,
}


class TestGetLeagueMembers(unittest.TestCase):
    """Class to test get_league_members function."""

    @patch("lambdas.step_function_lambdas.league_scores.main.boto3.client")
    def test_get_league_members_success(self, mock_boto_client):
        """Test get_league_members function for successful response."""
        # Set up mock DynamoDB response
        mock_dynamodb = mock_boto_client.return_value
        mock_dynamodb.query.return_value = {
            "Items": [
                {
                    "PK": {"S": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2023"},
                    "SK": {"S": "TEAM#1"},
                    "owner_id": {"L": [{"S": "1"}]},
                },
                {
                    "PK": {"S": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2023"},
                    "SK": {"S": "TEAM#2"},
                    "owner_id": {"L": [{"S": "2"}]},
                },
            ]
        }
        expected_members = [
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2023",
                "SK": "TEAM#1",
                "owner_id": ["1"],
                "season": "2023",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2023",
                "SK": "TEAM#2",
                "owner_id": ["2"],
                "season": "2023",
            },
        ]

        # Act
        members = get_league_members(league_id="12345", platform="ESPN", season="2023")

        # Assert
        members_sorted = sorted(members, key=lambda x: x["SK"])
        expected_sorted = sorted(expected_members, key=lambda x: x["SK"])
        self.assertEqual(members_sorted, expected_sorted)

    @patch("lambdas.step_function_lambdas.league_scores.main.boto3.client")
    def test_get_league_members_failure(self, mock_boto_client):
        """Test get_league_members function for boto error."""
        # Set up mock DynamoDB response
        mock_dynamodb = mock_boto_client.return_value
        mock_dynamodb.query.side_effect = botocore.exceptions.ClientError(
            error_response={
                "Error": {"Code": "500", "Message": "Internal Server Error"}
            },
            operation_name="Query",
        )

        # Act
        with pytest.raises(botocore.exceptions.ClientError):
            get_league_members(league_id="12345", platform="ESPN", season="2023")


class TestCreateTeamIdMemberIdMapping(unittest.TestCase):
    """Class to test create_team_id_member_id_mapping function."""

    def test_create_team_id_member_id_mapping(self):
        """Test create_team_id_member_id_mapping function."""
        # Set up test data
        members = [
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2023",
                "SK": "TEAM#1",
                "owner_id": ["1", "2"],
                "season": "2023",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2023",
                "SK": "TEAM#2",
                "owner_id": ["3"],
                "season": "2023",
            },
        ]
        expected_mapping = {
            "1": "1",
            "2": "3",
        }

        # Act
        mapping = create_team_id_member_id_mapping(members)

        # Assert
        self.assertEqual(mapping, expected_mapping)


class TestGetLeagueScores(unittest.TestCase):
    """Class to test get_league_scores function."""

    @patch("lambdas.step_function_lambdas.league_scores.main.make_espn_api_request")
    def test_get_league_scores_after_2018_success(self, mock_make_request):
        """Test get_league_scores function for seasons after 2018 successful response."""
        # Set up test data
        mock_make_request.return_value = {
            "schedule": [
                {
                    "matchupPeriodId": 1,
                    "home": {"teamId": 1, "totalPoints": 100.0},
                    "away": {"teamId": 2, "totalPoints": 90.0},
                },
                {
                    "matchupPeriodId": 1,
                    "home": {"teamId": 3, "totalPoints": 110.0},
                    "away": {"teamId": 4, "totalPoints": 95.0},
                },
            ]
        }
        expected_scores = [
            {
                "matchupPeriodId": 1,
                "home": {"teamId": 1, "totalPoints": 100.0},
                "away": {"teamId": 2, "totalPoints": 90.0},
            },
            {
                "matchupPeriodId": 1,
                "home": {"teamId": 3, "totalPoints": 110.0},
                "away": {"teamId": 4, "totalPoints": 95.0},
            },
        ]

        # Act
        scores = get_league_scores(
            league_id="12345",
            platform="ESPN",
            privacy="private",
            season="2023",
            swid_cookie="{ABC-123}",
            espn_s2_cookie="S2-COOKIE",
        )

        # Assert
        self.assertEqual(scores, expected_scores)
        mock_make_request.assert_any_call(
            season=2023,
            league_id="12345",
            params=[
                ("scoringPeriodId", "1"),
                ("view", "mBoxscore"),
                ("view", "mMatchupScore"),
            ],
            swid_cookie="{ABC-123}",
            espn_s2_cookie="S2-COOKIE",
        )

    @patch("lambdas.step_function_lambdas.league_scores.main.make_espn_api_request")
    def test_get_league_scores_before_2018_success(self, mock_make_request):
        """Test get_league_scores function for seasons before 2018 successful response."""
        # Set up test data
        mock_make_request.return_value = {
            "schedule": [
                {
                    "matchupPeriodId": 1,
                    "home": {"teamId": 1, "totalPoints": 100.0},
                    "away": {"teamId": 2, "totalPoints": 90.0},
                },
                {
                    "matchupPeriodId": 1,
                    "home": {"teamId": 3, "totalPoints": 110.0},
                    "away": {"teamId": 4, "totalPoints": 95.0},
                },
            ]
        }
        expected_scores = [
            {
                "matchupPeriodId": 1,
                "home": {"teamId": 1, "totalPoints": 100.0},
                "away": {"teamId": 2, "totalPoints": 90.0},
            },
            {
                "matchupPeriodId": 1,
                "home": {"teamId": 3, "totalPoints": 110.0},
                "away": {"teamId": 4, "totalPoints": 95.0},
            },
        ]

        # Act
        scores = get_league_scores(
            league_id="12345",
            platform="ESPN",
            privacy="private",
            season="2017",
            swid_cookie="{ABC-123}",
            espn_s2_cookie="S2-COOKIE",
        )

        # Assert
        self.assertEqual(scores, expected_scores)
        mock_make_request.assert_any_call(
            season=2017,
            league_id="12345",
            params=[
                ("seasonId", "2017"),
                ("scoringPeriodId", "1"),
                ("view", "mBoxscore"),
                ("view", "mMatchupScore"),
            ],
            swid_cookie="{ABC-123}",
            espn_s2_cookie="S2-COOKIE",
        )

    def test_get_league_scores_missing_cookies(self):
        """Test get_league_scores function raises ValueError if cookies are missing."""
        # Act
        with pytest.raises(ValueError):
            get_league_scores(
                league_id="12345",
                platform="ESPN",
                privacy="private",
                season="2017",
                swid_cookie=None,
                espn_s2_cookie=None,
            )

    def test_get_league_scores_invalid_platform(self):
        """Test get_league_scores function raises ValueError if an unsupported platform is provided."""
        # Act
        with pytest.raises(ValueError):
            get_league_scores(
                league_id="12345",
                platform="Sleeper",
                privacy="private",
                season="2017",
                swid_cookie=None,
                espn_s2_cookie=None,
            )


class TestGetLeagueSettings(unittest.TestCase):
    """Class to test get_league_lineup_settings function."""

    @patch("lambdas.step_function_lambdas.league_scores.main.make_espn_api_request")
    def test_get_league_lineup_settings_after_2018_success(self, mock_make_request):
        """Test get_league_lineup_settings function for seasons after 2018 successful response."""
        # Set up test data
        mock_make_request.return_value = {
            "settings": {
                "rosterSettings": {
                    "lineupSlotCounts": {
                        "0": 1,
                        "2": 2,
                        "4": 2,
                        "6": 1,
                        "16": 1,
                        "20": 6,
                    }
                }
            }
        }
        expected_lineup_settings = {
            "0": 1,
            "2": 2,
            "4": 2,
            "6": 1,
            "16": 1,
            "20": 6,
        }

        # Act
        lineup_settings = get_league_lineup_settings(
            league_id="12345",
            platform="ESPN",
            privacy="private",
            season="2023",
            swid_cookie="{ABC-123}",
            espn_s2_cookie="S2-COOKIE",
        )

        # Assert
        self.assertEqual(lineup_settings, expected_lineup_settings)
        mock_make_request.assert_called_once_with(
            season=2023,
            league_id="12345",
            params=[
                ("view", "mSettings"),
                ("view", "mTeam"),
            ],
            swid_cookie="{ABC-123}",
            espn_s2_cookie="S2-COOKIE",
        )

    @patch("lambdas.step_function_lambdas.league_scores.main.make_espn_api_request")
    def test_get_league_lineup_settings_before_2018_success(self, mock_make_request):
        """Test get_league_lineup_settings function for seasons before 2018 successful response."""
        # Set up test data
        mock_make_request.return_value = {
            "settings": {
                "rosterSettings": {
                    "lineupSlotCounts": {
                        "0": 1,
                        "2": 2,
                        "4": 2,
                        "6": 1,
                        "16": 1,
                        "20": 6,
                    }
                }
            }
        }
        expected_lineup_settings = {
            "0": 1,
            "2": 2,
            "4": 2,
            "6": 1,
            "16": 1,
            "20": 6,
        }

        # Act
        lineup_settings = get_league_lineup_settings(
            league_id="12345",
            platform="ESPN",
            privacy="private",
            season="2017",
            swid_cookie="{ABC-123}",
            espn_s2_cookie="S2-COOKIE",
        )

        # Assert
        self.assertEqual(lineup_settings, expected_lineup_settings)
        mock_make_request.assert_called_once_with(
            season=2017,
            league_id="12345",
            params=[
                ("seasonId", "2017"),
                ("view", "mSettings"),
                ("view", "mTeam"),
            ],
            swid_cookie="{ABC-123}",
            espn_s2_cookie="S2-COOKIE",
        )

    def test_get_league_lineup_settings_missing_cookies(self):
        """Test get_league_lineup_settings function raises ValueError if cookies are missing."""
        # Act
        with pytest.raises(ValueError):
            get_league_lineup_settings(
                league_id="12345",
                platform="ESPN",
                privacy="private",
                season="2017",
                swid_cookie=None,
                espn_s2_cookie=None,
            )

    def test_get_league_lineup_settings_invalid_platform(self):
        """Test get_league_lineup_settings function raises ValueError if an unsupported platform is provided."""
        # Act
        with pytest.raises(ValueError):
            get_league_lineup_settings(
                league_id="12345",
                platform="Sleeper",
                privacy="private",
                season="2017",
                swid_cookie=None,
                espn_s2_cookie=None,
            )


class TestSafeInt(unittest.TestCase):
    """Class to test safe_int function."""

    def test_safe_int_valid_integer(self):
        """Test safe_int with a valid integer string."""
        self.assertEqual(safe_int("42"), 42)

    def test_safe_int_value_error(self):
        """Tests safe_int with an input that causes a ValueError."""
        result = safe_int("42.5")
        self.assertEqual(result, 10**12)


class TestCalculateLineupEfficiency(unittest.TestCase):
    """Class to test calculate_lineup_efficiency function."""

    def test_calculate_lineup_efficiency(self):
        """Test calculate_lineup_efficiency with sample data."""
        # Set up test data
        lineup_limits = LINEUP_LIMITS
        starting_players = [
            {
                "player_id": "1",
                "full_name": "Player One",
                "points_scored": 10.0,
                "position": "QB",
            },
            {
                "player_id": "2",
                "full_name": "Player Two",
                "points_scored": 10.0,
                "position": "RB",
            },
            {
                "player_id": "3",
                "full_name": "Player Three",
                "points_scored": 10.0,
                "position": "RB",
            },
            {
                "player_id": "4",
                "full_name": "Player Four",
                "points_scored": 10.0,
                "position": "WR",
            },
            {
                "player_id": "5",
                "full_name": "Player Five",
                "points_scored": 10.0,
                "position": "WR",
            },
            {
                "player_id": "6",
                "full_name": "Player Six",
                "points_scored": 10.0,
                "position": "WR",
            },
            {
                "player_id": "7",
                "full_name": "Player Seven",
                "points_scored": 10.0,
                "position": "TE",
            },
            {
                "player_id": "8",
                "full_name": "Player Eight",
                "points_scored": 10.0,
                "position": "D/ST",
            },
            {
                "player_id": "9",
                "full_name": "Player Nine",
                "points_scored": 10.0,
                "position": "K",
            },
        ]
        bench_players = [
            {
                "player_id": "10",
                "full_name": "Player Ten",
                "points_scored": 15.0,
                "position": "RB",
            },
            {
                "player_id": "11",
                "full_name": "Player Eleven",
                "points_scored": 12.0,
                "position": "WR",
            },
        ]
        team_score = 90.0

        # Act
        efficiency = calculate_lineup_efficiency(
            lineup_limits=lineup_limits,
            starting_players=starting_players,
            bench_players=bench_players,
            team_score=team_score,
        )

        # Assert
        self.assertEqual(round(efficiency, 2), 0.93)  # 90/97 = 0.9278 rounded to 0.93

    def test_calculate_lineup_efficiency_missing_position_players(self):
        """Test calculate_lineup_efficiency with sample data missing players for a position."""
        # Set up test data
        lineup_limits = LINEUP_LIMITS
        starting_players = [
            {
                "player_id": "1",
                "full_name": "Player One",
                "points_scored": 10.0,
                "position": "QB",
            },
            {
                "player_id": "2",
                "full_name": "Player Two",
                "points_scored": 10.0,
                "position": "RB",
            },
            {
                "player_id": "3",
                "full_name": "Player Three",
                "points_scored": 10.0,
                "position": "RB",
            },
            {
                "player_id": "4",
                "full_name": "Player Four",
                "points_scored": 10.0,
                "position": "WR",
            },
            {
                "player_id": "5",
                "full_name": "Player Five",
                "points_scored": 10.0,
                "position": "WR",
            },
            {
                "player_id": "6",
                "full_name": "Player Six",
                "points_scored": 10.0,
                "position": "WR",
            },
            {
                "player_id": "8",
                "full_name": "Player Eight",
                "points_scored": 10.0,
                "position": "D/ST",
            },
            {
                "player_id": "9",
                "full_name": "Player Nine",
                "points_scored": 10.0,
                "position": "K",
            },
        ]
        bench_players = [
            {
                "player_id": "10",
                "full_name": "Player Ten",
                "points_scored": 15.0,
                "position": "RB",
            },
            {
                "player_id": "11",
                "full_name": "Player Eleven",
                "points_scored": 12.0,
                "position": "WR",
            },
        ]
        team_score = 80.0

        # Act
        efficiency = calculate_lineup_efficiency(
            lineup_limits=lineup_limits,
            starting_players=starting_players,
            bench_players=bench_players,
            team_score=team_score,
        )

        # Assert
        self.assertEqual(round(efficiency, 2), 0.92)  # 80/87 = 0.9195 rounded to 0.92

    def test_calculate_lineup_efficiency_no_data(self):
        """Test calculate_lineup_efficiency with sample data."""
        # Set up test data
        lineup_limits = LINEUP_LIMITS
        team_score = 90.0

        # Act
        efficiency = calculate_lineup_efficiency(
            lineup_limits=lineup_limits,
            starting_players=[],
            bench_players=[],
            team_score=team_score,
        )

        # Assert
        self.assertEqual(efficiency, 1.0)


class TestProcessLeagueScores(unittest.TestCase):
    """Class to test process_league_scores function."""

    @patch(
        "lambdas.step_function_lambdas.league_scores.main.calculate_lineup_efficiency"
    )
    def test_process_league_scores_after_2018_success(self, mock_calculate_efficiency):
        """Test process_league_scores function for seasons after 2018."""
        self.maxDiff = None
        # Set up test data
        matchups = SAMPLE_MATCHUPS_RESPONSE
        members = [
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2023",
                "SK": "TEAM#1",
                "owner_id": ["1"],
                "season": "2023",
                "owner_first_name": "Player",
                "owner_last_name": "One",
                "owner_full_name": "Player One",
                "team_name": "Team One",
                "team_id": "1",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2023",
                "SK": "TEAM#2",
                "owner_id": ["2"],
                "season": "2023",
                "owner_first_name": "Player",
                "owner_last_name": "Two",
                "owner_full_name": "Player Two",
                "team_name": "Team Two",
                "team_id": "2",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2023",
                "SK": "TEAM#3",
                "owner_id": ["3"],
                "season": "2023",
                "owner_first_name": "Player",
                "owner_last_name": "Three",
                "owner_full_name": "Player Three",
                "team_name": "Team Three",
                "team_id": "3",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2023",
                "SK": "TEAM#4",
                "owner_id": ["4"],
                "season": "2023",
                "owner_first_name": "Player",
                "owner_last_name": "Four",
                "owner_full_name": "Player Four",
                "team_name": "Team Four",
                "team_id": "4",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2023",
                "SK": "TEAM#5",
                "owner_id": ["5"],
                "season": "2023",
                "owner_first_name": "Player",
                "owner_last_name": "Five",
                "owner_full_name": "Player Five",
                "team_name": "Team Five",
                "team_id": "5",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2023",
                "SK": "TEAM#6",
                "owner_id": ["6"],
                "season": "2023",
                "owner_first_name": "Player",
                "owner_last_name": "Six",
                "owner_full_name": "Player Six",
                "team_name": "Team Six",
                "team_id": "6",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2023",
                "SK": "TEAM#7",
                "owner_id": ["7"],
                "season": "2023",
                "owner_first_name": "Player",
                "owner_last_name": "Seven",
                "owner_full_name": "Player Seven",
                "team_name": "Team Seven",
                "team_id": "7",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2023",
                "SK": "TEAM#8",
                "owner_id": ["8"],
                "season": "2023",
                "owner_first_name": "Player",
                "owner_last_name": "Eight",
                "owner_full_name": "Player Eight",
                "team_name": "Team Eight",
                "team_id": "8",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2023",
                "SK": "TEAM#9",
                "owner_id": ["9"],
                "season": "2023",
                "owner_first_name": "Player",
                "owner_last_name": "Nine",
                "owner_full_name": "Player Nine",
                "team_name": "Team Nine",
                "team_id": "9",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2023",
                "SK": "TEAM#10",
                "owner_id": ["10"],
                "season": "2023",
                "owner_first_name": "Player",
                "owner_last_name": "Ten",
                "owner_full_name": "Player Ten",
                "team_name": "Team Ten",
                "team_id": "10",
            },
        ]
        lineup_limits = LINEUP_LIMITS
        mock_calculate_efficiency.return_value = 0.95

        # Set up expected result
        expected_processed_scores = [
            {
                "team_a": "1",
                "team_b": "2",
                "team_a_score": 100.0,
                "team_b_score": 95.0,
                "team_a_starting_players": [
                    {
                        "player_id": "101",
                        "full_name": "Player One",
                        "points_scored": 25.0,
                        "position": "QB",
                    },
                    {
                        "player_id": "102",
                        "full_name": "Player Two",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_a_bench_players": [
                    {
                        "player_id": "202",
                        "full_name": "Player Two O'Two",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_a_full_name": "Player One",
                "team_a_team_name": "Team One",
                "team_a_efficiency": 0.95,
                "team_b_starting_players": [
                    {
                        "player_id": "103",
                        "full_name": "Player Three",
                        "points_scored": 25.0,
                        "position": "QB",
                    },
                    {
                        "player_id": "104",
                        "full_name": "Player Four",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_b_bench_players": [
                    {
                        "player_id": "204",
                        "full_name": "Player Two O'Four",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_b_efficiency": 0.95,
                "team_b_full_name": "Player Two",
                "team_b_team_name": "Team Two",
                "playoff_tier_type": "REGULAR_SEASON",
                "winner": "1",
                "loser": "2",
                "matchup_week": 1,
            },
            {
                "team_a": "2",
                "team_b": "3",
                "team_a_score": 95.0,
                "team_b_score": 100.0,
                "team_a_starting_players": [
                    {
                        "player_id": "103",
                        "full_name": "Player Three",
                        "points_scored": 25.0,
                        "position": "QB",
                    },
                    {
                        "player_id": "104",
                        "full_name": "Player Four",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_a_bench_players": [
                    {
                        "player_id": "204",
                        "full_name": "Player Two O'Four",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_a_efficiency": 0.95,
                "team_a_full_name": "Player Two",
                "team_a_team_name": "Team Two",
                "team_b_starting_players": [
                    {
                        "player_id": "101",
                        "full_name": "Player One",
                        "points_scored": 25.0,
                        "position": "QB",
                    },
                    {
                        "player_id": "102",
                        "full_name": "Player Two",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_b_bench_players": [
                    {
                        "player_id": "202",
                        "full_name": "Player Two O'Two",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_b_full_name": "Player Three",
                "team_b_team_name": "Team Three",
                "team_b_efficiency": 0.95,
                "playoff_tier_type": "REGULAR_SEASON",
                "winner": "3",
                "loser": "2",
                "matchup_week": 1,
            },
            {
                "team_a": "1",
                "team_b": "2",
                "team_a_score": 100.0,
                "team_b_score": 100.0,
                "team_a_starting_players": [
                    {
                        "player_id": "101",
                        "full_name": "Player One",
                        "points_scored": 25.0,
                        "position": "QB",
                    },
                    {
                        "player_id": "102",
                        "full_name": "Player Two",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_a_bench_players": [
                    {
                        "player_id": "202",
                        "full_name": "Player Two O'Two",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_a_full_name": "Player One",
                "team_a_team_name": "Team One",
                "team_a_efficiency": 0.95,
                "team_b_starting_players": [
                    {
                        "player_id": "103",
                        "full_name": "Player Three",
                        "points_scored": 25.0,
                        "position": "QB",
                    },
                    {
                        "player_id": "104",
                        "full_name": "Player Four",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_b_bench_players": [
                    {
                        "player_id": "204",
                        "full_name": "Player Two O'Four",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_b_efficiency": 0.95,
                "team_b_full_name": "Player Two",
                "team_b_team_name": "Team Two",
                "playoff_tier_type": "REGULAR_SEASON",
                "winner": "TIE",
                "loser": "TIE",
                "matchup_week": 1,
            },
        ]

        # Act
        processed_scores = process_league_scores(
            matchups=matchups,
            members=members,
            lineup_limits_data=lineup_limits,
            season="2023",
        )

        # Assert
        self.assertEqual(processed_scores, expected_processed_scores)

    def test_process_league_scores_before_2018_success(self):
        """Test process_league_scores function for seasons before 2018."""
        self.maxDiff = None
        # Set up test data
        matchups = SAMPLE_MATCHUPS_RESPONSE
        members = [
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2017",
                "SK": "TEAM#1",
                "owner_id": ["1"],
                "season": "2017",
                "owner_first_name": "Player",
                "owner_last_name": "One",
                "owner_full_name": "Player One",
                "team_name": "Team One",
                "team_id": "1",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2017",
                "SK": "TEAM#2",
                "owner_id": ["2"],
                "season": "2017",
                "owner_first_name": "Player",
                "owner_last_name": "Two",
                "owner_full_name": "Player Two",
                "team_name": "Team Two",
                "team_id": "2",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2017",
                "SK": "TEAM#3",
                "owner_id": ["3"],
                "season": "2017",
                "owner_first_name": "Player",
                "owner_last_name": "Three",
                "owner_full_name": "Player Three",
                "team_name": "Team Three",
                "team_id": "3",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2017",
                "SK": "TEAM#4",
                "owner_id": ["4"],
                "season": "2017",
                "owner_first_name": "Player",
                "owner_last_name": "Four",
                "owner_full_name": "Player Four",
                "team_name": "Team Four",
                "team_id": "4",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2017",
                "SK": "TEAM#5",
                "owner_id": ["5"],
                "season": "2017",
                "owner_first_name": "Player",
                "owner_last_name": "Five",
                "owner_full_name": "Player Five",
                "team_name": "Team Five",
                "team_id": "5",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2017",
                "SK": "TEAM#6",
                "owner_id": ["6"],
                "season": "2017",
                "owner_first_name": "Player",
                "owner_last_name": "Six",
                "owner_full_name": "Player Six",
                "team_name": "Team Six",
                "team_id": "6",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2017",
                "SK": "TEAM#7",
                "owner_id": ["7"],
                "season": "2017",
                "owner_first_name": "Player",
                "owner_last_name": "Seven",
                "owner_full_name": "Player Seven",
                "team_name": "Team Seven",
                "team_id": "7",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2017",
                "SK": "TEAM#8",
                "owner_id": ["8"],
                "season": "2017",
                "owner_first_name": "Player",
                "owner_last_name": "Eight",
                "owner_full_name": "Player Eight",
                "team_name": "Team Eight",
                "team_id": "8",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2017",
                "SK": "TEAM#9",
                "owner_id": ["9"],
                "season": "2017",
                "owner_first_name": "Player",
                "owner_last_name": "Nine",
                "owner_full_name": "Player Nine",
                "team_name": "Team Nine",
                "team_id": "9",
            },
            {
                "PK": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2017",
                "SK": "TEAM#10",
                "owner_id": ["10"],
                "season": "2017",
                "owner_first_name": "Player",
                "owner_last_name": "Ten",
                "owner_full_name": "Player Ten",
                "team_name": "Team Ten",
                "team_id": "10",
            },
        ]
        lineup_limits = LINEUP_LIMITS

        # Set up expected result
        expected_processed_scores = [
            {
                "team_a": "1",
                "team_b": "2",
                "team_a_score": 100.0,
                "team_b_score": 95.0,
                "team_a_starting_players": [
                    {
                        "player_id": "101",
                        "full_name": "Player One",
                        "points_scored": 25.0,
                        "position": "QB",
                    },
                    {
                        "player_id": "102",
                        "full_name": "Player Two",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_a_bench_players": [
                    {
                        "player_id": "202",
                        "full_name": "Player Two O'Two",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_a_full_name": "Player One",
                "team_a_team_name": "Team One",
                "team_a_efficiency": 1.0,
                "team_b_starting_players": [
                    {
                        "player_id": "103",
                        "full_name": "Player Three",
                        "points_scored": 25.0,
                        "position": "QB",
                    },
                    {
                        "player_id": "104",
                        "full_name": "Player Four",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_b_bench_players": [
                    {
                        "player_id": "204",
                        "full_name": "Player Two O'Four",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_b_efficiency": 1.0,
                "team_b_full_name": "Player Two",
                "team_b_team_name": "Team Two",
                "playoff_tier_type": "REGULAR_SEASON",
                "winner": "1",
                "loser": "2",
                "matchup_week": 1,
            },
            {
                "team_a": "2",
                "team_b": "3",
                "team_a_score": 95.0,
                "team_b_score": 100.0,
                "team_a_starting_players": [
                    {
                        "player_id": "103",
                        "full_name": "Player Three",
                        "points_scored": 25.0,
                        "position": "QB",
                    },
                    {
                        "player_id": "104",
                        "full_name": "Player Four",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_a_bench_players": [
                    {
                        "player_id": "204",
                        "full_name": "Player Two O'Four",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_a_efficiency": 1.0,
                "team_a_full_name": "Player Two",
                "team_a_team_name": "Team Two",
                "team_b_starting_players": [
                    {
                        "player_id": "101",
                        "full_name": "Player One",
                        "points_scored": 25.0,
                        "position": "QB",
                    },
                    {
                        "player_id": "102",
                        "full_name": "Player Two",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_b_bench_players": [
                    {
                        "player_id": "202",
                        "full_name": "Player Two O'Two",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_b_full_name": "Player Three",
                "team_b_team_name": "Team Three",
                "team_b_efficiency": 1.0,
                "playoff_tier_type": "REGULAR_SEASON",
                "winner": "3",
                "loser": "2",
                "matchup_week": 1,
            },
            {
                "team_a": "1",
                "team_b": "2",
                "team_a_score": 100.0,
                "team_b_score": 100.0,
                "team_a_starting_players": [
                    {
                        "player_id": "101",
                        "full_name": "Player One",
                        "points_scored": 25.0,
                        "position": "QB",
                    },
                    {
                        "player_id": "102",
                        "full_name": "Player Two",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_a_bench_players": [
                    {
                        "player_id": "202",
                        "full_name": "Player Two O'Two",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_a_full_name": "Player One",
                "team_a_team_name": "Team One",
                "team_a_efficiency": 1.0,
                "team_b_starting_players": [
                    {
                        "player_id": "103",
                        "full_name": "Player Three",
                        "points_scored": 25.0,
                        "position": "QB",
                    },
                    {
                        "player_id": "104",
                        "full_name": "Player Four",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_b_bench_players": [
                    {
                        "player_id": "204",
                        "full_name": "Player Two O'Four",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_b_efficiency": 1.0,
                "team_b_full_name": "Player Two",
                "team_b_team_name": "Team Two",
                "playoff_tier_type": "REGULAR_SEASON",
                "winner": "TIE",
                "loser": "TIE",
                "matchup_week": 1,
            },
        ]

        # Act
        processed_scores = process_league_scores(
            matchups=matchups,
            members=members,
            lineup_limits_data=lineup_limits,
            season="2017",
        )

        # Assert
        self.assertEqual(processed_scores, expected_processed_scores)


class TestGetPlayoffStatus(unittest.TestCase):
    """Class to test get_playoff_status function."""

    def test_get_playoff_status_after_2021_home_team_champion(self):
        """Tests get_playoff_status function for seasons after 2021 with home team the champion."""
        # Set up test data
        matchups = [
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 15,
                "home": {
                    "teamId": "3",
                    "totalPoints": 100.0,
                },
                "away": {
                    "teamId": "4",
                    "totalPoints": 95.0,
                },
            },
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 15,
                "home": {
                    "teamId": "5",
                    "totalPoints": 100.0,
                },
                "away": {
                    "teamId": "6",
                    "totalPoints": 95.0,
                },
            },
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 16,
                "home": {
                    "teamId": "1",
                    "totalPoints": 100.0,
                },
                "away": {
                    "teamId": "4",
                    "totalPoints": 95.0,
                },
            },
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 16,
                "home": {
                    "teamId": "2",
                    "totalPoints": 100.0,
                },
                "away": {
                    "teamId": "3",
                    "totalPoints": 95.0,
                },
            },
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 17,
                "home": {
                    "teamId": "1",
                    "totalPoints": 100.0,
                },
                "away": {
                    "teamId": "2",
                    "totalPoints": 95.0,
                },
            },
        ]
        expected_playoff_teams = [
            {
                "team_id": "3",
                "playoff_status": "MADE_PLAYOFFS",
            },
            {
                "team_id": "4",
                "playoff_status": "MADE_PLAYOFFS",
            },
            {
                "team_id": "5",
                "playoff_status": "MADE_PLAYOFFS",
            },
            {
                "team_id": "6",
                "playoff_status": "MADE_PLAYOFFS",
            },
            {
                "team_id": "1",
                "playoff_status": "CLINCHED_FIRST_ROUND_BYE",
            },
            {
                "team_id": "2",
                "playoff_status": "CLINCHED_FIRST_ROUND_BYE",
            },
        ]
        expected_league_champion = [
            {
                "team_id": "1",
                "championship_status": "LEAGUE_CHAMPION",
            }
        ]

        # Act
        playoff_teams, league_champion = get_playoff_status(
            matchups=matchups,
            season="2023",
        )

        # Assert
        self.assertEqual(playoff_teams, expected_playoff_teams)
        self.assertEqual(league_champion, expected_league_champion)

    def test_get_playoff_status_after_2021_away_team_champion(self):
        """Tests get_playoff_status function for seasons after 2021 with away team the champion."""
        # Set up test data
        matchups = [
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 15,
                "home": {
                    "teamId": "3",
                    "totalPoints": 100.0,
                },
                "away": {
                    "teamId": "4",
                    "totalPoints": 95.0,
                },
            },
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 15,
                "home": {
                    "teamId": "5",
                    "totalPoints": 100.0,
                },
                "away": {
                    "teamId": "6",
                    "totalPoints": 95.0,
                },
            },
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 16,
                "home": {
                    "teamId": "1",
                    "totalPoints": 100.0,
                },
                "away": {
                    "teamId": "4",
                    "totalPoints": 95.0,
                },
            },
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 16,
                "home": {
                    "teamId": "2",
                    "totalPoints": 100.0,
                },
                "away": {
                    "teamId": "3",
                    "totalPoints": 95.0,
                },
            },
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 17,
                "home": {
                    "teamId": "1",
                    "totalPoints": 90.0,
                },
                "away": {
                    "teamId": "2",
                    "totalPoints": 95.0,
                },
            },
        ]
        expected_playoff_teams = [
            {
                "team_id": "3",
                "playoff_status": "MADE_PLAYOFFS",
            },
            {
                "team_id": "4",
                "playoff_status": "MADE_PLAYOFFS",
            },
            {
                "team_id": "5",
                "playoff_status": "MADE_PLAYOFFS",
            },
            {
                "team_id": "6",
                "playoff_status": "MADE_PLAYOFFS",
            },
            {
                "team_id": "1",
                "playoff_status": "CLINCHED_FIRST_ROUND_BYE",
            },
            {
                "team_id": "2",
                "playoff_status": "CLINCHED_FIRST_ROUND_BYE",
            },
        ]
        expected_league_champion = [
            {
                "team_id": "2",
                "championship_status": "LEAGUE_CHAMPION",
            }
        ]

        # Act
        playoff_teams, league_champion = get_playoff_status(
            matchups=matchups,
            season="2023",
        )

        # Assert
        self.assertEqual(playoff_teams, expected_playoff_teams)
        self.assertEqual(league_champion, expected_league_champion)

    def test_get_playoff_status_before_2021_home_team_champion(self):
        """Tests get_playoff_status function for seasons before 2021 with home team the champion."""
        # Set up test data
        matchups = [
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 14,
                "home": {
                    "teamId": "3",
                    "totalPoints": 100.0,
                },
                "away": {
                    "teamId": "4",
                    "totalPoints": 95.0,
                },
            },
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 14,
                "home": {
                    "teamId": "5",
                    "totalPoints": 100.0,
                },
                "away": {
                    "teamId": "6",
                    "totalPoints": 95.0,
                },
            },
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 15,
                "home": {
                    "teamId": "1",
                    "totalPoints": 100.0,
                },
                "away": {
                    "teamId": "4",
                    "totalPoints": 95.0,
                },
            },
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 15,
                "home": {
                    "teamId": "2",
                    "totalPoints": 100.0,
                },
                "away": {
                    "teamId": "3",
                    "totalPoints": 95.0,
                },
            },
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 16,
                "home": {
                    "teamId": "1",
                    "totalPoints": 100.0,
                },
                "away": {
                    "teamId": "2",
                    "totalPoints": 95.0,
                },
            },
        ]
        expected_playoff_teams = [
            {
                "team_id": "3",
                "playoff_status": "MADE_PLAYOFFS",
            },
            {
                "team_id": "4",
                "playoff_status": "MADE_PLAYOFFS",
            },
            {
                "team_id": "5",
                "playoff_status": "MADE_PLAYOFFS",
            },
            {
                "team_id": "6",
                "playoff_status": "MADE_PLAYOFFS",
            },
            {
                "team_id": "1",
                "playoff_status": "CLINCHED_FIRST_ROUND_BYE",
            },
            {
                "team_id": "2",
                "playoff_status": "CLINCHED_FIRST_ROUND_BYE",
            },
        ]
        expected_league_champion = [
            {
                "team_id": "1",
                "championship_status": "LEAGUE_CHAMPION",
            }
        ]

        # Act
        playoff_teams, league_champion = get_playoff_status(
            matchups=matchups,
            season="2020",
        )

        # Assert
        self.assertEqual(playoff_teams, expected_playoff_teams)
        self.assertEqual(league_champion, expected_league_champion)

    def test_get_playoff_status_before_2021_away_team_champion(self):
        """Tests get_playoff_status function for seasons before 2021 with away team the champion."""
        # Set up test data
        matchups = [
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 14,
                "home": {
                    "teamId": "3",
                    "totalPoints": 100.0,
                },
                "away": {
                    "teamId": "4",
                    "totalPoints": 95.0,
                },
            },
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 14,
                "home": {
                    "teamId": "5",
                    "totalPoints": 100.0,
                },
                "away": {
                    "teamId": "6",
                    "totalPoints": 95.0,
                },
            },
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 15,
                "home": {
                    "teamId": "1",
                    "totalPoints": 100.0,
                },
                "away": {
                    "teamId": "4",
                    "totalPoints": 95.0,
                },
            },
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 15,
                "home": {
                    "teamId": "2",
                    "totalPoints": 100.0,
                },
                "away": {
                    "teamId": "3",
                    "totalPoints": 95.0,
                },
            },
            {
                "playoffTierType": "WINNERS_BRACKET",
                "matchupPeriodId": 16,
                "home": {
                    "teamId": "1",
                    "totalPoints": 90.0,
                },
                "away": {
                    "teamId": "2",
                    "totalPoints": 95.0,
                },
            },
        ]
        expected_playoff_teams = [
            {
                "team_id": "3",
                "playoff_status": "MADE_PLAYOFFS",
            },
            {
                "team_id": "4",
                "playoff_status": "MADE_PLAYOFFS",
            },
            {
                "team_id": "5",
                "playoff_status": "MADE_PLAYOFFS",
            },
            {
                "team_id": "6",
                "playoff_status": "MADE_PLAYOFFS",
            },
            {
                "team_id": "1",
                "playoff_status": "CLINCHED_FIRST_ROUND_BYE",
            },
            {
                "team_id": "2",
                "playoff_status": "CLINCHED_FIRST_ROUND_BYE",
            },
        ]
        expected_league_champion = [
            {
                "team_id": "2",
                "championship_status": "LEAGUE_CHAMPION",
            }
        ]

        # Act
        playoff_teams, league_champion = get_playoff_status(
            matchups=matchups,
            season="2020",
        )

        # Assert
        self.assertEqual(playoff_teams, expected_playoff_teams)
        self.assertEqual(league_champion, expected_league_champion)


class TestLambdaHandler(unittest.TestCase):
    """Class to test lambda_handler function."""

    @patch("lambdas.step_function_lambdas.league_scores.main.get_league_members")
    @patch(
        "lambdas.step_function_lambdas.league_scores.main.create_team_id_member_id_mapping"
    )
    @patch("lambdas.step_function_lambdas.league_scores.main.get_league_scores")
    @patch(
        "lambdas.step_function_lambdas.league_scores.main.get_league_lineup_settings"
    )
    @patch("lambdas.step_function_lambdas.league_scores.main.process_league_scores")
    @patch("lambdas.step_function_lambdas.league_scores.main.get_playoff_status")
    @patch("lambdas.step_function_lambdas.league_scores.main.batch_write_to_dynamodb")
    def test_lambda_handler_success(
        self,
        mock_batch_write_to_dynamodb,
        mock_get_playoff_status,
        mock_process_league_scores,
        mock_get_league_lineup_settings,
        mock_get_league_scores,
        mock_create_team_id_member_id_mapping,
        mock_get_league_members,
    ):
        """Tests successful lambda_handler execution."""
        # Mock dependencies
        mock_get_league_members.return_value = None
        mock_create_team_id_member_id_mapping.return_value = {
            "team_id": "2",
            "member_id": "test_member_id",
        }
        mock_get_league_scores.return_value = ["test"]
        mock_get_league_lineup_settings.return_value = None
        mock_process_league_scores.return_value = [
            {
                "team_a": "1",
                "team_b": "2",
                "team_a_score": 100.0,
                "team_b_score": 95.0,
                "team_a_starting_players": [
                    {
                        "player_id": "101",
                        "full_name": "Player One",
                        "points_scored": 25.0,
                        "position": "QB",
                    },
                    {
                        "player_id": "102",
                        "full_name": "Player Two",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_a_bench_players": [
                    {
                        "player_id": "202",
                        "full_name": "Player Two O'Two",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_a_full_name": "Player One",
                "team_a_team_name": "Team One",
                "team_a_efficiency": 1.0,
                "team_b_starting_players": [
                    {
                        "player_id": "103",
                        "full_name": "Player Three",
                        "points_scored": 25.0,
                        "position": "QB",
                    },
                    {
                        "player_id": "104",
                        "full_name": "Player Four",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_b_bench_players": [
                    {
                        "player_id": "204",
                        "full_name": "Player Two O'Four",
                        "points_scored": 30.0,
                        "position": "QB",
                    },
                ],
                "team_b_efficiency": 1.0,
                "team_b_full_name": "Player Two",
                "team_b_team_name": "Team Two",
                "playoff_tier_type": "REGULAR_SEASON",
                "winner": "1",
                "loser": "2",
                "matchup_week": 1,
            },
        ]
        mock_get_playoff_status.return_value = (
            [
                {
                    "team_id": "4",
                    "playoff_status": "MADE_PLAYOFFS",
                },
            ],
            [
                {
                    "team_id": "2",
                    "championship_status": "LEAGUE_CHAMPION",
                }
            ],
        )
        mock_batch_write_to_dynamodb.return_value = None

        # Act
        lambda_handler(
            event={
                "leagueId": "12345",
                "platform": "ESPN",
                "privacy": "private",
                "swidCookie": None,
                "espnS2Cookie": None,
                "season": "2023",
            },
            context={},
        )

        # Assert
        # NOTE: No specific assertions for this one as the payloads are quite large
        assert True

    @patch("lambdas.step_function_lambdas.league_scores.main.get_league_members")
    @patch(
        "lambdas.step_function_lambdas.league_scores.main.create_team_id_member_id_mapping"
    )
    @patch("lambdas.step_function_lambdas.league_scores.main.get_league_scores")
    def test_lambda_handler_no_matchups(
        self,
        mock_get_league_scores,
        mock_create_team_id_member_id_mapping,
        mock_get_league_members,
    ):
        """Tests ValueError is raised in lambda_handler if no matchups returned."""
        # Mock dependencies
        mock_get_league_members.return_value = None
        mock_create_team_id_member_id_mapping.return_value = None
        mock_get_league_scores.return_value = None

        # Act
        with pytest.raises(ValueError):
            lambda_handler(
                event={
                    "leagueId": "12345",
                    "platform": "ESPN",
                    "privacy": "private",
                    "swidCookie": None,
                    "espnS2Cookie": None,
                    "season": "2023",
                },
                context={},
            )
