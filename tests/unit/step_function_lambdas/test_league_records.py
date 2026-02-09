import unittest
from unittest.mock import patch

import pytest
from decimal import Decimal

from lambdas.step_function_lambdas.league_records.main import (
    compile_all_time_records,
    format_dynamodb_item,
    lambda_handler,
)


class TestCompileAllTimeRecords(unittest.TestCase):
    """Class for testing compile_all_time_records function."""

    def test_compile_all_time_records(self):
        """Tests successful execution of compile_all_time_records function."""
        # Set up test data
        matchup_data = [
            {
                "season": "2025",
                "week": "1",
                "team_a_owner_id": "owner1",
                "team_a_owner_full_name": "Owner One",
                "team_a_score": 100,
                "team_a_starting_players": [
                    {
                        "player_id": "pqb",
                        "full_name": "QB One",
                        "points_scored": 30,
                        "position": "QB",
                    },
                    {
                        "player_id": "prb",
                        "full_name": "RB One",
                        "points_scored": 20,
                        "position": "RB",
                    },
                    {
                        "player_id": "pwr",
                        "full_name": "WR One",
                        "points_scored": 15,
                        "position": "WR",
                    },
                    {
                        "player_id": "pte",
                        "full_name": "TE One",
                        "points_scored": 10,
                        "position": "TE",
                    },
                ],
                "team_b_owner_id": "owner2",
                "team_b_owner_full_name": "Owner Two",
                "team_b_score": 90,
                "team_b_starting_players": [
                    {
                        "player_id": "pdst",
                        "full_name": "DST One",
                        "points_scored": 12,
                        "position": "D/ST",
                    },
                    {
                        "player_id": "pk",
                        "full_name": "K One",
                        "points_scored": 5,
                        "position": "K",
                    },
                ],
            }
        ]
        members_data = [
            {
                "PK": "TEAM#team1#2025",
                "team_id": "team1",
                "owner_id": "owner1",
                "owner_full_name": "Owner One",
            },
            {
                "PK": "TEAM#team2#2025",
                "team_id": "team2",
                "owner_id": "owner2",
                "owner_full_name": "Owner Two",
            },
        ]
        championship_team_data = [
            {"season": "2025", "team_id": "team1", "championship_status": "WIN"}
        ]

        # Set up expected result lists
        expected_championships = [
            {
                "owner_full_name": "Owner One",
                "owner_id": "owner1",
                "championships_won": 1,
            }
        ]

        expected_top10_scores = [
            {
                "season": "2025",
                "week": "1",
                "owner_name": "Owner One",
                "owner_id": "owner1",
                "score": 100,
            },
            {
                "season": "2025",
                "week": "1",
                "owner_name": "Owner Two",
                "owner_id": "owner2",
                "score": 90,
            },
        ]

        expected_bottom10_scores = [
            {
                "season": "2025",
                "week": "1",
                "owner_name": "Owner Two",
                "owner_id": "owner2",
                "score": 90,
            },
            {
                "season": "2025",
                "week": "1",
                "owner_name": "Owner One",
                "owner_id": "owner1",
                "score": 100,
            },
        ]

        expected_top10_qb = [
            {
                "season": "2025",
                "week": "1",
                "owner_full_name": "Owner One",
                "owner_id": "owner1",
                "player_id": "pqb",
                "full_name": "QB One",
                "points_scored": Decimal(30),
                "position": "QB",
            }
        ]

        expected_top10_rb = [
            {
                "season": "2025",
                "week": "1",
                "owner_full_name": "Owner One",
                "owner_id": "owner1",
                "player_id": "prb",
                "full_name": "RB One",
                "points_scored": Decimal(20),
                "position": "RB",
            }
        ]

        expected_top10_wr = [
            {
                "season": "2025",
                "week": "1",
                "owner_full_name": "Owner One",
                "owner_id": "owner1",
                "player_id": "pwr",
                "full_name": "WR One",
                "points_scored": Decimal(15),
                "position": "WR",
            }
        ]

        expected_top10_te = [
            {
                "season": "2025",
                "week": "1",
                "owner_full_name": "Owner One",
                "owner_id": "owner1",
                "player_id": "pte",
                "full_name": "TE One",
                "points_scored": Decimal(10),
                "position": "TE",
            }
        ]

        expected_top10_dst = [
            {
                "season": "2025",
                "week": "1",
                "owner_full_name": "Owner Two",
                "owner_id": "owner2",
                "player_id": "pdst",
                "full_name": "DST One",
                "points_scored": Decimal(12),
                "position": "D/ST",
            }
        ]

        expected_top10_k = [
            {
                "season": "2025",
                "week": "1",
                "owner_full_name": "Owner Two",
                "owner_id": "owner2",
                "player_id": "pk",
                "full_name": "K One",
                "points_scored": Decimal(5),
                "position": "K",
            }
        ]

        # Act
        (
            championships,
            top10_scores,
            bottom10_scores,
            top10_qb,
            top10_rb,
            top10_wr,
            top10_te,
            top10_dst,
            top10_k,
        ) = compile_all_time_records(
            matchup_data=matchup_data,
            members_data=members_data,
            championship_team_data=championship_team_data,
        )

        # Assert
        self.assertEqual(championships, expected_championships)
        self.assertEqual(top10_scores, expected_top10_scores)
        self.assertEqual(bottom10_scores, expected_bottom10_scores)
        self.assertEqual(top10_qb, expected_top10_qb)
        self.assertEqual(top10_rb, expected_top10_rb)
        self.assertEqual(top10_wr, expected_top10_wr)
        self.assertEqual(top10_te, expected_top10_te)
        self.assertEqual(top10_dst, expected_top10_dst)
        self.assertEqual(top10_k, expected_top10_k)


