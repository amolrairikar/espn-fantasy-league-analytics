"""FastAPI router for league onboarding (via Step Functions) endpoints."""

import json

import boto3
import botocore.exceptions
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from api.dependencies import (
    ENVIRONMENT,
    logger,
    verify_espn_access,
)
from api.models import APIResponse, LeagueMetadata

router = APIRouter(
    prefix="/onboard",
    dependencies=[
        Depends(verify_espn_access),
    ],
)


@router.post("", status_code=status.HTTP_201_CREATED)
def onboard_league(
    data: LeagueMetadata = Body(
        description="The league information (ID, cookies, platform) required for onboarding."
    ),
    league_id: str = Query(description="Unique ID for the league."),
    season: str = Query(description="Season to validate league information for."),
    swid_cookie: str = Query(
        default=None, description="SWID cookie from browser cookies."
    ),
    espn_s2_cookie: str = Query(
        default=None, description="ESPN S2 cookie from browser cookies."
    ),
) -> APIResponse:
    """
    Onboards a league by triggering a Lambda execution that retrieves league
    data such as matchups, scores, etc.

    Args:
        data (LeagueMetadata): The league information (ID, cookies, platform) required for onboarding.
        league_id (str): Unique ID for the league.
        season (str): Season to validate league information for.
        swid_cookie (str): SWID cookie from browser cookies.
        espn_s2_cookie (str): ESPN S2 cookie from browser cookies.

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
        logger.exception("Unexpected error while onboarding league")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
