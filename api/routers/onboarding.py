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
from api.models import APIError, APIResponse, LeagueMetadata

router = APIRouter(
    prefix="/onboard",
    dependencies=[Depends(get_api_key)],
)


@router.post(
    "/{league_id}",
    response_model=APIResponse,
    response_model_exclude_none=True,
    responses={
        400: {"model": APIError, "description": "Bad request"},
        404: {"model": APIError, "description": "State machine not found"},
        500: {"model": APIError, "description": "Internal server error"},
    },
)
def onboard_league(
    league_id: str = Path(description="ID of league to onboard."),
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
        logger.info("Starting onboarding process for league %s", league_id)
        # TODO: Remove region hardcoding if in future the Step Function is multi-region
        response = sfn.start_execution(
            stateMachineArn=f"arn:aws:states:us-east-2:{os.environ['ACCOUNT_NUMBER']}:stateMachine:league-onboarding",
            input=json.dumps(execution_input),
        )
        logger.info("Step Function response: %s", response)
        api_response = {"execution_id": response["executionArn"].rsplit(":", 1)[-1]}
        return APIResponse(
            message="success",
            detail="Successfully triggered onboarding",
            data=api_response,
        )
    except botocore.exceptions.ClientError as e:
        exception_mappings = {
            400: [
                "InvalidArn",
                "InvalidExecutionInput",
                "InvalidName",
            ],
            404: [
                "StateMachineDoesNotExist",
                "StateMachineDeleting",
            ],
        }
        status_messages = {
            400: "Bad request",
            404: "Resource not found",
            500: "Internal server error",
        }
        error_code = e.response.get("Error", {}).get("Code", "UnknownError")
        # TODO: turn this into a reusable function for the API
        for status_code, dynamo_errors in exception_mappings.items():
            if error_code in dynamo_errors:
                logger.exception("%d error", status_code)
                raise HTTPException(
                    status_code=status_code,
                    detail=APIError(
                        message="error",
                        detail=status_messages[status_code] + f" ({error_code})",
                    ).model_dump(),
                )
        logger.exception("Unexpected DynamoDB client error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                message="error", detail=status_messages[500] + f" ({error_code})"
            ).model_dump(),
        )


@router.get(
    "/{onboarding_execution_id}",
    response_model=APIResponse,
    response_model_exclude_none=True,
    responses={
        400: {"model": APIError, "description": "Bad request"},
        404: {"model": APIError, "description": "Onboarding execution not found"},
        500: {"model": APIError, "description": "Internal server error"},
    },
)
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
        # TODO: Remove region hardcoding if in future the Step Function is multi-region
        execution_arn = f"arn:aws:states:us-east-2:{os.environ['ACCOUNT_NUMBER']}:execution:league-onboarding:{onboarding_execution_id}"
        response = sfn.describe_execution(
            executionArn=execution_arn,
        )
        logger.info("Execution status: %s", response)
        api_response = {"execution_status": response["status"]}
        return APIResponse(
            message="success",
            detail="Successfully retrieved onboarding status",
            data=api_response,
        )
    except botocore.exceptions.ClientError as e:
        exception_mappings = {
            400: [
                "InvalidArn",
            ],
            404: [
                "ExecutionDoesNotExist",
            ],
        }
        status_messages = {
            400: "Bad request",
            404: "Resource not found",
            500: "Internal server error",
        }
        error_code = e.response.get("Error", {}).get("Code", "UnknownError")
        # TODO: turn this into a reusable function for the API
        for status_code, dynamo_errors in exception_mappings.items():
            if error_code in dynamo_errors:
                logger.exception("%d error", status_code)
                raise HTTPException(
                    status_code=status_code,
                    detail=APIError(
                        message="error",
                        detail=status_messages[status_code] + f" ({error_code})",
                    ).model_dump(),
                )
        logger.exception("Unexpected DynamoDB client error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                message="error", detail=status_messages[500] + f" ({error_code})"
            ).model_dump(),
        )
