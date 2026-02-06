import unittest
from unittest.mock import patch

from api.models import APIResponse
from api.routers.owners import (
    get_owners,
)


class TestGetOwners(unittest.TestCase):
    """Tests for get_owners endpoint."""

    @patch("api.routers.owners.query_dynamodb")
    def test_get_owners(self, mock_query_dynamodb):
        """Test the get_owners endpoint."""
        # Set up mock data
        mock_response = APIResponse(
            detail="Found all owners for the league",
            data=[{"Owner": "Test Owner 1"}, {"Owner": "Test Owner 2"}],
        )
        mock_query_dynamodb.return_value = mock_response
        league_id = "123"
        platform = "ESPN"

        # Act
        result = get_owners(
            league_id=league_id,
            platform=platform,
        )

        # Assert
        self.assertEqual(result, mock_response)
        mock_query_dynamodb.assert_called_once_with(
            pk=f"LEAGUE#{league_id}#PLATFORM#{platform}",
            sk_prefix="OWNERS",
        )
