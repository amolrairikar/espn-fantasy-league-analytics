from unittest.mock import patch, MagicMock

import botocore.exceptions
import pytest

# We need to import the base package prior to patching sys.modules to avoid an AttributeError
import lambda_layer.common_utils  # noqa: F401

with patch.dict("sys.modules", {"common_utils.logging_config": MagicMock()}):
    from lambda_layer.common_utils.batch_write_dynamodb import batch_write_to_dynamodb


def test_batch_write_successful_single_batch():
    """Test successful write with items less than 25."""
    items = [{"PutRequest": {"Item": {"id": {"S": f"item{i}"}}}} for i in range(10)]

    with patch(
        "lambda_layer.common_utils.batch_write_dynamodb.boto3.client"
    ) as mock_boto_client:
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb
        mock_dynamodb.batch_write_item.return_value = {"UnprocessedItems": {}}

        batch_write_to_dynamodb(items, "test-table")

        mock_dynamodb.batch_write_item.assert_called_once()
        call_args = mock_dynamodb.batch_write_item.call_args
        assert call_args[1]["RequestItems"]["test-table"] == items


def test_batch_write_successful_multiple_batches():
    """Test successful write with multiple batches (>25 items)."""
    items = [{"PutRequest": {"Item": {"id": {"S": f"item{i}"}}}} for i in range(60)]

    with patch(
        "lambda_layer.common_utils.batch_write_dynamodb.boto3.client"
    ) as mock_boto_client:
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb
        mock_dynamodb.batch_write_item.return_value = {"UnprocessedItems": {}}

        batch_write_to_dynamodb(items, "test-table")

        # Should be called 3 times (25 + 25 + 10)
        assert mock_dynamodb.batch_write_item.call_count == 3


def test_batch_write_with_empty_list():
    """Test batch write with empty list."""
    with patch(
        "lambda_layer.common_utils.batch_write_dynamodb.boto3.client"
    ) as mock_boto_client:
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        batch_write_to_dynamodb([], "test-table")

        mock_dynamodb.batch_write_item.assert_not_called()


def test_batch_write_with_retries_success():
    """Test successful write after retries on unprocessed items."""
    items = [{"PutRequest": {"Item": {"id": {"S": f"item{i}"}}}} for i in range(10)]

    with (
        patch(
            "lambda_layer.common_utils.batch_write_dynamodb.boto3.client"
        ) as mock_boto_client,
        patch("lambda_layer.common_utils.batch_write_dynamodb.time.sleep"),
    ):
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # First call returns unprocessed items, second succeeds
        unprocessed_response = {"UnprocessedItems": {"test-table": items[:5]}}
        success_response = {"UnprocessedItems": {}}
        mock_dynamodb.batch_write_item.side_effect = [
            unprocessed_response,
            success_response,
        ]

        batch_write_to_dynamodb(items, "test-table")

        assert mock_dynamodb.batch_write_item.call_count == 2


def test_batch_write_max_retries_exceeded():
    """Test RuntimeError raised when max retries exceeded."""
    items = [{"PutRequest": {"Item": {"id": {"S": f"item{i}"}}}} for i in range(10)]

    with (
        patch(
            "lambda_layer.common_utils.batch_write_dynamodb.boto3.client"
        ) as mock_boto_client,
        patch("lambda_layer.common_utils.batch_write_dynamodb.time.sleep"),
    ):
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        # Always return unprocessed items
        unprocessed_response = {"UnprocessedItems": {"test-table": items}}
        mock_dynamodb.batch_write_item.return_value = unprocessed_response

        with pytest.raises(RuntimeError, match="Max retries exceeded"):
            batch_write_to_dynamodb(items, "test-table")


def test_batch_write_client_error_handling():
    """Test that ClientError is logged and re-raised."""
    items = [{"PutRequest": {"Item": {"id": {"S": "item1"}}}}]

    with (
        patch(
            "lambda_layer.common_utils.batch_write_dynamodb.boto3.client"
        ) as mock_boto_client,
        patch("lambda_layer.common_utils.batch_write_dynamodb.logger") as mock_logger,
    ):
        mock_dynamodb = MagicMock()
        mock_boto_client.return_value = mock_dynamodb

        error = botocore.exceptions.ClientError(
            {"Error": {"Code": "ValidationException", "Message": "Invalid request"}},
            "BatchWriteItem",
        )
        mock_dynamodb.batch_write_item.side_effect = error

        with pytest.raises(botocore.exceptions.ClientError):
            batch_write_to_dynamodb(items, "test-table")

        mock_logger.exception.assert_called_once()
