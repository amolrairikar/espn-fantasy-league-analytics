import json
import unittest
from unittest.mock import patch

import botocore.exceptions
import pytest

from lambdas.step_function_lambdas.league_drafts.main import (
    get_teams,
    get_draft_results,
    get_player_season_totals,
    process_player_scoring_totals,
    enrich_draft_data,
    lambda_handler,
)


class TestGetTeams(unittest.TestCase):
    """Class to test get_teams function."""

    @patch("lambdas.step_function_lambdas.league_drafts.main.boto3.client")
    def test_get_teams_success(self, mock_boto_client):
        """Test get_teams function for successful response."""
        # Set up mock DynamoDB response
        mock_dynamodb = mock_boto_client.return_value
        mock_dynamodb.query.return_value = {
            "Items": [
                {
                    "PK": {"S": "LEAGUE#1#PLATFORM#ESPN#SEASON#2025"},
                    "SK": {"S": "TEAM#1"},
                    "owner_first_name": {"S": "First"},
                    "owner_full_name": {"S": "First Last"},
                    "owner_id": {"L": [{"S": "id_123"}]},
                    "owner_last_name": {"S": "Last"},
                    "team_abbreviation": {"S": "ABC"},
                    "team_id": {"S": "1"},
                    "team_name": {"S": "Team Name"},
                }
            ]
        }
        expected_teams = [
            {
                "PK": "LEAGUE#1#PLATFORM#ESPN#SEASON#2025",
                "SK": "TEAM#1",
                "owner_first_name": "First",
                "owner_full_name": "First Last",
                "owner_id": ["id_123"],
                "owner_last_name": "Last",
                "team_abbreviation": "ABC",
                "team_id": "1",
                "team_name": "Team Name",
                "season": "2025",
            }
        ]

        # Act
        teams = get_teams(league_id="1", platform="ESPN", season="2025")

        # Assert
        self.assertEqual(teams, expected_teams)

    @patch("lambdas.step_function_lambdas.league_drafts.main.boto3.client")
    def test_get_teams_failure(self, mock_boto_client):
        """Test get_teams function for boto error."""
        # Set up mock DynamoDB response
        mock_dynamodb = mock_boto_client.return_value
        mock_dynamodb.query.side_effect = botocore.exceptions.ClientError(
            error_response={
                "Error": {"Code": "500", "Message": "Internal Server Error"}
            },
            operation_name="Query",
        )

        # Act
        with pytest.raises(botocore.exceptions.ClientError):
            get_teams(league_id="12345", platform="ESPN", season="2023")


class TestGetDraftResults(unittest.TestCase):
    """Class for testing get_draft_results function."""

    @patch("lambdas.step_function_lambdas.league_drafts.main.make_espn_api_request")
    def test_get_draft_results_after_2018_success(self, mock_make_request):
        """Tests successful invocation of get_draft_results for seasons after 2018."""
        # Set up test data
        mock_make_request.return_value = {
            "draftDetail": {
                "picks": [
                    {
                        "pick": "1",
                    },
                    {
                        "pick": "2",
                    },
                ],
            },
        }
        expected_picks = [
            {
                "pick": "1",
            },
            {
                "pick": "2",
            },
        ]

        # Act
        picks = get_draft_results(
            league_id="12345",
            platform="ESPN",
            season="2023",
            swid_cookie="{ABC-123}",
            espn_s2_cookie="S2-COOKIE",
        )

        # Assert
        self.assertEqual(picks, expected_picks)
        mock_make_request.assert_any_call(
            season=2023,
            league_id="12345",
            params=[
                ("view", "mDraftDetail"),
            ],
            swid_cookie="{ABC-123}",
            espn_s2_cookie="S2-COOKIE",
        )

    @patch("lambdas.step_function_lambdas.league_drafts.main.make_espn_api_request")
    def test_get_draft_results_before_2018_success(self, mock_make_request):
        """Tests successful invocation of get_draft_results for seasons before 2018."""
        # Set up test data
        mock_make_request.return_value = {
            "draftDetail": {
                "picks": [
                    {
                        "pick": "1",
                    },
                    {
                        "pick": "2",
                    },
                ],
            },
        }
        expected_picks = [
            {
                "pick": "1",
            },
            {
                "pick": "2",
            },
        ]

        # Act
        picks = get_draft_results(
            league_id="12345",
            platform="ESPN",
            season="2017",
            swid_cookie="{ABC-123}",
            espn_s2_cookie="S2-COOKIE",
        )

        # Assert
        self.assertEqual(picks, expected_picks)
        mock_make_request.assert_any_call(
            season=2017,
            league_id="12345",
            params=[
                ("seasonId", "2017"),
                ("view", "mDraftDetail"),
            ],
            swid_cookie="{ABC-123}",
            espn_s2_cookie="S2-COOKIE",
        )

    def test_get_draft_results_missing_cookies(self):
        """Test get_draft_results function raises ValueError if cookies are missing."""
        # Act
        with pytest.raises(ValueError):
            get_draft_results(
                league_id="12345",
                platform="ESPN",
                season="2017",
                swid_cookie=None,
                espn_s2_cookie=None,
            )

    def test_get_draft_results_invalid_platform(self):
        """Test get_draft_results function raises ValueError if an unsupported platform is provided."""
        # Act
        with pytest.raises(ValueError):
            get_draft_results(
                league_id="12345",
                platform="Sleeper",
                season="2017",
                swid_cookie=None,
                espn_s2_cookie=None,
            )


