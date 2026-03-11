"""FastAPI router for league onboarding (via Step Functions) endpoints."""

import os

import boto3
import botocore.exceptions
from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import (
    ENVIRONMENT,
    get_api_key,
    logger,
    verify_espn_access,
)
from api.models import APIResponse

router = APIRouter(
    prefix="/database",
    dependencies=[
        Depends(get_api_key),
        Depends(verify_espn_access),
    ],
)

s3_client = boto3.client("s3")
bucket_env_add = "-dev" if ENVIRONMENT == "DEV" else ""
BUCKET_NAME = (
    f"{os.environ['ACCOUNT_NUMBER']}-fantasy-recap-app-database{bucket_env_add}"
)


@router.get("", status_code=status.HTTP_200_OK)
def get_database(
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
    Fetches information about .duckdb database for the corresponding league_id.

    Args:
        league_id (str): Unique ID for the league.
        season (str): Season to validate league information for.
        swid_cookie (str): SWID cookie from browser cookies.
        espn_s2_cookie (str): ESPN S2 cookie from browser cookies.

    Returns:
        APIResponse: A JSON response with a message field indicating success/failure
            and a data field with .duckdb file information.

    Raises:
        HTTPException: 400 or 500 errors if an exception occurs.
    """
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": f"{league_id}.duckdb"},
            ExpiresIn=60,  # in seconds
        )
        db_file_metadata = s3_client.head_object(
            Bucket=BUCKET_NAME, Key=f"{league_id}.duckdb"
        )
        return APIResponse(
            detail="Found league database file",
            data={
                "url": url,
                "version": db_file_metadata["ETag"],
                "size": db_file_metadata["ContentLength"],
            },
        )
    except botocore.exceptions.ClientError as e:
        if e.response.get("Error", {}).get("Code", "") == "404":
            logger.error(
                "Object %s not found", f"s3://{BUCKET_NAME}/{league_id}.duckdb"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid league ID specified",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error fetching league database: {e}",
            )
