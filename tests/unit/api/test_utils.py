import unittest
from unittest.mock import MagicMock, patch

import botocore.exceptions
from fastapi import HTTPException

from api.routers.utils import delete_league_items


class TestDeleteLeagueItems(unittest.TestCase):
    """Tests for the delete_league_items function."""

    def test_delete_league_items_success(self):
        """Test that items are deleted successfully."""
        mock_table = MagicMock()
        mock_table.query.return_value = {
            "Items": [{"PK": "item1", "SK": "sk1"}, {"PK": "item2", "SK": "sk2"}],
            "LastEvaluatedKey": None,
        }

        with patch("api.routers.utils.table", mock_table):
            delete_league_items(league_id="test_league")

        self.assertEqual(mock_table.query.call_count, 1)
        self.assertEqual(mock_table.batch_writer.call_count, 1)
        self.assertEqual(
            mock_table.batch_writer().__enter__().delete_item.call_count, 2
        )

    def test_delete_league_items_failure(self):
        """Test that an exception is raised if the query fails."""
        mock_table = MagicMock()
        mock_table.query.side_effect = botocore.exceptions.ClientError(
            error_response={
                "Error": {"Code": "500", "Message": "Internal Server Error"}
            },
            operation_name="Query",
        )

        with patch("api.routers.utils.table", mock_table):
            with self.assertRaises(HTTPException) as context:
                delete_league_items(league_id="test_league")

        self.assertIn("Internal Server Error", str(context.exception))
