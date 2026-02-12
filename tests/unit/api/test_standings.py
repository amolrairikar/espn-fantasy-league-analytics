import unittest
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from api.models import APIResponse
import api.routers.standings as standings_module
from api.routers.standings import (
    deserialize_items,
    get_season_standings_one_team,
    get_standings_for_season,
    get_head_to_head_standings,
    get_all_time_standings,
    get_playoff_standings,
    get_weekly_standings_single_team,
    get_standings,
)


class TestDeserializeItems(unittest.TestCase):
    """Tests for the deserialize_items function."""

    def test_deserialize_items_empty(self):
        """Tests deserializing an empty list."""
        # Act & Assert
        self.assertEqual(deserialize_items([]), [])

    def test_deserialize_items_single(self):
        """Tests deserializing a single DynamoDB item."""
        # Set up mock data
        dynamodb_item = {
            "PK": {"S": "LEAGUE#123#PLATFORM#ESPN"},
            "SK": {"S": "STANDINGS#SEASON#2023#TEAM#1"},
            "Points": {"N": "1500"},
            "Wins": {"N": "10"},
        }
        expected = {
            "Points": 1500,
            "Wins": 10,
        }

        # Act & Assert
        self.assertEqual(deserialize_items([dynamodb_item]), [expected])


class TestGetSeasonStandingsOneTeam(unittest.TestCase):
    """Tests for the get_season_standings_one_team function."""

    @patch("api.routers.standings.dynamodb_client")
    def test_get_season_standings_one_team(self, mock_dynamodb_client):
        """Tests getting season standings for one team."""
        # Set up mock response
        mock_response = {
            "Items": [
                {
                    "PK": {"S": "LEAGUE#123#PLATFORM#ESPN#STANDINGS#SEASON#TEAM#1"},
                    "SK": {"S": "SEASON#2023"},
                    "Points": {"N": "1500"},
                    "Wins": {"N": "10"},
                }
            ]
        }
        mock_dynamodb_client.query.return_value = mock_response

        expected_data = [
            {
                "Points": 1500,
                "Wins": 10,
            }
        ]

        # Act
        response = get_season_standings_one_team(
            league_id="123",
            platform="ESPN",
            team="1",
        )

        # Assert
        self.assertEqual(response.data, expected_data)
        self.assertEqual(response.detail, "Found standings for team 1")


class TestGetSeasonStandings(unittest.TestCase):
    """Tests for the get_standings_for_season function."""

    @patch("api.routers.standings.dynamodb_client")
    def test_get_season_standings(self, mock_dynamodb_client):
        """Tests getting season standings for one team."""
        # Set up mock response
        mock_response = {
            "Items": [
                {
                    "PK": {"S": "LEAGUE#123#PLATFORM#ESPN#STANDINGS#SEASON#TEAM#1"},
                    "SK": {"S": "SEASON#2023"},
                    "Points": {"N": "1500"},
                    "Wins": {"N": "10"},
                },
                {
                    "PK": {"S": "LEAGUE#123#PLATFORM#ESPN#SEASON#2023"},
                    "SK": {"S": "STANDINGS#SEASON#"},
                    "Points": {"N": "1400"},
                    "Wins": {"N": "9"},
                },
            ]
        }
        mock_dynamodb_client.query.return_value = mock_response

        expected_data = [
            {
                "Points": 1500,
                "Wins": 10,
            },
            {
                "Points": 1400,
                "Wins": 9,
            },
        ]

        # Act
        response = get_standings_for_season(
            league_id="123",
            platform="ESPN",
            season="2023",
        )

        # Assert
        self.assertEqual(response.data, expected_data)
        self.assertEqual(response.detail, "Found standings for 2023 season")


class TestGetHeadToHeadStandings(unittest.TestCase):
    """Tests for the get_head_to_head_standings function."""

    @patch("api.routers.standings.dynamodb_client")
    def test_get_head_to_head_standings(self, mock_dynamodb_client):
        """Tests getting head-to-head standings."""
        # Set up mock response
        mock_response = {
            "Items": [
                {
                    "PK": {"S": "LEAGUE#123#PLATFORM#ESPN#STANDINGS#SEASON#TEAM#1"},
                    "SK": {"S": "STANDINGS#H2H"},
                    "Points": {"N": "1500"},
                    "Wins": {"N": "10"},
                }
            ]
        }
        mock_dynamodb_client.query.return_value = mock_response

        expected_data = [
            {
                "Points": 1500,
                "Wins": 10,
            }
        ]

        # Act
        response = get_head_to_head_standings(
            league_id="123",
            platform="ESPN",
        )

        # Assert
        self.assertEqual(response.data, expected_data)
        self.assertEqual(response.detail, "Found head to head standings")