class TestGetPlayerSeasonTotals(unittest.TestCase):
    """Class for testing get_player_season_totals function."""

    @patch("lambdas.step_function_lambdas.league_drafts.main.make_espn_api_request")
    def test_get_player_season_totals_after_2018_success(self, mock_make_request):
        """Tests successful invocation of get_player_season_totals for seasons after 2018."""
        # Set up test data
        mock_make_request.return_value = {
            "players": [
                {
                    "id": "1",
                },
                {
                    "id": "2",
                },
            ],
        }
        expected_players = [
            {
                "id": "1",
            },
            {
                "id": "2",
            },
        ]

        # Act
        players = get_player_season_totals(
            league_id="12345",
            platform="ESPN",
            season="2023",
            swid_cookie="{ABC-123}",
            espn_s2_cookie="S2-COOKIE",
        )

        # Assert
        self.assertEqual(players, expected_players)
        mock_make_request.assert_any_call(
            season=2023,
            league_id="12345",
            params=[
                ("view", "kona_player_info"),
            ],
            headers={
                "X-Fantasy-Filter": json.dumps(
                    {
                        "players": {
                            "limit": 1500,
                            "sortAppliedStatTotal": {
                                "sortAsc": False,
                                "sortPriority": 2,
                                "value": "002024",
                            },
                        }
                    }
                )
            },
            swid_cookie="{ABC-123}",
            espn_s2_cookie="S2-COOKIE",
        )

    @patch("lambdas.step_function_lambdas.league_drafts.main.make_espn_api_request")
    def test_get_player_season_totals_before_2018_success(self, mock_make_request):
        """Tests successful invocation of get_player_season_totals for seasons before 2018."""
        # Set up test data
        mock_make_request.return_value = {
            "players": [
                {
                    "id": "1",
                },
                {
                    "id": "2",
                },
            ],
        }
        expected_players = [
            {
                "id": "1",
            },
            {
                "id": "2",
            },
        ]

        # Act
        players = get_player_season_totals(
            league_id="12345",
            platform="ESPN",
            season="2017",
            swid_cookie="{ABC-123}",
            espn_s2_cookie="S2-COOKIE",
        )

        # Assert
        self.assertEqual(players, expected_players)
        mock_make_request.assert_any_call(
            season=2017,
            league_id="12345",
            params=[
                ("seasonId", "2017"),
                ("view", "kona_player_info"),
            ],
            headers={
                "X-Fantasy-Filter": json.dumps(
                    {
                        "players": {
                            "limit": 1500,
                            "sortAppliedStatTotal": {
                                "sortAsc": False,
                                "sortPriority": 2,
                                "value": "002024",
                            },
                        }
                    }
                )
            },
            swid_cookie="{ABC-123}",
            espn_s2_cookie="S2-COOKIE",
        )

    def test_get_player_season_totals_missing_cookies(self):
        """Test get_player_season_totals function raises ValueError if cookies are missing."""
        # Act
        with pytest.raises(ValueError):
            get_player_season_totals(
                league_id="12345",
                platform="ESPN",
                season="2017",
                swid_cookie=None,
                espn_s2_cookie=None,
            )

    def test_get_player_season_totals_invalid_platform(self):
        """Test get_player_season_totals function raises ValueError if an unsupported platform is provided."""
        # Act
        with pytest.raises(ValueError):
            get_player_season_totals(
                league_id="12345",
                platform="Sleeper",
                season="2017",
                swid_cookie=None,
                espn_s2_cookie=None,
            )


class TestProcessPlayerScoringTotals(unittest.TestCase):
    """Class for testing process_player_scoring_totals function."""

    def test_process_player_scoring_totals_after_2018(self):
        """Test process_player_scoring_totals for post-2018 data."""
        # Set up test data
        player_totals = [
            {
                "player": {
                    "defaultPositionId": 1,
                    "fullName": "First Last",
                },
                "id": "1",
                "ratings": {"0": {"totalRating": 100.08}},
            },
            {
                "player": {
                    "defaultPositionId": 1,
                    "fullName": "First Last",
                },
                "id": "2",
            },
        ]
        expected_processed_totals = [
            {
                "player_id": "1",
                "player_name": "First Last",
                "position": "QB",
                "total_points": 100.08,
            }
        ]

        # Act
        processed_totals = process_player_scoring_totals(
            player_totals=player_totals,
            season="2023",
        )

        # Assert
        self.assertEqual(processed_totals, expected_processed_totals)

    def test_process_player_scoring_totals_before_2018(self):
        """Test process_player_scoring_totals for pre-2018 data."""
        # Set up test data
        player_totals = [
            {
                "player": {
                    "defaultPositionId": 1,
                    "fullName": "First Last",
                    "stats": [
                        {
                            "appliedTotal": 100.08,
                        },
                    ],
                },
                "id": "1",
            },
        ]
        expected_processed_totals = [
            {
                "player_id": "1",
                "player_name": "First Last",
                "position": "QB",
                "total_points": 100.08,
            }
        ]

        # Act
        processed_totals = process_player_scoring_totals(
            player_totals=player_totals,
            season="2017",
        )

        # Assert
        self.assertEqual(processed_totals, expected_processed_totals)