class TestFormatDynamodbItem(unittest.TestCase):
    """Class for testing format_dynamodb_item function."""

    def test_format_dynamodb_item_all_time_championships(self):
        """Tests all_time_championships formatting."""
        # Set up test data
        item = {
            "owner_id": "owner1",
            "owner_full_name": "Owner One",
            "championships_won": 2,
        }

        # Act
        formatted = format_dynamodb_item(
            record_type="all_time_championships",
            item=item,
            league_id="league123",
            platform="ESPN",
        )

        # Assert
        expected = {
            "PK": {"S": "LEAGUE#league123#PLATFORM#ESPN"},
            "SK": {"S": "HALL_OF_FAME#CHAMPIONSHIPS#owner1"},
            "GSI5PK": {"S": "LEAGUE#league123"},
            "GSI5SK": {"S": "FOR_DELETION_USE_ONLY"},
            "owner_id": {"S": "owner1"},
            "owner_full_name": {"S": "Owner One"},
            "championships_won": {"N": "2"},
        }
        self.assertEqual(formatted, expected)

    def test_format_dynamodb_item_top_and_bottom_team_scores(self):
        """Tests top_10_scores and bottom_10_scores formatting."""
        # Set up test data
        top_item = {
            "season": "2025",
            "week": "1",
            "owner_id": "owner1",
            "owner_name": "Owner One",
            "score": 123,
        }
        expected_top = {
            "PK": {"S": "LEAGUE#league123#PLATFORM#ESPN"},
            "SK": {"S": "HALL_OF_FAME#TOP10TEAMSCORES#owner1#2025#1"},
            "GSI5PK": {"S": "LEAGUE#league123"},
            "GSI5SK": {"S": "FOR_DELETION_USE_ONLY"},
            "owner_id": {"S": "owner1"},
            "owner_full_name": {"S": "Owner One"},
            "season": {"S": "2025"},
            "week": {"N": "1"},
            "points_scored": {"N": "123"},
        }

        # Act
        formatted_top = format_dynamodb_item(
            record_type="top_10_scores",
            item=top_item,
            league_id="league123",
            platform="ESPN",
        )

        # Assert
        self.assertEqual(formatted_top, expected_top)

        # Set up test data
        bottom_item = {
            "season": "2025",
            "week": "2",
            "owner_id": "owner2",
            "owner_name": "Owner Two",
            "score": 10,
        }
        expected_bottom = {
            "PK": {"S": "LEAGUE#league123#PLATFORM#ESPN"},
            "SK": {"S": "HALL_OF_FAME#BOTTOM10TEAMSCORES#owner2#2025#2"},
            "GSI5PK": {"S": "LEAGUE#league123"},
            "GSI5SK": {"S": "FOR_DELETION_USE_ONLY"},
            "owner_id": {"S": "owner2"},
            "owner_full_name": {"S": "Owner Two"},
            "season": {"S": "2025"},
            "week": {"N": "2"},
            "points_scored": {"N": "10"},
        }

        # Act
        formatted_bottom = format_dynamodb_item(
            record_type="bottom_10_scores",
            item=bottom_item,
            league_id="league123",
            platform="ESPN",
        )

        # Assert
        self.assertEqual(formatted_bottom, expected_bottom)

    def _assert_player_record(self, record_type, item, expected_sk_suffix):
        """Utility function for asserting top 10 player score test results."""
        # Set up test data
        expected = {
            "PK": {"S": "LEAGUE#LID#PLATFORM#ESPN"},
            "SK": {"S": expected_sk_suffix},
            "GSI5PK": {"S": "LEAGUE#LID"},
            "GSI5SK": {"S": "FOR_DELETION_USE_ONLY"},
            "season": {"S": item["season"]},
            "week": {"N": str(item["week"])},
            "owner_id": {"S": item["owner_id"]},
            "owner_full_name": {"S": item["owner_full_name"]},
            "player_name": {"S": item["full_name"]},
            "points_scored": {"N": str(item["points_scored"])},
            "position": {"S": item["position"]},
        }

        # Act
        formatted = format_dynamodb_item(
            record_type=record_type, item=item, league_id="LID", platform="ESPN"
        )

        # Assert
        self.assertEqual(formatted, expected)

    def test_format_dynamodb_item_top_10_player_scores(self):
        """Tests formatting for player performance record types (QB,RB,WR,TE,DST,K)."""
        # Set up test data
        base_item = {
            "season": "2025",
            "week": "3",
            "owner_id": "ownerX",
            "owner_full_name": "Owner X",
            "player_id": "p1",
            "full_name": "Player One",
            "points_scored": Decimal("45"),
            "position": "QB",
        }

        # QB
        self._assert_player_record(
            record_type="top_10_qb_scores",
            item=base_item,
            expected_sk_suffix="HALL_OF_FAME#TOP10PERFORMANCES#QB#p1#2025#3",
        )

        # RB
        rb_item = dict(base_item, position="RB", player_id="p2")
        self._assert_player_record(
            record_type="top_10_rb_scores",
            item=rb_item,
            expected_sk_suffix="HALL_OF_FAME#TOP10PERFORMANCES#RB#p2#2025#3",
        )

        # WR
        wr_item = dict(base_item, position="WR", player_id="p3")
        self._assert_player_record(
            record_type="top_10_wr_scores",
            item=wr_item,
            expected_sk_suffix="HALL_OF_FAME#TOP10PERFORMANCES#WR#p3#2025#3",
        )

        # TE
        te_item = dict(base_item, position="TE", player_id="p4")
        self._assert_player_record(
            record_type="top_10_te_scores",
            item=te_item,
            expected_sk_suffix="HALL_OF_FAME#TOP10PERFORMANCES#TE#p4#2025#3",
        )

        # DST
        dst_item = dict(base_item, position="D/ST", player_id="p5")
        self._assert_player_record(
            record_type="top_10_dst_scores",
            item=dst_item,
            expected_sk_suffix="HALL_OF_FAME#TOP10PERFORMANCES#DST#p5#2025#3",
        )

        # K
        k_item = dict(base_item, position="K", player_id="p6")
        self._assert_player_record(
            record_type="top_10_k_scores",
            item=k_item,
            expected_sk_suffix="HALL_OF_FAME#TOP10PERFORMANCES#K#p6#2025#3",
        )

    def test_format_dynamodb_item_unsupported_record_type_raises(self):
        """Unsupported record types should raise ValueError."""
        # Act
        with pytest.raises(ValueError):
            format_dynamodb_item(
                record_type="nope", item={}, league_id="L", platform="P"
            )