class TestGetAllTimeStandings(unittest.TestCase):
    """Tests for the get_all_time_standings function."""

    @patch("api.routers.standings.dynamodb_client")
    def test_get_all_time_standings(self, mock_dynamodb_client):
        """Tests getting all-time standings."""
        # Set up mock response
        mock_response = {
            "Items": [
                {
                    "PK": {"S": "LEAGUE#123#PLATFORM#ESPN#STANDINGS#SEASON#TEAM#1"},
                    "SK": {"S": "STANDINGS#ALL-TIME"},
                    "Points": {"N": "1500"},
                    "Wins": {"N": "10"},
                }
            ]
        }
        mock_dynamodb_client.query.return_value = mock_response

        expected_data = [
            {
                "Points": 1500,
                "Wins": 10,
            }
        ]

        # Act
        response = get_all_time_standings(
            league_id="123",
            platform="ESPN",
        )

        # Assert
        self.assertEqual(response.data, expected_data)
        self.assertEqual(response.detail, "Found all-time standings")


class TestGetPlayoffStandings(unittest.TestCase):
    """Tests for the get_playoff_standings function."""

    @patch("api.routers.standings.dynamodb_client")
    def test_get_playoff_standings(self, mock_dynamodb_client):
        """Tests getting playoff standings."""
        # Set up mock response
        mock_response = {
            "Items": [
                {
                    "PK": {"S": "LEAGUE#123#PLATFORM#ESPN#STANDINGS#SEASON#TEAM#1"},
                    "SK": {"S": "STANDINGS#ALL-TIME-PLAYOFFS#"},
                    "Points": {"N": "1500"},
                    "Wins": {"N": "10"},
                }
            ]
        }
        mock_dynamodb_client.query.return_value = mock_response

        expected_data = [
            {
                "Points": 1500,
                "Wins": 10,
            }
        ]

        # Act
        response = get_playoff_standings(
            league_id="123",
            platform="ESPN",
        )

        # Assert
        self.assertEqual(response.data, expected_data)
        self.assertEqual(response.detail, "Found playoff standings")


class TestGetWeeklyStandingsSingleTeam(unittest.TestCase):
    """Tests for the get_weekly_standings_single_team function."""

    @patch("api.routers.standings.dynamodb_client")
    def test_get_weekly_standings_single_team(self, mock_dynamodb_client):
        """Tests getting weekly standings for a single team."""
        # Set up mock response
        mock_response = {
            "Items": [
                {
                    "PK": {"S": "LEAGUE#123#PLATFORM#ESPN#STANDINGS#SEASON#TEAM#1"},
                    "SK": {"S": "STANDINGS#WEEKLY#1"},
                    "Points": {"N": "1500"},
                    "Wins": {"N": "10"},
                }
            ]
        }
        mock_dynamodb_client.query.return_value = mock_response

        expected_data = [
            {
                "Points": 1500,
                "Wins": 10,
            }
        ]

        # Act
        response = get_weekly_standings_single_team(
            league_id="123",
            platform="ESPN",
            season="2023",
            team="1",
            week="5",
        )

        # Assert
        self.assertEqual(response.data, expected_data)
        self.assertEqual(response.detail, "Found weekly standings")


class TestGetStandings(unittest.TestCase):
    """Tests for the get_standings function."""

    @patch("api.routers.standings.get_playoff_standings")
    def test_get_standings(self, mock_get_playoff_standings):
        """Tests successful call to get_standings."""
        # Set up mock response
        mock_get_playoff_standings.return_value = APIResponse(
            detail="Found playoff standings",
            data=[
                {
                    "Points": 1500,
                    "Wins": 10,
                }
            ],
        )

        # Ensure the QUERY_HANDLERS mapping uses the mocked handler
        standings_module.QUERY_HANDLERS[("playoffs", False, False, False)] = (
            mock_get_playoff_standings
        )

        # Act
        response = get_standings(
            league_id="123",
            platform="ESPN",
            standings_type="playoffs",
            season=None,
            team=None,
            week=None,
        )

        # Assert
        self.assertEqual(response.detail, "Found playoff standings")
        self.assertEqual(
            response.data,
            [
                {
                    "Points": 1500,
                    "Wins": 10,
                }
            ],
        )
        mock_get_playoff_standings.assert_called_once_with(
            league_id="123",
            platform="ESPN",
            standings_type="playoffs",
            season=None,
            team=None,
            week=None,
        )

    def test_get_standings_no_handler(self):
        """Test get_standings with no matching handler."""
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            get_standings(
                league_id="12345",
                platform="espn",
                standings_type="playoffs",
                season="test",
                team="test",
                week=1,
            )

        self.assertEqual(exc_info.value.status_code, 400)
        self.assertEqual(
            exc_info.value.detail,
            "Invalid combination of query parameters: standings_type=playoffs, season=test, team=test, week=1",
        )
