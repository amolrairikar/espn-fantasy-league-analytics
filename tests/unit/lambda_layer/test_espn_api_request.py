import unittest
from unittest.mock import patch, MagicMock

import requests

from lambda_layer.common_utils.espn_api_request import (
    get_base_api_url,
    make_espn_api_request,
)


class TestGetBaseUrl(unittest.TestCase):
    """Tests for get_base_api_url function."""

    def test_url_for_season_after_2018(self):
        """Test that correct URL is returned for seasons after 2018."""
        season = 2020
        league_id = "12345"
        expected_url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}"
        actual_url = get_base_api_url(season=season, league_id=league_id)
        self.assertEqual(actual_url, expected_url)

    def test_url_for_season_before_2018(self):
        """Test that correct URL is returned for seasons before 2018."""
        season = 2015
        league_id = "67890"
        expected_url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/leagueHistory/{league_id}"
        actual_url = get_base_api_url(season=season, league_id=league_id)
        self.assertEqual(actual_url, expected_url)


class TestMakeEspnApiRequest(unittest.TestCase):
    """Tests for make_espn_api_request function."""

    @patch("lambda_layer.common_utils.espn_api_request.session.get")
    def test_make_espn_api_request_after_2018_with_cookies(self, mock_get):
        """Test API request after 2018 with SWID and ESPN S2 cookies."""
        # Set up test variables
        season = 2021
        league_id = "12345"
        params = {"view": "mTeam"}
        swid_cookie = "{SWID-COOKIE}"
        espn_s2_cookie = "ESPNS2COOKIE"

        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_get.return_value = mock_response

        # Act
        response = make_espn_api_request(
            season=season,
            league_id=league_id,
            params=params,
            swid_cookie=swid_cookie,
            espn_s2_cookie=espn_s2_cookie,
        )

        # Assert
        mock_get.assert_called_once()
        _, called_kwargs = mock_get.call_args
        self.assertIn("params", called_kwargs)
        self.assertEqual(called_kwargs["params"], params)
        self.assertIn("cookies", called_kwargs)
        self.assertEqual(
            called_kwargs["cookies"],
            {"SWID": swid_cookie, "espn_s2": espn_s2_cookie},
        )
        self.assertEqual(response, {"status": "success"})

    @patch("lambda_layer.common_utils.espn_api_request.session.get")
    def test_make_espn_api_request_after_2018_with_header(self, mock_get):
        """Test API request after 2018 with SWID and ESPN S2 cookies plus a header."""
        # Set up test variables
        season = 2021
        league_id = "12345"
        params = {"view": "mTeam"}
        headers = {"Custom-Header": "HeaderValue"}
        swid_cookie = "{SWID-COOKIE}"
        espn_s2_cookie = "ESPNS2COOKIE"

        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_get.return_value = mock_response

        # Act
        response = make_espn_api_request(
            season=season,
            league_id=league_id,
            params=params,
            headers=headers,
            swid_cookie=swid_cookie,
            espn_s2_cookie=espn_s2_cookie,
        )

        # Assert
        mock_get.assert_called_once()
        _, called_kwargs = mock_get.call_args
        self.assertIn("params", called_kwargs)
        self.assertEqual(called_kwargs["params"], params)
        self.assertIn("cookies", called_kwargs)
        self.assertEqual(
            called_kwargs["cookies"],
            {"SWID": swid_cookie, "espn_s2": espn_s2_cookie},
        )
        self.assertIn("headers", called_kwargs)
        self.assertEqual(called_kwargs["headers"], headers)
        self.assertEqual(response, {"status": "success"})

    @patch("lambda_layer.common_utils.espn_api_request.session.get")
    def test_make_espn_api_request_after_2018_without_cookies(self, mock_get):
        """Test API request after 2018 without SWID and ESPN S2 cookies."""
        # Set up test variables
        season = 2021
        league_id = "12345"
        params = {"view": "mTeam"}

        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_get.return_value = mock_response

        # Act
        response = make_espn_api_request(
            season=season,
            league_id=league_id,
            params=params,
            swid_cookie=None,
            espn_s2_cookie=None,
        )

        # Assert
        mock_get.assert_called_once()
        _, called_kwargs = mock_get.call_args
        self.assertIn("params", called_kwargs)
        self.assertEqual(
            called_kwargs["params"],
            params,
        )
        self.assertNotIn("cookies", called_kwargs)
        self.assertEqual(response, {"status": "success"})

    @patch("lambda_layer.common_utils.espn_api_request.session.get")
    def test_make_espn_api_request_before_2018_with_cookies(self, mock_get):
        """Test API request with SWID and ESPN S2 cookies."""
        # Set up test variables
        season = 2017
        league_id = "12345"
        params = {"view": "mTeam"}
        swid_cookie = "{SWID-COOKIE}"
        espn_s2_cookie = "ESPNS2COOKIE"

        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = [{"status": "success"}]
        mock_get.return_value = mock_response

        # Act
        response = make_espn_api_request(
            season=season,
            league_id=league_id,
            params=params,
            swid_cookie=swid_cookie,
            espn_s2_cookie=espn_s2_cookie,
        )

        # Assert
        mock_get.assert_called_once()
        _, called_kwargs = mock_get.call_args
        self.assertIn("params", called_kwargs)
        self.assertEqual(
            called_kwargs["params"],
            params,
        )
        self.assertIn("cookies", called_kwargs)
        self.assertEqual(
            called_kwargs["cookies"],
            {"SWID": swid_cookie, "espn_s2": espn_s2_cookie},
        )
        self.assertEqual(response, {"status": "success"})

    @patch("lambda_layer.common_utils.espn_api_request.session.get")
    def test_make_espn_api_request_before_2018_without_cookies(self, mock_get):
        """Test API request before 2018 without SWID and ESPN S2 cookies."""
        # Set up test variables
        season = 2017
        league_id = "12345"
        params = {"view": "mTeam"}

        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = [{"status": "success"}]
        mock_get.return_value = mock_response

        # Act
        response = make_espn_api_request(
            season=season,
            league_id=league_id,
            params=params,
            swid_cookie=None,
            espn_s2_cookie=None,
        )

        # Assert
        mock_get.assert_called_once()
        _, called_kwargs = mock_get.call_args
        self.assertIn("params", called_kwargs)
        self.assertEqual(
            called_kwargs["params"],
            params,
        )
        self.assertNotIn("cookies", called_kwargs)
        self.assertEqual(response, {"status": "success"})

    @patch("lambda_layer.common_utils.espn_api_request.session.get")
    def test_make_espn_api_request_exception(self, mock_get):
        """Test that a requests.RequestException is raised on request failure."""
        # Set up test variables
        season = 2021
        league_id = "12345"
        params = {"view": "mTeam"}

        # Mock API response
        mock_get.side_effect = requests.RequestException("Request failed")

        # Act
        with self.assertRaises(requests.RequestException) as context:
            make_espn_api_request(
                season=season,
                league_id=league_id,
                params=params,
                swid_cookie=None,
                espn_s2_cookie=None,
            )

        # Assert
        mock_get.assert_called_once()
        self.assertIn("Request failed", str(context.exception))
