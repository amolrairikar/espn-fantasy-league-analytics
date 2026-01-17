import unittest
from unittest.mock import patch, MagicMock

import botocore.exceptions
import pytest

from lambda_layer.common_utils.query_dynamodb import fetch_league_data


class TestFetchLeagueData(unittest.TestCase):
    """Unit tests for fetch_league_data function."""

    @patch("lambda_layer.common_utils.query_dynamodb.boto3.client")
    def test_fetch_league_data_with_multiple_items(self, mock_boto_client):
        """Test successful fetch with multiple items returned."""
        mock_response = {
            "Items": [
                {
                    "PK": {"S": "league#1"},
                    "SK": {"S": "player#1"},
                    "name": {"S": "Player One"},
                    "score": {"N": "100"},
                },
                {
                    "PK": {"S": "league#1"},
                    "SK": {"S": "player#2"},
                    "name": {"S": "Player Two"},
                    "score": {"N": "95"},
                },
            ]
        }
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb
        mock_dynamodb.query.return_value = mock_response

        result = fetch_league_data(
            table_name="test-table", pk="league#1", sk_prefix="player#"
        )

        assert len(result) == 2
        assert result[0]["name"] == "Player One"
        assert result[0]["score"] == 100
        assert result[1]["name"] == "Player Two"
        assert result[1]["score"] == 95

    @patch("lambda_layer.common_utils.query_dynamodb.boto3.client")
    def test_fetch_league_data_with_no_items(self, mock_boto_client):
        """Test fetch when no items are returned."""
        mock_response = {"Items": []}
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb
        mock_dynamodb.query.return_value = mock_response

        result = fetch_league_data(
            table_name="test-table", pk="league#1", sk_prefix="player#"
        )

        assert result == []

    @patch("lambda_layer.common_utils.query_dynamodb.boto3.client")
    def test_fetch_league_data_with_single_item(self, mock_boto_client):
        """Test successful fetch with single item."""
        mock_response = {
            "Items": [
                {
                    "PK": {"S": "league#1"},
                    "SK": {"S": "config#1"},
                    "leagueId": {"N": "123"},
                    "active": {"BOOL": True},
                },
            ]
        }
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb
        mock_dynamodb.query.return_value = mock_response

        result = fetch_league_data(
            table_name="test-table", pk="league#1", sk_prefix="config#"
        )

        assert len(result) == 1
        assert result[0]["leagueId"] == 123
        assert result[0]["active"] is True

    @patch("lambda_layer.common_utils.query_dynamodb.boto3.client")
    def test_fetch_league_data_correct_query_parameters(self, mock_boto_client):
        """Test that correct parameters are passed to DynamoDB query."""
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb
        mock_dynamodb.query.return_value = {"Items": []}

        fetch_league_data(
            table_name="test-table", pk="pk_value", sk_prefix="sk_prefix_value"
        )

        mock_dynamodb.query.assert_called_once_with(
            TableName="test-table",
            KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": "pk_value"},
                ":prefix": {"S": "sk_prefix_value"},
            },
        )

    @patch("lambda_layer.common_utils.query_dynamodb.boto3.client")
    def test_fetch_league_data_client_error_handling(self, mock_boto_client):
        """Test that ClientError is logged and re-raised."""
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb
        error = botocore.exceptions.ClientError(
            {"Error": {"Code": "ValidationException", "Message": "Invalid request"}},
            "Query",
        )
        mock_dynamodb.query.side_effect = error

        with pytest.raises(botocore.exceptions.ClientError):
            fetch_league_data(
                table_name="test-table", pk="pk_value", sk_prefix="sk_prefix_value"
            )
