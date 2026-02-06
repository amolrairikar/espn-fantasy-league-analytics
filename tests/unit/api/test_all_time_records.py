import unittest
from unittest.mock import patch

from api.models import APIResponse
from api.routers.all_time_records import (
    get_alltime_records,
)


class TestGetAlltimeRecords(unittest.TestCase):
    """Tests for get_alltime_records endpoint."""

    @patch("api.routers.all_time_records.query_dynamodb")
    def test_get_alltime_records(self, mock_query_dynamodb):
        """Test the get_alltime_records endpoint."""
        # Set up mock data
        mock_response = APIResponse(
            detail="Found all-time records for all_time_championships",
            data=[{"Record": "Test Record"}],
        )
        mock_query_dynamodb.return_value = mock_response
        league_id = "123"
        platform = "ESPN"
        record_type = "all_time_championships"

        # Act
        result = get_alltime_records(
            league_id=league_id,
            platform=platform,
            record_type=record_type,
        )

        # Assert
        self.assertEqual(result, mock_response)
        mock_query_dynamodb.assert_called_once_with(
            pk=f"LEAGUE#{league_id}#PLATFORM#{platform}",
            sk_prefix="HALL_OF_FAME#CHAMPIONSHIPS#",
        )
