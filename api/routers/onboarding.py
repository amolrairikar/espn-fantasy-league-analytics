"""FastAPI router for league onboarding (via Step Functions) endpoints."""

import json

import boto3
import botocore.exceptions
from fastapi import APIRouter, Body, Depends, HTTPException, status

from api.dependencies import (
    ENVIRONMENT,
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
    Onboards a league by triggering a Lambda execution that retrieves league
    data such as matchups, scores, etc.

    Args:
        league_id (str): ID of league to onboard.
        data (LeagueMetadata): The league information (ID, cookies, platform) required for onboarding.

    Returns:
        APIResponse: A JSON response with a message field indicating success/failure
            and an optional data field to capture additional details.

    Raises:
        HTTPException: 500 error if the onboarding lambda fails.
    """
    lambda_client = boto3.client("lambda")
    try:
        event_input = {
            "event-id": "",
            "body": {
                "leagueId": data.league_id,
                "platform": data.platform,
                "swidCookie": data.swid,
                "espnS2Cookie": data.espn_s2,
                "seasons": data.seasons,
            },
        }
        env_add_on = "-dev" if ENVIRONMENT == "DEV" else ""
        response = lambda_client.invoke(
            FunctionName=f"fantasy-recap-league-onboarding-lambda{env_add_on}",
            InvocationType="RequestResponse",
            LogType="Tail",
            Payload=json.dumps(event_input),
        )
        response_payload = json.loads(response["Payload"].read().decode("utf-8"))
        if (
            "FunctionError" not in response_payload
            and response_payload["status"] == "success"
        ):
            return APIResponse(detail="Successfully onboarded league")
        else:
            error_detail = response_payload["FunctionError"]
            error_message = f"Error occurred while onboarding league: {error_detail}"
            logger.exception(error_message)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_message,
            )
    except botocore.exceptions.ClientError as e:
        logger.exception("Unexpected error while triggering Step Function")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
