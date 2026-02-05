import unittest
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from api.models import APIResponse
from api.routers.matchups import (
    filter_dynamo_db_response,
    get_specific_matchup_two_teams,
    get_specific_matchup_one_team,
    get_all_time_matchups,
    get_weekly_matchups,
    get_team_season_matchups,
    get_team_all_time_matchups,
    get_matchups,
)
import api.routers.matchups as matchups_module


class TestFilterDynamoDBResponse(unittest.TestCase):
    """Tests for filter_dynamodb_response function."""

    def test_filter_dynamo_db_response_include_playoff_matchups(self):
        """Test filtering with playoff matchups included."""
        # Set up mock DynamoDB response
        mock_response = {
            "Items": [
                {"team_id": {"S": "1"}, "week": {"N": "1"}, "score": {"N": "100"}},
                {"team_id": {"S": "2"}, "week": {"N": "1"}, "score": {"N": "150"}},
            ]
        }
        expected_output = [
            {"team_id": "1", "week": 1, "score": 100},
            {"team_id": "2", "week": 1, "score": 150},
        ]

        # Act
        result = filter_dynamo_db_response(
            response=mock_response, playoff_filter="include"
        )

        # Assert
        self.assertEqual(result, expected_output)

    def test_filter_dynamo_db_response_exclude_playoff_matchups(self):
        """Test filtering with playoff matchups excluded."""
        # Set up mock DynamoDB response
        mock_response = {
            "Items": [
                {
                    "team_id": {"S": "1"},
                    "week": {"N": "1"},
                    "score": {"N": "100"},
                    "playoff_tier_type": {"S": "NONE"},
                },
                {
                    "team_id": {"S": "2"},
                    "week": {"N": "15"},
                    "score": {"N": "150"},
                    "playoff_tier_type": {"S": "PLAYOFF"},
                },
            ]
        }
        expected_output = [
            {"team_id": "1", "week": 1, "score": 100, "playoff_tier_type": "NONE"}
        ]

        # Act
        result = filter_dynamo_db_response(
            response=mock_response, playoff_filter="exclude"
        )

        # Assert
        self.assertEqual(result, expected_output)

    def test_filter_dynamo_db_response_only_playoff_matchups(self):
        """Test filtering with only playoff matchups."""
        # Set up mock DynamoDB response
        mock_response = {
            "Items": [
                {
                    "team_id": {"S": "1"},
                    "week": {"N": "1"},
                    "score": {"N": "100"},
                    "playoff_tier_type": {"S": "NONE"},
                },
                {
                    "team_id": {"S": "2"},
                    "week": {"N": "15"},
                    "score": {"N": "150"},
                    "playoff_tier_type": {"S": "WINNERS_BRACKET"},
                },
            ]
        }
        expected_output = [
            {
                "team_id": "2",
                "week": 15,
                "score": 150,
                "playoff_tier_type": "WINNERS_BRACKET",
            }
        ]

        # Act
        result = filter_dynamo_db_response(
            response=mock_response, playoff_filter="only"
        )

        # Assert
        self.assertEqual(result, expected_output)


class TestGetSpecificMatchupTwoTeams(unittest.TestCase):
    """Tests for get_specific_matchup_two_teams function."""

    @patch("api.routers.matchups.dynamodb_client")
    def test_get_specific_matchup_two_teams_success(self, mock_dynamodb_client):
        """Test retrieving specific matchup between two teams."""
        # Set up mock query response
        mock_query = mock_dynamodb_client.query
        mock_query.side_effect = [
            {
                "Items": [
                    {
                        "team_id": {"S": "1"},
                        "opponent_id": {"S": "2"},
                        "week": {"N": "1"},
                        "score": {"N": "100"},
                    },
                ]
            },
            {},
        ]
        expected_output = [
            {"team_id": "1", "opponent_id": "2", "week": 1, "score": 100},
        ]

        # Act
        result = get_specific_matchup_two_teams(
            league_id="12345",
            platform="espn",
            playoff_filter="include",
            team1_id="1",
            team2_id="2",
            season="2025",
            week_number="1",
        )

        # Assert
        self.assertEqual(result.data, expected_output)

    @patch("api.routers.matchups.dynamodb_client")
    def test_get_specific_matchup_two_teams_no_matchup(self, mock_dynamodb_client):
        """Test retrieving specific matchup between two teams and no matchup found."""
        # Set up mock query response
        mock_query = mock_dynamodb_client.query
        mock_query.side_effect = [{}, {}]

        # Act
        with pytest.raises(HTTPException) as exc_info:
            get_specific_matchup_two_teams(
                league_id="12345",
                platform="espn",
                playoff_filter="include",
                team1_id="1",
                team2_id="2",
                season="2025",
                week_number="1",
            )

        # Assert
        self.assertEqual(exc_info.value.status_code, 404)
        self.assertEqual(
            exc_info.value.detail,
            "No matchup between 1 and 2 for 2025 week 1",
        )


