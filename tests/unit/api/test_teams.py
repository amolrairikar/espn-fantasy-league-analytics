import unittest
from unittest.mock import patch

from api.models import APIResponse
from api.routers.teams import (
    get_teams,
)


class TestGetTeams(unittest.TestCase):
    """Tests for get_teams endpoint."""

    @patch("api.routers.teams.query_dynamodb")
    def test_get_all_teams(self, mock_query_dynamodb):
        """Test the get_teams endpoint for all teams."""
        # Set up mock data
        mock_response = APIResponse(
            detail="Found all teams for the league",
            data=[{"Team": "Test Team 1"}, {"Team": "Test Team 2"}],
        )
        mock_query_dynamodb.return_value = mock_response

        # Act
        result = get_teams(
            league_id="123",
            platform="ESPN",
            season="2025",
            team_id=None,
        )

        # Assert
        self.assertEqual(result, mock_response)
        mock_query_dynamodb.assert_called_once_with(
            pk="LEAGUE#123#PLATFORM#ESPN#SEASON#2025",
            sk_prefix="TEAM#",
        )

    @patch("api.routers.teams.query_dynamodb")
    def test_get_single_team(self, mock_query_dynamodb):
        """Test the get_teams endpoint for a single team."""
        # Set up mock data
        mock_response = APIResponse(
            detail="Found all teams for the league",
            data=[{"Team": "Test Team 1"}],
        )
        mock_query_dynamodb.return_value = mock_response

        # Act
        result = get_teams(
            league_id="123",
            platform="ESPN",
            season="2025",
            team_id="1",
        )

        # Assert
        self.assertEqual(result, mock_response)
        mock_query_dynamodb.assert_called_once_with(
            pk="LEAGUE#123#PLATFORM#ESPN#SEASON#2025",
            sk_prefix="TEAM#1",
        )
