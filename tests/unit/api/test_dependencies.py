import json
import logging
import unittest
from decimal import Decimal
from unittest.mock import patch

import botocore.exceptions
import pytest
from fastapi import HTTPException

from api.dependencies import (
    JsonFormatter,
    build_api_request_headers,
    filter_dynamodb_response,
    query_dynamodb,
    query_with_handling,
)


class TestJsonFormatter(unittest.TestCase):
    """Tests for JsonFormatter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.formatter = JsonFormatter()

    def test_format_returns_valid_json(self):
        """
        Test that format() returns a valid JSON string and
        contains all required fields.
        """
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_func",
        )
        result = self.formatter.format(record)
        parsed = json.loads(result)
        self.assertIsInstance(parsed, dict)
        self.assertIn("timestamp", parsed)
        self.assertIn("level", parsed)
        self.assertIn("message", parsed)
        self.assertIn("function", parsed)

    def test_format_field_value_accuracy(self):
        """Test that JSON fields contains correct values."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_func",
        )
        result = self.formatter.format(record)
        parsed = json.loads(result)
        self.assertEqual(parsed["message"], "Test message")
        self.assertEqual(parsed["level"], "INFO")
        self.assertEqual(parsed["function"], "test_func")
        self.assertIsInstance(parsed["timestamp"], int)
        self.assertGreater(parsed["timestamp"], 0)

    def test_format_with_formatted_message(self):
        """Test that getMessage() is used for message formatting."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Hello %s",
            args=("World",),
            exc_info=None,
            func="test_func",
        )
        result = self.formatter.format(record)
        parsed = json.loads(result)
        self.assertEqual(parsed["message"], "Hello World")


class TestBuildApiRequestHeaders(unittest.TestCase):
    """Tests for build_api_request_headers function."""

    def test_build_headers(self):
        """Test build_headers method."""
        cookies: dict[str, str | None] = {
            "swid": "some-swid-value",
            "espn_s2": "some-espn-s2-value",
        }
        expected_headers = {
            "Cookie": "espn_s2=some-espn-s2-value; SWID=some-swid-value;",
        }
        headers = build_api_request_headers(cookies=cookies)
        self.assertEqual(headers, expected_headers)

    def test_build_headers_with_missing_cookies(self):
        """Test build_headers method with missing cookies."""
        cookies: dict[str, str | None] = {
            "swid": None,
            "espn_s2": "some-espn-s2-value",
        }
        with pytest.raises(HTTPException) as exc_info:
            build_api_request_headers(cookies=cookies)
        self.assertEqual(exc_info.value.status_code, 400)
        self.assertIn(
            "Missing required espn_s2 and swid cookies", str(exc_info.value.detail)
        )


class TestFilterDynamodbResponse(unittest.TestCase):
    """Tests for filter_dynamodb_response function."""

    def test_filter_dynamodb_response_with_items(self):
        """Test filtering response with items."""
        # Set up test data
        mock_response = {
            "Items": [
                {
                    "PK": {"S": "LEAGUE#123#PLATFORM#ESPN"},
                    "SK": {"S": "HALL_OF_FAME#CHAMPIONSHIPS#1"},
                    "Value": {"N": "5"},
                },
                {
                    "PK": {"S": "LEAGUE#123#PLATFORM#ESPN"},
                    "SK": {"S": "HALL_OF_FAME#TOP10TEAMSCORES#1"},
                    "Value": {"N": "300"},
                },
            ]
        }
        expected_output = [
            {"Value": Decimal("5")},
            {"Value": Decimal("300")},
        ]

        # Act
        result = filter_dynamodb_response(response=mock_response)

        # Assert
        self.assertEqual(result, expected_output)


class TestQueryDynamodb(unittest.TestCase):
    """Tests for query_dynamodb function."""

    @patch("api.dependencies.dynamodb_client")
    def test_query_dynamodb_successful(self, mock_dynamodb_client):
        """Test successful DynamoDB query."""
        # Set up mock data
        mock_response = {
            "Items": [
                {
                    "PK": {"S": "LEAGUE#123#PLATFORM#ESPN"},
                    "SK": {"S": "HALL_OF_FAME#CHAMPIONSHIPS#1"},
                    "Value": {"N": "5"},
                }
            ]
        }
        mock_dynamodb_client.query.return_value = mock_response

        # Act
        result = query_dynamodb(
            pk="LEAGUE#123#PLATFORM#ESPN",
            sk_prefix="HALL_OF_FAME#CHAMPIONSHIPS#",
        )
        if result.data is None:
            self.fail("result.data is None, expected a list of items")

        # Assert
        self.assertEqual(
            result.detail,
            "Found records for pk LEAGUE#123#PLATFORM#ESPN and sk_prefix HALL_OF_FAME#CHAMPIONSHIPS#",
        )
        self.assertEqual(len(result.data), 1)
        self.assertEqual(result.data[0]["Value"], Decimal("5"))

    @patch("api.dependencies.dynamodb_client")
    def test_query_dynamodb_no_items(self, mock_dynamodb_client):
        """Test DynamoDB query with no items found."""
        # Set up mock data
        mock_response = {"Items": []}
        mock_dynamodb_client.query.return_value = mock_response

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            query_dynamodb(
                pk="LEAGUE#999#PLATFORM#ESPN",
                sk_prefix="HALL_OF_FAME#CHAMPIONSHIPS#",
            )

        self.assertEqual(context.exception.status_code, 404)
        self.assertIn(
            "No entries found for pk LEAGUE#999#PLATFORM#ESPN and sk_prefix HALL_OF_FAME#CHAMPIONSHIPS#",
            context.exception.detail,
        )

    @patch("api.dependencies.dynamodb_client")
    def test_query_dynamodb_client_error(self, mock_dynamodb_client):
        """Test DynamoDB query that raises a ClientError."""
        # Set up mock data
        mock_dynamodb_client.query.side_effect = botocore.exceptions.ClientError(
            error_response={
                "Error": {"Code": "500", "Message": "Internal Server Error"}
            },
            operation_name="Query",
        )

        # Act & Assert
        with self.assertRaises(HTTPException):
            query_dynamodb(
                pk="LEAGUE#123#PLATFORM#ESPN",
                sk_prefix="HALL_OF_FAME#CHAMPIONSHIPS#",
            )


class TestQueryWithHandling(unittest.TestCase):
    """Tests for query_with_handling function."""

    @patch("api.dependencies.dynamodb_client")
    def test_query_with_handling_success(self, mock_dynamodb_client):
        """Test successful query_with_handling."""
        # Set up mock data
        mock_response = {
            "Items": [
                {
                    "PK": {"S": "LEAGUE#123#PLATFORM#ESPN"},
                    "SK": {"S": "HALL_OF_FAME#CHAMPIONSHIPS#1"},
                    "Value": {"N": "5"},
                }
            ]
        }
        mock_dynamodb_client.query.return_value = mock_response

        # Define a sample function to be called
        def sample_query_function(pk: str, sk_prefix: str):
            return mock_dynamodb_client.query(
                TableName="TestTable",
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": pk},
                    ":sk_prefix": {"S": sk_prefix},
                },
            )

        # Act
        result = query_with_handling(
            fn=sample_query_function,
            pk="LEAGUE#123#PLATFORM#ESPN",
            sk_prefix="HALL_OF_FAME#CHAMPIONSHIPS#",
        )

        # Assert
        self.assertEqual(result, mock_response)

    @patch("api.dependencies.dynamodb_client")
    def test_query_with_handling_client_error(self, mock_dynamodb_client):
        """Test query_with_handling that raises a ClientError."""
        # Set up mock data
        mock_dynamodb_client.query.side_effect = botocore.exceptions.ClientError(
            error_response={
                "Error": {"Code": "500", "Message": "Internal Server Error"}
            },
            operation_name="Query",
        )

        # Define a sample function to be called
        def sample_query_function(pk: str, sk_prefix: str):
            return mock_dynamodb_client.query(
                TableName="TestTable",
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": pk},
                    ":sk_prefix": {"S": sk_prefix},
                },
            )

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            query_with_handling(
                fn=sample_query_function,
                pk="LEAGUE#123#PLATFORM#ESPN",
                sk_prefix="HALL_OF_FAME#CHAMPIONSHIPS#",
            )

        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("Internal server error", context.exception.detail)