class TestGetSpecificMatchupOneTeam(unittest.TestCase):
    """Tests for get_specific_matchup_one_team function."""

    @patch("api.routers.matchups.dynamodb_client")
    def test_get_specific_matchup_one_team_success(self, mock_dynamodb_client):
        """Test retrieving specific matchup for one team."""
        # Set up mock query response
        mock_query = mock_dynamodb_client.query
        mock_query.side_effect = [
            {
                "Items": [
                    {
                        "team_id": {"S": "1"},
                        "opponent_id": {"S": "2"},
                        "week": {"N": "1"},
                        "score": {"N": "100"},
                    },
                ]
            },
            {},
        ]
        expected_output = [
            {"team_id": "1", "opponent_id": "2", "week": 1, "score": 100},
        ]

        # Act
        result = get_specific_matchup_one_team(
            league_id="12345",
            platform="espn",
            playoff_filter="include",
            team1_id="1",
            season="2025",
            week_number="1",
        )

        # Assert
        self.assertEqual(result.data, expected_output)

    @patch("api.routers.matchups.dynamodb_client")
    def test_get_specific_matchup_one_team_no_matchup(self, mock_dynamodb_client):
        """Test retrieving specific matchup for one team and no matchup found."""
        # Set up mock query response
        mock_query = mock_dynamodb_client.query
        mock_query.side_effect = [{}, {}]

        # Act
        with pytest.raises(HTTPException) as exc_info:
            get_specific_matchup_one_team(
                league_id="12345",
                platform="espn",
                playoff_filter="include",
                team1_id="1",
                season="2025",
                week_number="1",
            )

        # Assert
        self.assertEqual(exc_info.value.status_code, 404)
        self.assertEqual(
            exc_info.value.detail,
            "No matchup for 1 for 2025 week 1",
        )


class TestGetAllTimeMatchups(unittest.TestCase):
    """Tests for get_all_time_matchups function."""

    @patch("api.routers.matchups.dynamodb_client")
    def test_get_all_time_matchups_success(self, mock_dynamodb_client):
        """Test retrieving all time matchups."""
        # Set up mock query response
        mock_query = mock_dynamodb_client.query
        mock_query.side_effect = [
            {
                "Items": [
                    {
                        "team_id": {"S": "1"},
                        "opponent_id": {"S": "2"},
                        "week": {"N": "1"},
                        "score": {"N": "100"},
                    },
                ]
            },
            {
                "Items": [
                    {
                        "team_id": {"S": "1"},
                        "opponent_id": {"S": "2"},
                        "week": {"N": "10"},
                        "score": {"N": "100"},
                    },
                ]
            },
        ]
        expected_output = [
            {"team_id": "1", "opponent_id": "2", "week": 1, "score": 100},
            {"team_id": "1", "opponent_id": "2", "week": 10, "score": 100},
        ]

        # Act
        result = get_all_time_matchups(
            league_id="12345",
            platform="espn",
            playoff_filter="include",
            team1_id="1",
            team2_id="2",
        )

        # Assert
        self.assertEqual(result.data, expected_output)

    @patch("api.routers.matchups.dynamodb_client")
    def test_get_all_time_matchups_no_matchup(self, mock_dynamodb_client):
        """Test retrieving all time matchups and no matchups found."""
        # Set up mock query response
        mock_query = mock_dynamodb_client.query
        mock_query.side_effect = [{}, {}]

        # Act
        with pytest.raises(HTTPException) as exc_info:
            get_all_time_matchups(
                league_id="12345",
                platform="espn",
                playoff_filter="include",
                team1_id="1",
                team2_id="2",
            )

        # Assert
        self.assertEqual(exc_info.value.status_code, 404)
        self.assertEqual(
            exc_info.value.detail,
            "No matchups between 1 and 2",
        )


