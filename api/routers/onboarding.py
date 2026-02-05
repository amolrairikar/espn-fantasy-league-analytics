"""FastAPI router for league onboarding (via Step Functions) endpoints."""

import json
import os

import boto3
import botocore.exceptions
from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

from api.dependencies import (
    get_api_key,
    logger,
)
from api.models import APIResponse, LeagueMetadata

router = APIRouter(
    prefix="/onboard",
    dependencies=[Depends(get_api_key)],
)


@router.post("", status_code=status.HTTP_201_CREATED)
def onboard_league(
    data: LeagueMetadata = Body(
        description="The league information (ID, cookies, platform) required for onboarding."
    ),
) -> APIResponse:
    """
    Onboards a league by triggering a Step Function execution that retrieves league
    data such as matchups, scores, etc.

    Args:
        league_id (str): ID of league to onboard.
        data (LeagueMetadata): The league information (ID, cookies, platform) required for onboarding.

    Returns:
        APIResponse: A JSON response with a message field indicating success/failure
            and an optional data field to capture additional details.

    Raises:
        HTTPException: 400, 404, or 500 errors if an exception occurs.
    """
    sfn = boto3.client("stepfunctions")
    try:
        execution_input = {
            "league_id": data.league_id,
            "platform": data.platform,
            "privacy": data.privacy,
            "swid_cookie": data.swid,
            "espn_s2_cookie": data.espn_s2,
            "seasons": data.seasons,
        }
        logger.info("Starting onboarding process for league %s", data.league_id)
        # TODO: Remove region hardcoding in env variable if in future the Step Function is multi-region
        response = sfn.start_execution(
            stateMachineArn=os.environ["ONBOARDING_SFN_ARN"],
            input=json.dumps(execution_input),
        )
        logger.info("Step Function response: %s", response)
        return APIResponse(
            detail="Successfully triggered onboarding",
            data={"execution_id": response["executionArn"].rsplit(":", 1)[-1]},
        )
    except botocore.exceptions.ClientError as e:
        logger.exception("Unexpected error while triggering Step Function")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/{onboarding_execution_id}", status_code=status.HTTP_200_OK)
def check_onboarding_status(
    onboarding_execution_id: str = Path(
        description="Execution ID for the Step Function run."
    ),
) -> APIResponse:
    """
    Onboards a league by triggering a Step Function execution that retrieves league
    data such as matchups, scores, etc.

    Args:
        onboarding_execution_id (str): Execution ID for the Step Function run.

    Returns:
        APIResponse: A JSON response with a message field indicating success/failure
            and an optional data field to capture additional details.

    Raises:
        HTTPException: 400, 404, or 500 errors if an exception occurs.
    """
    sfn = boto3.client("stepfunctions")
    try:
        logger.info(
            "Checking status for onboarding execution: %s", onboarding_execution_id
        )
        if os.environ["ENVIRONMENT"] == "PROD":
            execution_arn = f"arn:aws:states:{os.environ['AWS_REGION']}:{os.environ['ACCOUNT_NUMBER']}:execution:league-onboarding:{onboarding_execution_id}"
        else:
            execution_arn = f"arn:aws:states:{os.environ['AWS_REGION']}:{os.environ['ACCOUNT_NUMBER']}:execution:league-onboarding-dev:{onboarding_execution_id}"
        response = sfn.describe_execution(
            executionArn=execution_arn,
        )
        logger.info("Execution status: %s", response)
        api_response = {"execution_status": response["status"]}
        return APIResponse(
            detail="Successfully retrieved onboarding status",
            data=api_response,
        )
    except botocore.exceptions.ClientError as e:
        logger.exception("Unexpected error while retrieving onboarding status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