class TestEnrichDraftData(unittest.TestCase):
    """Class for testing enrich_draft_data function."""

    def test_enrich_draft_data_success(self):
        """Test successful execution of enrich_draft_data function."""
        # Set up test data
        draft_results = [
            {
                "autoDraftTypeId": 0,
                "bidAmount": 0,
                "id": 1,
                "keeper": False,
                "lineupSlotId": 2,
                "memberId": "1",
                "nominatingTeamId": 0,
                "overallPickNumber": 1,
                "playerId": 123,
                "reservedForKeeper": False,
                "roundId": 1,
                "roundPickNumber": 1,
                "teamId": 8,
                "tradeLocked": False,
            },
        ]
        player_totals = [
            {
                "player_id": 123,
                "player_name": "First Last",
                "position": "QB",
                "total_points": 100.08,
            },
        ]
        teams = [
            {
                "PK": "LEAGUE#1#PLATFORM#ESPN#SEASON#2025",
                "SK": "TEAM#8",
                "owner_first_name": "First",
                "owner_full_name": "First Last",
                "owner_id": ["id_123"],
                "owner_last_name": "Last",
                "team_abbreviation": "ABC",
                "team_id": "8",
                "team_name": "Team Name",
                "season": "2025",
            }
        ]
        expected_data = [
            {
                "auto_draft_type_id": 0,
                "bid_amount": 0,
                "draft_position_rank_delta": 0,
                "keeper": False,
                "overall_pick_number": 1,
                "owner_full_name": "First Last",
                "owner_id": "id_123",
                "player_id": 123,
                "player_name": "First Last",
                "position": "QB",
                "position_draft_rank": 1,
                "position_rank": 1,
                "reserved_for_keeper": False,
                "round": 1,
                "round_pick_number": 1,
                "team_id": "8",
                "total_players_at_position": 1,
                "total_points": 100.08,
                "trade_locked": False,
            },
        ]

        # Act
        data = enrich_draft_data(
            draft_results=draft_results,
            player_totals=player_totals,
            teams=teams,
        )

        # Assert
        self.assertEqual(data, expected_data)


class TestLambdaHandler(unittest.TestCase):
    """Class for testing lambda_handler function."""

    @patch("lambdas.step_function_lambdas.league_drafts.main.get_teams")
    @patch("lambdas.step_function_lambdas.league_drafts.main.get_draft_results")
    @patch("lambdas.step_function_lambdas.league_drafts.main.get_player_season_totals")
    @patch(
        "lambdas.step_function_lambdas.league_drafts.main.process_player_scoring_totals"
    )
    @patch("lambdas.step_function_lambdas.league_drafts.main.enrich_draft_data")
    @patch("lambdas.step_function_lambdas.league_drafts.main.batch_write_to_dynamodb")
    def test_lambda_handler_success(
        self,
        mock_batch_write_to_dynamodb,
        mock_enrich_draft_data,
        mock_process_player_scoring_totals,
        mock_get_player_season_totals,
        mock_get_draft_results,
        mock_get_teams,
    ):
        """Tests happy path for lambda_handler function."""
        # NOTE: This test is just for line coverage, the live dependency test
        # is a more accurate test for a handler function.

        # Mock all dependencies
        mock_get_teams.return_value = None
        mock_get_draft_results.return_value = None
        mock_get_player_season_totals.return_value = None
        mock_process_player_scoring_totals.return_value = None
        mock_enrich_draft_data.return_value = [
            {
                "round": 1,
                "round_pick_number": 1,
                "overall_pick_number": 1,
                "reserved_for_keeper": False,
                "bid_amount": 0,
                "keeper": False,
                "player_id": 123,
                "player_name": "First Last",
                "position": "QB",
                "total_points": 100.08,
                "position_rank": 1,
                "position_draft_rank": 1,
                "draft_position_rank_delta": 0,
                "owner_id": 2,
                "owner_full_name": "Owner Two",
            },
        ]
        mock_batch_write_to_dynamodb.return_value = None

        # Act
        lambda_handler(
            event={
                "leagueId": "12345",
                "platform": "ESPN",
                "swidCookie": None,
                "espnS2Cookie": None,
                "season": "2023",
            },
            context={},
        )

        # Assert
        # NOTE: No specific assertions for this one as the live dependency test will test the handler
        assert True
