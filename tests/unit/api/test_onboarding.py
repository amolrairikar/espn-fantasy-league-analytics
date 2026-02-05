import unittest
from unittest.mock import MagicMock, patch

import botocore.exceptions
import pytest

from api.models import APIResponse
from api.routers.onboarding import onboard_league, check_onboarding_status


@pytest.fixture(autouse=True)
def set_env_vars():
    with patch.dict(
        "os.environ",
        {
            "ENVIRONMENT": "DEV",
            "AWS_REGION": "us-east-1",
            "ACCOUNT_NUMBER": "123456789012",
            "ONBOARDING_SFN_ARN": "arn:aws:states:us-east-1:123456789012:stateMachine:league-onboarding-dev",
        },
    ):
        yield


class TestOnboardLeague(unittest.TestCase):
    @patch("api.routers.onboarding.boto3.client")
    def test_onboard_league_success(self, mock_boto_client):
        """Test successful onboarding of a league."""
        # Mock Step Functions client
        mock_sfn = MagicMock()
        mock_boto_client.return_value = mock_sfn
        mock_sfn.start_execution.return_value = {
            "executionArn": "arn:aws:states:region:account-id:execution:stateMachineName:executionName"
        }

        # Mock onboarding data
        data = MagicMock()
        data.league_id = "12345"
        data.platform = "ESPN"
        data.privacy = "PUBLIC"
        data.swid = "swid_cookie_value"
        data.espn_s2 = "espn_s2_cookie_value"
        data.seasons = [2021, 2022]

        # Act
        response = onboard_league(data=data)
        if response.data is None:
            self.fail("result.data is None, expected a list of items")

        # Assert
        self.assertEqual(
            response,
            APIResponse(
                detail="Successfully triggered onboarding",
                data={"execution_id": "executionName"},
            ),
        )
        mock_sfn.start_execution.assert_called_once()

    @patch("api.routers.onboarding.boto3.client")
    def test_onboard_league_failure(self, mock_boto_client):
        """Test onboarding failure due to Step Function error."""
        # Mock Step Functions client to raise an exception
        mock_sfn = MagicMock()
        mock_boto_client.return_value = mock_sfn
        mock_sfn.start_execution.side_effect = botocore.exceptions.ClientError(
            error_response={"Error": {"Code": "Step Function error"}},
            operation_name="StartExecution",
        )

        # Mock onboarding data
        data = MagicMock()
        data.league_id = "12345"
        data.platform = "ESPN"
        data.privacy = "PUBLIC"
        data.swid = "swid_cookie_value"
        data.espn_s2 = "espn_s2_cookie_value"
        data.seasons = [2021, 2022]

        # Act & Assert
        with self.assertRaises(Exception) as context:
            onboard_league(data)

        self.assertIn("Step Function error", str(context.exception))


class TestCheckOnboardingStatus(unittest.TestCase):
    """Tests for check_onboarding_status function."""

    @patch("api.routers.onboarding.boto3.client")
    def test_check_onboarding_status_success(self, mock_boto_client):
        """Test successful retrieval of onboarding status."""
        # Mock Step Functions client
        mock_sfn = MagicMock()
        mock_boto_client.return_value = mock_sfn
        mock_sfn.describe_execution.return_value = {"status": "SUCCEEDED"}

        # Act
        response = check_onboarding_status(onboarding_execution_id="executionName")
        if response.data is None:
            self.fail("result.data is None, expected a list of items")

        # Assert
        self.assertEqual(
            response,
            APIResponse(
                detail="Successfully retrieved onboarding status",
                data={"execution_status": "SUCCEEDED"},
            ),
        )
        mock_sfn.describe_execution.assert_called_once()

    @patch("api.routers.onboarding.boto3.client")
    def test_check_onboarding_status_failure(self, mock_boto_client):
        """Test failure in retrieving onboarding status due to Step Function error."""
        # Mock Step Functions client to raise an exception
        mock_sfn = MagicMock()
        mock_boto_client.return_value = mock_sfn
        mock_sfn.describe_execution.side_effect = botocore.exceptions.ClientError(
            error_response={"Error": {"Code": "Step Function error"}},
            operation_name="DescribeExecution",
        )

        # Act & Assert
        with self.assertRaises(Exception) as context:
            check_onboarding_status(onboarding_execution_id="executionName")

        self.assertIn("Step Function error", str(context.exception))
