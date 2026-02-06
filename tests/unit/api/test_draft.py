import unittest
from unittest.mock import patch

from api.routers.draft import get_draft_results


class TestGetDraftResults(unittest.TestCase):
    """Tests for get_draft_results function."""

    @patch("api.routers.draft.query_dynamodb")
    def test_get_draft_results_success(self, mock_query_dynamodb):
        """Tests successful retrieval of draft results."""
        # Set up mock data
        league_id = "12345"
        platform = "ESPN"
        season = "2023"
        mock_response = {
            "Items": [
                {
                    "pick_number": {"N": "1"},
                    "team_id": {"S": "10"},
                    "player_id": {"S": "100"},
                },
                {
                    "pick_number": {"N": "2"},
                    "team_id": {"S": "11"},
                    "player_id": {"S": "101"},
                },
            ]
        }
        mock_query_dynamodb.return_value = mock_response

        # Act
        result = get_draft_results(
            league_id=league_id, platform=platform, season=season
        )

        # Assert
        self.assertEqual(result, mock_response)
        mock_query_dynamodb.assert_called_once_with(
            pk=f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}",
            sk_prefix="DRAFT#",
        )
