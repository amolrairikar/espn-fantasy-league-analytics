import unittest
from unittest.mock import MagicMock, patch

import botocore.exceptions
import requests
from fastapi import HTTPException

from api.models import APIResponse, LeagueMetadata
from api.routers.league_metadata import (
    validate_espn_credentials,
    validate_league_info,
    get_league_metadata,
    post_league_metadata,
    update_league_metadata,
)


class TestValidateEspnCredentials(unittest.TestCase):
    """Tests for the validate_espn_credentials function."""

    @patch("api.routers.league_metadata.requests.get")
    def test_validate_espn_credentials_success(self, mock_get):
        """Test successful ESPN credential validation."""
        # Set up mock data
        mock_get.return_value = MagicMock()
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status.return_value = None

        # Act & Assert (no assertions since no error occurs)
        validate_espn_credentials(
            league_id="12345",
            season="2025",
            swid_cookie="swid_cookie",
            espn_s2_cookie="espn_s2_cookie",
        )

    @patch("api.routers.league_metadata.requests.get")
    def test_validate_espn_credentials_failure(self, mock_get):
        """Test failed ESPN credential validation."""
        # Mock the requests.get to return a 404 status code
        mock_get.return_value = MagicMock()
        mock_get.return_value.status_code = 404
        http_error = requests.HTTPError(
            "League ID not found", response=mock_get.return_value
        )
        mock_get.return_value.raise_for_status.side_effect = http_error

        # Act & Assert
        with self.assertRaises(requests.HTTPError):
            validate_espn_credentials(
                league_id="12345",
                season="2025",
                swid_cookie="swid_cookie",
                espn_s2_cookie="espn_s2_cookie",
            )


class TestValidateLeagueInfo(unittest.TestCase):
    """Tests for the validate_league_info function."""

    @patch("api.routers.league_metadata.validate_espn_credentials")
    def test_validate_league_info_valid(self, mock_validate_espn_credentials):
        """Test validate_league_info with valid inputs."""
        # Set up mock data
        expected_response = APIResponse(
            detail="League information validated successfully."
        )
        mock_validate_espn_credentials.return_value = None

        # Act
        result = validate_league_info(
            league_id="12345",
            platform="ESPN",
            season="2025",
            swid_cookie="swid_cookie",
            espn_s2_cookie="espn_s2_cookie",
        )

        # Assert
        self.assertEqual(result, expected_response)

    @patch("api.routers.league_metadata.validate_espn_credentials")
    def test_validate_league_info_invalid_league_id(
        self, mock_validate_espn_credentials
    ):
        """Test validate_league_info with invalid league ID."""
        # Mock validate_espn_credentials to return a 404 status code
        mock_response = MagicMock()
        mock_response.status_code = 404
        error = requests.RequestException("League ID not found")
        error.response = mock_response
        mock_validate_espn_credentials.side_effect = error

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            validate_league_info(
                league_id="12345",
                platform="ESPN",
                season="2025",
                swid_cookie="swid_cookie",
                espn_s2_cookie="espn_s2_cookie",
            )

        self.assertEqual(context.exception.status_code, 404)
        self.assertIn("League ID not found", str(context.exception.detail))

    @patch("api.routers.league_metadata.validate_espn_credentials")
    def test_validate_league_info_unexpected_error(
        self, mock_validate_espn_credentials
    ):
        """Test validate_league_info handling of unexpected errors."""
        # Mock validate_espn_credentials to return an unexpected status code
        mock_response = MagicMock()
        mock_response.status_code = None
        error = requests.RequestException("Unexpected error")
        error.response = mock_response
        mock_validate_espn_credentials.side_effect = error

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            validate_league_info(
                league_id="invalid",
                platform="ESPN",
                season="2025",
                swid_cookie="invalid",
                espn_s2_cookie="invalid",
            )

        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("Unexpected error", str(context.exception))

    def test_validate_league_info_invalid_platform(self):
        """Test validate_league_info with unsupported platform."""
        # Act & Assert
        with self.assertRaises(Exception) as context:
            validate_league_info(
                league_id="12345",
                platform="YAHOO",
                season="2025",
                swid_cookie="swid_cookie",
                espn_s2_cookie="espn_s2_cookie",
            )

        self.assertIn(
            "Platforms besides ESPN not currently supported.", str(context.exception)
        )