class TestLambdaHandler(unittest.TestCase):
    """Test lambda_handler function."""

    @patch("lambdas.step_function_lambdas.league_records.main.fetch_league_data")
    @patch("lambdas.step_function_lambdas.league_records.main.compile_all_time_records")
    @patch("lambdas.step_function_lambdas.league_records.main.format_dynamodb_item")
    @patch("lambdas.step_function_lambdas.league_records.main.batch_write_to_dynamodb")
    def test_lambda_handler_success(
        self,
        mock_batch_write_to_dynamodb,
        mock_format_dynamodb_item,
        mock_compile_all_time_records,
        mock_fetch_data,
    ):
        """Tests happy path for lambda_handler function."""
        # NOTE: This test is just for line coverage, the live dependency test
        # is a more accurate test for a handler function.
        # Mock dependencies
        mock_fetch_data.return_value = ["dummy_value"]
        mock_compile_all_time_records.return_value = (
            ["items"],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
        )
        mock_format_dynamodb_item.return_value = {}
        mock_batch_write_to_dynamodb.return_value = None

        # Act
        lambda_handler(
            event=[
                [
                    {
                        "leagueId": "12345",
                        "platform": "ESPN",
                        "privacy": "private",
                        "swidCookie": None,
                        "espnS2Cookie": None,
                        "season": "2023",
                    },
                ],
            ],
            context={},
        )

        # Assert
        # NOTE: No specific assertions for this one as the live dependency test will test the handler
        assert True

    @patch("lambdas.step_function_lambdas.league_records.main.fetch_league_data")
    def test_lambda_handler_missing_data(self, mock_fetch_data):
        """Tests lambda_handler error handling when some input data is missing."""
        # Mock dependencies
        mock_fetch_data.return_value = []

        # Act
        with pytest.raises(ValueError):
            lambda_handler(
                event=[
                    [
                        {
                            "leagueId": "12345",
                            "platform": "ESPN",
                            "privacy": "private",
                            "swidCookie": None,
                            "espnS2Cookie": None,
                            "season": "2023",
                        },
                    ],
                ],
                context={},
            )
