"""FastAPI router for league onboarding (via Step Functions) endpoints."""

import json

import boto3
import botocore.exceptions
from fastapi import APIRouter, Body, HTTPException, status

from api.dependencies import (
    BUCKET_NAME,
    ENVIRONMENT,
    logger,
)
from api.models import APIResponse, LeagueMetadata

router = APIRouter(
    prefix="/onboard",
)

lambda_client = boto3.client("lambda")
s3_client = boto3.client("s3")


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
        data (LeagueMetadata): The league information (ID, cookies, platform) required for onboarding.

    Returns:
        APIResponse: A JSON response with a message field indicating success/failure
            and an optional data field to capture additional details.

    Raises:
        HTTPException: 500 error if the onboarding lambda fails.
    """
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
            # Generate presigned URL to S3 bucket with DuckDB file
            url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": BUCKET_NAME, "Key": f"{data.league_id}.duckdb"},
                ExpiresIn=60,  # in seconds
            )
            db_file_metadata = s3_client.head_object(
                Bucket=BUCKET_NAME, Key=f"{data.league_id}.duckdb"
            )
            return APIResponse(
                detail="Successfully onboarded league",
                data={
                    "url": url,
                    "version": db_file_metadata["ETag"],
                    "size": db_file_metadata["ContentLength"],
                },
            )
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