class TestGetLeagueMetadata(unittest.TestCase):
    @patch("api.routers.league_metadata.dynamodb_client")
    def test_get_league_metadata_success(self, mock_dynamodb_client):
        # Mock the response from DynamoDB
        mock_dynamodb_client.get_item.return_value = {
            "Item": {
                "league_id": {"S": "12345"},
                "platform": {"S": "ESPN"},
                "espn_s2_cookie": {"S": "mock_espn_s2"},
                "swid_cookie": {"S": "mock_swid"},
                "seasons": {"SS": ["2020", "2021"]},
            }
        }

        # Act
        response = get_league_metadata(league_id="12345", platform="ESPN")
        if not response.data:
            self.fail("Expected data in response, got None")

        # Assert
        self.assertEqual(response.data["league_id"], "12345")
        self.assertEqual(response.data["platform"], "ESPN")
        self.assertEqual(response.data["espn_s2_cookie"], "mock_espn_s2")
        self.assertEqual(response.data["swid_cookie"], "mock_swid")
        self.assertEqual(response.data["seasons"], ["2020", "2021"])

    @patch("api.routers.league_metadata.dynamodb_client")
    def test_get_league_metadata_not_found(self, mock_dynamodb_client):
        # Set up mock data
        mock_dynamodb_client.get_item.return_value = {}

        # Act & Assert
        with self.assertRaises(Exception) as context:
            get_league_metadata(league_id="99999", platform="ESPN")

        self.assertIn(
            "League with ID 99999 not found in database.", str(context.exception)
        )

    @patch("api.routers.league_metadata.dynamodb_client")
    def test_get_league_metadata_dynamodb_error(self, mock_dynamodb_client):
        # Mock DynamoDB to raise an exception
        mock_dynamodb_client.get_item.side_effect = botocore.exceptions.ClientError(
            error_response={
                "Error": {"Code": "InternalFailure", "Message": "DynamoDB error"}
            },
            operation_name="GetItem",
        )

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            get_league_metadata(league_id="12345", platform="ESPN")

        self.assertIn("Internal server error", str(context.exception))


class TestPostLeagueMetadata(unittest.TestCase):
    """Tests for the post_league_metadata function."""

    @patch("api.routers.league_metadata.dynamodb_client")
    def test_post_league_metadata_success(self, mock_dynamodb_client):
        """Test successful posting of league metadata."""
        # Set up mock data
        mock_dynamodb_client.put_item.return_value = {}

        # Act
        response = post_league_metadata(
            data=MagicMock(
                league_id="12345",
                platform="ESPN",
                espn_s2="mock_espn_s2",
                swid="mock_swid",
                seasons=["2020", "2021"],
            )
        )

        # Assert
        self.assertIn("League with ID 12345 added to database.", response.detail)

    @patch("api.routers.league_metadata.dynamodb_client")
    def test_post_league_metadata_already_exists(self, mock_dynamodb_client):
        """Test error handling for post_league_metadata if league exists."""
        # Mock DynamoDB to raise an exception
        mock_dynamodb_client.put_item.side_effect = botocore.exceptions.ClientError(
            error_response={
                "Error": {
                    "Code": "ConditionalCheckFailedException",
                    "Message": "League with ID 12345 already exists",
                },
            },
            operation_name="PutItem",
        )

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            post_league_metadata(
                data=MagicMock(
                    league_id="12345",
                    platform="ESPN",
                    espn_s2="mock_espn_s2",
                    swid="mock_swid",
                    seasons=["2020", "2021"],
                )
            )

        self.assertIn("League with ID 12345 already exists", str(context.exception))

    @patch("api.routers.league_metadata.dynamodb_client")
    def test_post_league_metadata_dynamodb_error(self, mock_dynamodb_client):
        """Test handling of DynamoDB errors during posting."""
        # Mock DynamoDB to raise an exception
        mock_dynamodb_client.put_item.side_effect = botocore.exceptions.ClientError(
            error_response={
                "Error": {"Code": "InternalFailure", "Message": "DynamoDB error"}
            },
            operation_name="PutItem",
        )

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            post_league_metadata(
                data=MagicMock(
                    league_id="12345",
                    platform="ESPN",
                    espn_s2="mock_espn_s2",
                    swid="mock_swid",
                    seasons=["2020", "2021"],
                )
            )

        self.assertIn("Internal server error", str(context.exception))


class TestUpdateLeagueMetadata(unittest.TestCase):
    """Tests for the update_league_metadata function."""

    @patch("api.routers.league_metadata.dynamodb_client")
    def test_update_league_metadata_success(self, mock_dynamodb_client):
        """Test successful updating of league metadata."""
        # Set up mock data
        mock_dynamodb_client.update_item.return_value = {}

        # Act
        response = update_league_metadata(
            data=LeagueMetadata(
                league_id="12345",
                platform="ESPN",
                espn_s2="espn_s2",
                swid="swid",
                seasons=["2020", "2021", "2022"],
                onboarded_date="2024-01-01",
                onboarding_status=True,
            ),
            league_id="12345",
        )

        # Assert
        self.assertEqual(
            response,
            APIResponse(detail="League with ID 12345 updated in database.", data=None),
        )

    @patch("api.routers.league_metadata.dynamodb_client")
    def test_update_league_metadata_dynamodb_error(self, mock_dynamodb_client):
        """Test handling of DynamoDB errors during updating."""
        # Mock DynamoDB to raise an exception
        mock_dynamodb_client.update_item.side_effect = botocore.exceptions.ClientError(
            error_response={
                "Error": {"Code": "InternalFailure", "Message": "DynamoDB error"}
            },
            operation_name="UpdateItem",
        )

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            update_league_metadata(
                data=LeagueMetadata(
                    league_id="12345",
                    platform="ESPN",
                    espn_s2="espn_s2",
                    swid="swid",
                    seasons=["2020", "2021", "2022"],
                    onboarded_date="2024-01-01",
                    onboarding_status=True,
                ),
                league_id="12345",
            )

        self.assertIn("Internal server error", str(context.exception))
