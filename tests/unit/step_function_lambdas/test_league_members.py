import unittest
from unittest.mock import patch

import pytest

from lambdas.step_function_lambdas.league_members.main import (
    get_league_members_and_teams,
    join_league_members_to_teams,
    lambda_handler,
)


class TestGetLeagueMembersAndTeams(unittest.TestCase):
    """Tests for get_league_members_and_teams function."""

    @patch("lambdas.step_function_lambdas.league_members.main.make_espn_api_request")
    def test_get_league_members_and_teams_public_league(self, mock_make_request):
        """Test fetching league members and teams for a public ESPN league."""
        # Set up test variables
        league_id = "12345"
        platform = "ESPN"
        privacy = "public"
        season = "2021"

        # Mock API response
        mock_response = {
            "members": [{"id": "1", "firstName": "John", "lastName": "Doe"}],
            "teams": [{"id": "10", "ownerId": "1", "teamName": "Team A"}],
        }
        mock_make_request.return_value = mock_response

        # Act
        members, teams = get_league_members_and_teams(
            league_id=league_id,
            platform=platform,
            privacy=privacy,
            season=season,
        )

        # Assert
        self.assertEqual(members, mock_response["members"])
        self.assertEqual(teams, mock_response["teams"])
        mock_make_request.assert_called_once_with(
            season=int(season),
            league_id=league_id,
            params={"view": "mTeam"},
            swid_cookie=None,
            espn_s2_cookie=None,
        )

    @patch("lambdas.step_function_lambdas.league_members.main.make_espn_api_request")
    def test_get_league_members_and_teams_private_league(self, mock_make_request):
        """Test fetching league members and teams for a private ESPN league."""
        # Set up test variables
        league_id = "12345"
        platform = "ESPN"
        privacy = "private"
        season = "2021"
        swid_cookie = "{SWID-COOKIE}"
        espn_s2_cookie = "{ESPN-S2-COOKIE}"

        # Mock API response
        mock_response = {
            "members": [{"id": "1", "firstName": "John", "lastName": "Doe"}],
            "teams": [{"id": "10", "ownerId": "1", "teamName": "Team A"}],
        }
        mock_make_request.return_value = mock_response

        # Act
        members, teams = get_league_members_and_teams(
            league_id=league_id,
            platform=platform,
            privacy=privacy,
            season=season,
            swid_cookie=swid_cookie,
            espn_s2_cookie=espn_s2_cookie,
        )

        # Assert
        self.assertEqual(members, mock_response["members"])
        self.assertEqual(teams, mock_response["teams"])
        mock_make_request.assert_called_once_with(
            season=int(season),
            league_id=league_id,
            params={"view": "mTeam"},
            swid_cookie="{SWID-COOKIE}",
            espn_s2_cookie="{ESPN-S2-COOKIE}",
        )

    def test_get_league_members_and_teams_private_league_no_cookies(self):
        """Test fetching league members and teams for a private ESPN league without cookies."""
        # Set up test variables
        league_id = "12345"
        platform = "ESPN"
        privacy = "private"
        season = "2021"

        # Act
        with pytest.raises(ValueError):
            get_league_members_and_teams(
                league_id=league_id,
                platform=platform,
                privacy=privacy,
                season=season,
            )

    @patch("lambdas.step_function_lambdas.league_members.main.make_espn_api_request")
    def test_get_league_members_and_teams_private_league_before_2018(
        self, mock_make_request
    ):
        """Test fetching league members and teams for a private ESPN league for season before 2018."""
        # Set up test variables
        league_id = "12345"
        platform = "ESPN"
        privacy = "private"
        season = "2017"
        swid_cookie = "{SWID-COOKIE}"
        espn_s2_cookie = "{ESPN-S2-COOKIE}"

        # Mock API response
        mock_response = {
            "members": [{"id": "1", "firstName": "John", "lastName": "Doe"}],
            "teams": [{"id": "10", "ownerId": "1", "teamName": "Team A"}],
        }
        mock_make_request.return_value = mock_response

        # Act
        members, teams = get_league_members_and_teams(
            league_id=league_id,
            platform=platform,
            privacy=privacy,
            season=season,
            swid_cookie=swid_cookie,
            espn_s2_cookie=espn_s2_cookie,
        )

        # Assert
        self.assertEqual(members, mock_response["members"])
        self.assertEqual(teams, mock_response["teams"])
        mock_make_request.assert_called_once_with(
            season=int(season),
            league_id=league_id,
            params={"view": "mTeam", "seasonId": season},
            swid_cookie="{SWID-COOKIE}",
            espn_s2_cookie="{ESPN-S2-COOKIE}",
        )

    def test_get_league_members_and_teams_unsupported_platform(self):
        """Test fetching league members and teams for an unsupported platform."""
        # Set up test variables
        league_id = "12345"
        platform = "Sleeper"
        privacy = "private"
        season = "2021"

        # Act
        with pytest.raises(ValueError):
            get_league_members_and_teams(
                league_id=league_id,
                platform=platform,
                privacy=privacy,
                season=season,
            )


