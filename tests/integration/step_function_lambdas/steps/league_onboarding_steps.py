import json
import os
import time

import boto3
from behave import given, when, then
from behave.runner import Context
from dotenv import load_dotenv


@given("a league with valid inputs")  # type: ignore[reportCallIssue]
def get_valid_inputs(context: Context):
    """Fetch valid league onboarding inputs from a .env file."""
    load_dotenv()
    context.league_id = os.environ["LEAGUE_ID"]
    context.platform = os.environ["PLATFORM"]
    context.privacy = os.environ["PRIVACY"].lower()
    context.swid_cookie = os.environ["SWID_COOKIE"]
    context.espn_s2_cookie = os.environ["ESPN_S2_COOKIE"]
    first_season: str = os.environ["FIRST_SEASON"]
    last_season: str = os.environ["LAST_SEASON"]
    context.seasons = list(range(int(first_season), int(last_season) + 1))


@when("we onboard the league")  # type: ignore[reportCallIssue]
def start_league_onboarding(context: Context):
    """Triggers league onboarding step function."""
    sfn = boto3.client("stepfunctions")
    execution_input = {
        "league_id": context.league_id,
        "platform": context.platform,
        "privacy": context.privacy,
        "swid_cookie": context.swid_cookie,
        "espn_s2_cookie": context.espn_s2_cookie,
        "seasons": context.seasons,
    }
    response = sfn.start_execution(
        stateMachineArn=os.environ["ONBOARDING_SFN_ARN"],
        input=json.dumps(execution_input),
    )
    context.execution_id = response["executionArn"].rsplit(":", 1)[-1]


@then("the league should onboard successfully")  # type: ignore[reportCallIssue]
def check_league_onboarding(context: Context):
    """Polls the league onboarding Step Function to validate it completed successfully."""
    sfn_completed = False
    sfn_status = "NOT_STARTED"
    sfn = boto3.client("stepfunctions")
    execution_arn = f"arn:aws:states:us-east-1:{os.environ['ACCOUNT_NUMBER']}:execution:league-onboarding-dev:{context.execution_id}"
    while not sfn_completed:
        response = sfn.describe_execution(
            executionArn=execution_arn,
        )
        sfn_status = response["status"]
        if sfn_status in ["SUCCEEDED", "FAILED", "TIMED_OUT", "ABORTED"]:
            print(f"Step Function completed with status {sfn_status}")
            sfn_completed = True
        elif sfn_status == "RUNNING":
            print("Step Function still running. Rechecking in 5 seconds...")
            time.sleep(5)
        else:
            raise ValueError(
                f"Step Function encountered unexpected status: {sfn_status}"
            )
    assert sfn_status == "SUCCEEDED"
