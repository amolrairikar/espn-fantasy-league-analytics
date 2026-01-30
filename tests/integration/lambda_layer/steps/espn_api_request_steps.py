import os

from behave import given, when, then, use_step_matcher
from behave.runner import Context
from dotenv import load_dotenv

from lambda_layer.common_utils.espn_api_request import make_espn_api_request
from lambda_layer.common_utils.retryable_request_session import create_retry_session


@given("a requests session")  # type: ignore[reportCallIssue]
def create_requests_session(context: Context):
    """Creates a requests session using create_retry_session."""
    context.session = create_retry_session()


# Enables regex patterns in next step decorator
use_step_matcher("re")


@when(
    r"we make an (authenticated|unauthenticated) ESPN Fantasy Football API request for the (\d{4}) season"
)  # type: ignore[reportCallIssue]
def execute_espn_api_request(context: Context, authenticated_status: str, season: str):
    """
    Make a request to ESPN Fantasy Football API with/without credentials
    depending on authenticated_status.
    """
    # Load sensitive credentials for test
    load_dotenv()

    response = None

    if authenticated_status == "authenticated":
        response = make_espn_api_request(
            season=int(season),
            league_id=os.environ["LEAGUE_ID"],
            params={},
            swid_cookie=os.environ["SWID_COOKIE"],
            espn_s2_cookie=os.environ["ESPN_S2_COOKIE"],
        )
        context.response = response
    else:
        try:
            response = make_espn_api_request(
                season=int(season),
                league_id="123456789",
                params={},
                swid_cookie=None,
                espn_s2_cookie=None,
            )
            context.response = response
        except Exception as e:
            print(f"Expected exception for unauthenticated request: {e}")
            context.response = None


@then(r"(a|no) response will be returned")  # type: ignore[reportCallIssue]
def check_api_response(context: Context, expected_response: str):
    """Check if a response was returned by the API request."""
    if expected_response == "a":
        assert context.response is not None
    else:
        assert context.response is None