class TestGetWeeklyMatchups(unittest.TestCase):
    """Tests for get_weekly_matchups function."""

    @patch("api.routers.matchups.dynamodb_client")
    def test_get_weekly_matchups_success(self, mock_dynamodb_client):
        """Test retrieving weekly matchups."""
        # Set up mock query response
        mock_query = mock_dynamodb_client.query
        mock_query.side_effect = [
            {
                "Items": [
                    {
                        "team_id": {"S": "1"},
                        "opponent_id": {"S": "2"},
                        "week": {"N": "1"},
                        "score": {"N": "100"},
                    },
                    {
                        "team_id": {"S": "3"},
                        "opponent_id": {"S": "4"},
                        "week": {"N": "1"},
                        "score": {"N": "100"},
                    },
                ]
            }
        ]
        expected_output = [
            {"team_id": "1", "opponent_id": "2", "week": 1, "score": 100},
            {"team_id": "3", "opponent_id": "4", "week": 1, "score": 100},
        ]

        # Act
        result = get_weekly_matchups(
            league_id="12345",
            platform="espn",
            playoff_filter="include",
            season="2025",
            week_number="1",
        )

        # Assert
        self.assertEqual(result.data, expected_output)

    @patch("api.routers.matchups.dynamodb_client")
    def test_get_weekly_matchups_no_matchup(self, mock_dynamodb_client):
        """Test retrieving weekly matchups and no matchups found."""
        # Set up mock query response
        mock_query = mock_dynamodb_client.query
        mock_query.side_effect = [{}]

        # Act
        with pytest.raises(HTTPException) as exc_info:
            get_weekly_matchups(
                league_id="12345",
                platform="espn",
                playoff_filter="include",
                season="2025",
                week_number="1",
            )

        # Assert
        self.assertEqual(exc_info.value.status_code, 404)
        self.assertEqual(
            exc_info.value.detail,
            "No matchups found for 2025 season week 1",
        )


class TestGetTeamSeasonMatchups(unittest.TestCase):
    """Tests for get_team_season_matchups function."""

    @patch("api.routers.matchups.dynamodb_client")
    def test_get_team_season_matchups_success(self, mock_dynamodb_client):
        """Test retrieving team season matchups."""
        # Set up mock query response
        mock_query = mock_dynamodb_client.query
        mock_query.side_effect = [
            {
                "Items": [
                    {
                        "team_id": {"S": "1"},
                        "opponent_id": {"S": "2"},
                        "week": {"N": "1"},
                        "score": {"N": "100"},
                    },
                    {
                        "team_id": {"S": "1"},
                        "opponent_id": {"S": "4"},
                        "week": {"N": "2"},
                        "score": {"N": "100"},
                    },
                ]
            }
        ]
        expected_output = [
            {"team_id": "1", "opponent_id": "2", "week": 1, "score": 100},
            {"team_id": "1", "opponent_id": "4", "week": 2, "score": 100},
        ]

        # Act
        result = get_team_season_matchups(
            league_id="12345",
            platform="espn",
            playoff_filter="include",
            team1_id="1",
            season="2025",
        )

        # Assert
        self.assertEqual(result.data, expected_output)

    @patch("api.routers.matchups.dynamodb_client")
    def test_get_team_season_matchups_no_matchup(self, mock_dynamodb_client):
        """Test retrieving team season matchups and no matchups found."""
        # Set up mock query response
        mock_query = mock_dynamodb_client.query
        mock_query.side_effect = [{}]

        # Act
        with pytest.raises(HTTPException) as exc_info:
            get_team_season_matchups(
                league_id="12345",
                platform="espn",
                playoff_filter="include",
                team1_id="1",
                season="2025",
            )

        # Assert
        self.assertEqual(exc_info.value.status_code, 404)
        self.assertEqual(
            exc_info.value.detail,
            "No matchups found for team 1 in 2025 season",
        )


