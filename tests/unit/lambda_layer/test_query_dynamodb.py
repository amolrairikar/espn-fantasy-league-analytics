from unittest.mock import patch, MagicMock

import botocore.exceptions
import pytest

# We need to import the base package prior to patching sys.modules to avoid an AttributeError
import lambda_layer.common_utils  # noqa: F401

with patch.dict("sys.modules", {"common_utils.logging_config": MagicMock()}):
    from lambda_layer.common_utils.query_dynamodb import fetch_league_data


def test_fetch_league_data_with_multiple_items():
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

    with patch(
        "lambda_layer.common_utils.query_dynamodb.boto3.client"
    ) as mock_boto_client:
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


def test_fetch_league_data_with_no_items():
    """Test fetch when no items are returned."""
    mock_response = {"Items": []}

    with patch(
        "lambda_layer.common_utils.query_dynamodb.boto3.client"
    ) as mock_boto_client:
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb
        mock_dynamodb.query.return_value = mock_response

        result = fetch_league_data(
            table_name="test-table", pk="league#1", sk_prefix="player#"
        )

        assert result == []


def test_fetch_league_data_with_single_item():
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

    with patch(
        "lambda_layer.common_utils.query_dynamodb.boto3.client"
    ) as mock_boto_client:
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb
        mock_dynamodb.query.return_value = mock_response

        result = fetch_league_data(
            table_name="test-table", pk="league#1", sk_prefix="config#"
        )

        assert len(result) == 1
        assert result[0]["leagueId"] == 123
        assert result[0]["active"] is True


def test_fetch_league_data_correct_query_parameters():
    """Test that correct parameters are passed to DynamoDB query."""
    with patch(
        "lambda_layer.common_utils.query_dynamodb.boto3.client"
    ) as mock_boto_client:
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


def test_fetch_league_data_client_error_handling():
    """Test that ClientError is logged and re-raised."""
    with (
        patch(
            "lambda_layer.common_utils.query_dynamodb.boto3.client"
        ) as mock_boto_client,
        patch("lambda_layer.common_utils.query_dynamodb.logger") as mock_logger,
    ):
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

        mock_logger.exception.assert_called_once()
        call_args = mock_logger.exception.call_args[0]
        assert "pk_value" in call_args
        assert "sk_prefix_value" in call_args