class TestJoinLeagueMembersToTeams(unittest.TestCase):
    """Tests for join_league_members_to_teams function."""

    def test_join_league_members_to_teams_success(self):
        """Test joining league members to teams successfully."""
        # Set up test data
        members = [
            {
                "id": "1",
                "firstName": "John",
                "lastName": "Doe",
                "displayName": "johndoe",
            },
            {
                "id": "2",
                "firstName": "Jane",
                "lastName": "Smith",
                "displayName": "janesmith",
            },
        ]
        teams = [
            {"abbrev": "A", "id": "10", "name": "Team A", "owners": ["1"]},
            {"abbrev": "B", "id": "20", "name": "Team B", "owners": ["2"]},
        ]
        expected_output = [
            {
                "firstName": "John",
                "lastName": "Doe",
                "abbrev": "A",
                "teamId": "10",
                "teamName": "Team A",
                "displayName": ["johndoe"],
                "memberId": ["1"],
            },
            {
                "firstName": "Jane",
                "lastName": "Smith",
                "abbrev": "B",
                "teamId": "20",
                "teamName": "Team B",
                "displayName": ["janesmith"],
                "memberId": ["2"],
            },
        ]

        # Act
        combined_data = join_league_members_to_teams(members=members, teams=teams)

        # Assert
        combined_data_sorted = sorted(combined_data, key=lambda x: x["teamId"])
        expected_sorted = sorted(expected_output, key=lambda x: x["teamId"])
        self.assertEqual(combined_data_sorted, expected_sorted)


class TestLambdaHandler(unittest.TestCase):
    """Tests for lambda_handler function."""

    @patch(
        "lambdas.step_function_lambdas.league_members.main.get_league_members_and_teams"
    )
    @patch(
        "lambdas.step_function_lambdas.league_members.main.join_league_members_to_teams"
    )
    @patch("lambdas.step_function_lambdas.league_members.main.batch_write_to_dynamodb")
    def test_lambda_handler_success(
        self, mock_batch_write, mock_join_members_teams, mock_get_members_teams
    ):
        """Test lambda_handler function successfully processes event."""
        # Set up test event
        event = {
            "leagueId": "12345",
            "platform": "ESPN",
            "privacy": "public",
            "swidCookie": None,
            "espnS2Cookie": None,
            "season": "2021",
        }

        # Mock return values
        mock_get_members_teams.return_value = (
            [
                {
                    "id": "1",
                    "firstName": "John",
                    "lastName": "Doe",
                    "displayName": "johndoe",
                },
                {
                    "id": "2",
                    "firstName": "Jane",
                    "lastName": "Smith",
                    "displayName": "janesmith",
                },
            ],
            [
                {"abbrev": "A", "id": "10", "name": "Team A", "owners": ["1"]},
                {"abbrev": "B", "id": "20", "name": "Team B", "owners": ["2"]},
            ],
        )
        mock_join_members_teams.return_value = [
            {
                "firstName": "John",
                "lastName": "Doe",
                "abbrev": "A",
                "teamId": "10",
                "teamName": "Team A",
                "displayName": ["johndoe"],
                "memberId": ["1"],
            },
            {
                "firstName": "Jane",
                "lastName": "Smith",
                "abbrev": "B",
                "teamId": "20",
                "teamName": "Team B",
                "displayName": ["janesmith"],
                "memberId": ["2"],
            },
        ]
        mock_batch_write.return_value = None

        # Act
        lambda_handler(event=event, context=None)

        # Assert
        mock_get_members_teams.assert_called_once_with(
            league_id="12345",
            platform="ESPN",
            privacy="public",
            season="2021",
            swid_cookie=None,
            espn_s2_cookie=None,
        )
        mock_join_members_teams.assert_called_once_with(
            members=[
                {
                    "id": "1",
                    "firstName": "John",
                    "lastName": "Doe",
                    "displayName": "johndoe",
                },
                {
                    "id": "2",
                    "firstName": "Jane",
                    "lastName": "Smith",
                    "displayName": "janesmith",
                },
            ],
            teams=[
                {"abbrev": "A", "id": "10", "name": "Team A", "owners": ["1"]},
                {"abbrev": "B", "id": "20", "name": "Team B", "owners": ["2"]},
            ],
        )
        mock_batch_write.assert_called_once_with(
            batched_objects=[
                {
                    "PutRequest": {
                        "Item": {
                            "PK": {"S": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2021"},
                            "SK": {"S": "TEAM#10"},
                            "GSI5PK": {"S": "LEAGUE#12345"},
                            "GSI5SK": {"S": "FOR_DELETION_USE_ONLY"},
                            "owner_full_name": {"S": "John Doe"},
                            "owner_first_name": {"S": "John"},
                            "owner_last_name": {"S": "Doe"},
                            "owner_id": {"L": [{"S": "1"}]},
                            "team_id": {"S": "10"},
                            "team_name": {"S": "Team A"},
                            "team_abbreviation": {"S": "A"},
                        }
                    }
                },
                {
                    "PutRequest": {
                        "Item": {
                            "PK": {"S": "LEAGUE#12345#PLATFORM#ESPN#SEASON#2021"},
                            "SK": {"S": "TEAM#20"},
                            "GSI5PK": {"S": "LEAGUE#12345"},
                            "GSI5SK": {"S": "FOR_DELETION_USE_ONLY"},
                            "owner_full_name": {"S": "Jane Smith"},
                            "owner_first_name": {"S": "Jane"},
                            "owner_last_name": {"S": "Smith"},
                            "owner_id": {"L": [{"S": "2"}]},
                            "team_id": {"S": "20"},
                            "team_name": {"S": "Team B"},
                            "team_abbreviation": {"S": "B"},
                        }
                    }
                },
            ],
            table_name="fantasy-recap-app-db-dev",
        )

    @patch(
        "lambdas.step_function_lambdas.league_members.main.get_league_members_and_teams"
    )
    def test_lambda_handler_failure(self, mock_get_members_teams):
        """Test lambda_handler function raises ValueError if no members and teams returned."""
        # Set up test event
        event = {
            "leagueId": "12345",
            "platform": "ESPN",
            "privacy": "public",
            "swidCookie": None,
            "espnS2Cookie": None,
            "season": "2021",
        }

        # Mock return values
        mock_get_members_teams.return_value = ([], [])

        # Act
        with pytest.raises(ValueError):
            lambda_handler(event=event, context=None)