class TestGetTeamAllTimeMatchups(unittest.TestCase):
    """Tests for get_team_all_time_matchups function."""

    @patch("api.routers.matchups.dynamodb_client")
    def test_get_team_all_time_matchups_success(self, mock_dynamodb_client):
        """Test retrieving team all time matchups."""
        # Set up mock query response
        mock_query = mock_dynamodb_client.query
        mock_query.side_effect = [
            {
                "Items": [
                    {
                        "team_id": {"S": "1"},
                        "opponent_id": {"S": "2"},
                        "week": {"N": "1"},
                        "score": {"N": "100"},
                    },
                    {
                        "team_id": {"S": "1"},
                        "opponent_id": {"S": "4"},
                        "week": {"N": "2"},
                        "score": {"N": "100"},
                    },
                ]
            }
        ]
        expected_output = [
            {"team_id": "1", "opponent_id": "2", "week": 1, "score": 100},
            {"team_id": "1", "opponent_id": "4", "week": 2, "score": 100},
        ]

        # Act
        result = get_team_all_time_matchups(
            league_id="12345",
            platform="espn",
            playoff_filter="include",
            team1_id="1",
        )

        # Assert
        self.assertEqual(result.data, expected_output)

    @patch("api.routers.matchups.dynamodb_client")
    def test_get_team_all_time_matchups_no_matchup(self, mock_dynamodb_client):
        """Test retrieving team all time matchups and no matchups found."""
        # Set up mock query response
        mock_query = mock_dynamodb_client.query
        mock_query.side_effect = [{}]

        # Act
        with pytest.raises(HTTPException) as exc_info:
            get_team_all_time_matchups(
                league_id="12345",
                platform="espn",
                playoff_filter="include",
                team1_id="1",
            )

        # Assert
        self.assertEqual(exc_info.value.status_code, 404)
        self.assertEqual(
            exc_info.value.detail,
            "No matchups found for team 1 across all seasons",
        )


class TestGetMatchups(unittest.TestCase):
    """Tests for get_matchups function."""

    @patch("api.routers.matchups.get_specific_matchup_two_teams")
    def test_get_matchups_success(self, mock_get_specific_matchup_two_teams):
        """Test get_matchups success with get_specific_matchup_two_teams."""
        # Set up mock return value
        mock_get_specific_matchup_two_teams.return_value = APIResponse(
            detail="Found matchup between 1 and 2 for 2025 week 1",
            data="two_teams_result",
        )

        # Ensure the QUERY_HANDLERS mapping uses the mocked handler
        matchups_module.QUERY_HANDLERS[(True, True, True, True)] = (
            mock_get_specific_matchup_two_teams
        )

        # Act
        result = get_matchups(
            league_id="12345",
            platform="espn",
            playoff_filter="include",
            team1_id="1",
            team2_id="2",
            season="2025",
            week_number="1",
        )

        # Assert
        self.assertEqual(result.detail, "Found matchup between 1 and 2 for 2025 week 1")
        self.assertEqual(result.data, "two_teams_result")
        mock_get_specific_matchup_two_teams.assert_called_once_with(
            league_id="12345",
            platform="espn",
            playoff_filter="include",
            team1_id="1",
            team2_id="2",
            season="2025",
            week_number="1",
        )

    def test_get_matchups_no_handler(self):
        """Test get_matchups with no matching handler."""
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            get_matchups(
                league_id="12345",
                platform="espn",
                playoff_filter="include",
                team1_id=None,
                team2_id=None,
                season=None,
                week_number=None,
            )

        self.assertEqual(exc_info.value.status_code, 400)
        self.assertEqual(
            exc_info.value.detail,
            "Invalid combination of query parameters: season=None, week_number=None, team1_id=None, team2_id=None",
        )
