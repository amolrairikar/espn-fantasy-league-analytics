"""FastAPI router for league metadata endpoints."""

import datetime

import botocore.exceptions
import requests
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status

from api.dependencies import (
    build_api_request_headers,
    deserializer,
    dynamodb_client,
    get_api_key,
    table_name,
    logger,
)
from api.models import APIError, APIResponse, LeagueMetadata

router = APIRouter(
    prefix="/leagues",
    dependencies=[Depends(get_api_key)],
)


@router.post(
    "/validate/{season}",
    response_model=APIResponse,
    response_model_exclude_none=True,
    responses={
        400: {"model": APIError, "description": "Bad Request"},
        401: {"model": APIError, "description": "Unauthorized"},
        404: {"model": APIError, "description": "League ID not found"},
        500: {"model": APIError, "description": "Internal server error"},
    },
)
def validate_league_info(
    season: str = Path(description="Most recent active season for the league."),
    data: LeagueMetadata = Body(
        description="The league information (ID, cookies, platform) to validate."
    ),
) -> APIResponse:
    """
    Validates that the provided league information links to a valid league,
    and that cookie credentials work with API requests.

    Args:
        season (str): The most recent season the league was active for.
        data (LeagueMetadata): The league information (ID, cookies, platform) to validate.

    Returns:
        APIResponse: A JSON response with a message field indicating success/failure
            and an optional data field to capture additional details.

    Raises:
        HTTPException: 400, 401, 404, or 500 errors if an exception occurs.
    """
    url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{data.league_id}"
    headers = build_api_request_headers(data=data)
    try:
        response = requests.get(url=url, headers=headers)
        response.raise_for_status()
        log_message = "League information validated successfully."
        logger.info(log_message)
        return APIResponse(message="success", detail=log_message)
    except requests.RequestException as e:
        status_code = getattr(e.response, "status_code", None)
        errors = {
            400: "Bad request",
            401: "Unauthorized",
            404: "League ID not found",
        }
        if status_code in errors:
            error_message = errors[status_code]
            logger.error(error_message)
            raise HTTPException(
                status_code=status_code,
                detail=APIError(message="error", detail=error_message).model_dump(),
            )
        else:
            logger.exception("Unexpected error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=APIError(
                    message="error", detail="Internal server error"
                ).model_dump(),
            )


@router.get(
    "/{league_id}",
    response_model=APIResponse,
    response_model_exclude_none=True,
    responses={
        404: {"model": APIError, "description": "League ID not found"},
        429: {"model": APIError, "description": "Too many requests"},
        500: {"model": APIError, "description": "Internal server error"},
    },
)
def get_league_metadata(
    league_id: str = Path(description="The ID of the league to retrieve metadata for."),
    platform: str = Query(
        description="The platform the league is on (e.g., ESPN, Sleeper)."
    ),
) -> APIResponse:
    """
    Endpoint to check metadata for a league.

    Args:
        league_id (str): The ID of the league to retrieve metadata for.
        platform (str): The platform the league is on (e.g., ESPN, Sleeper)

    Returns:
        APIResponse: A JSON response with a message field indicating success/failure
            and a data field to return league metadata.

    Raises:
        HTTPException: 404 or 500 responses if an error occurs.
    """
    try:
        response = dynamodb_client.get_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
                "SK": {"S": "METADATA"},
            },
        )
        if "Item" in response:
            log_message = f"League with ID {league_id} found in database."
            logger.info(log_message)
            item = {k: deserializer.deserialize(v) for k, v in response["Item"].items()}
            logger.info("Retrieved item: %s", item)
            return APIResponse(message="success", detail=log_message, data=item)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=APIError(message="error", detail="League ID not found").model_dump(),
        )
    except botocore.exceptions.ClientError as e:
        exception_mappings = {
            404: [
                "ResourceNotFoundException",
            ],
            429: [
                "RequestLimitExceeded",
                "ThrottlingException",
            ],
        }
        status_messages = {
            404: "Resource not found",
            429: "Too many requests",
            500: "Internal server error",
        }
        error_code = e.response["Error"]["Code"]
        for status_code, dynamo_errors in exception_mappings.items():
            if error_code in dynamo_errors:
                logger.error("%d error: %s", status_code, e)
                raise HTTPException(
                    status_code=status_code,
                    detail=APIError(
                        message="error",
                        detail=status_messages[status_code] + f" ({error_code})",
                    ).model_dump(),
                )
        logger.error("Unexpected DynamoDB client error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                message="error", detail=status_messages[500] + f" ({error_code})"
            ).model_dump(),
        )


@router.post(
    "/",
    response_model=APIResponse,
    response_model_exclude_none=True,
    responses={
        404: {"model": APIError, "description": "Resource not found"},
        409: {"model": APIError, "description": "Request conflict"},
        429: {"model": APIError, "description": "Request limit exceeded"},
        500: {"model": APIError, "description": "Internal server error"},
    },
)
def post_league_metadata(data: LeagueMetadata) -> APIResponse:
    """
    Endpoint to create metadata for a league.

    Args:
        data (LeagueMetadata): The JSON object containing league metadata.

    Returns:
        APIResponse: A JSON response with a message field indicating success/failure
            and an optional data field to capture additional details.
    """
    try:
        dynamodb_client.put_item(
            TableName=table_name,
            Item={
                "PK": {"S": f"LEAGUE#{data.league_id}#PLATFORM#{data.platform}"},
                "SK": {"S": "METADATA"},
                "privacy": {"S": data.privacy},
                "espn_s2_cookie": {"S": data.espn_s2},
                "swid_cookie": {"S": data.swid},
                "onboarded_date": {
                    "S": datetime.datetime.now(tz=datetime.timezone.utc)
                    .isoformat(timespec="seconds")
                    .replace("+00:00", "Z")
                },
            },
        )
        log_message = f"League with ID {data.league_id} added to database."
        logger.info(log_message)
        return APIResponse(
            message="success",
            detail=log_message,
        )
    except botocore.exceptions.ClientError as e:
        exception_mappings = {
            404: [
                "ResourceNotFoundException",
            ],
            409: [
                "ConditionalCheckFailedException",
                "ItemCollectionSizeLimitExceededException",
                "TransactionConflictException",
            ],
            429: [
                "RequestLimitExceeded",
                "ThrottlingException",
            ],
        }
        status_messages = {
            404: "Resource not found",
            409: "Resource conflict",
            429: "Too many requests",
            500: "Internal server error",
        }
        error_code = e.response["Error"]["Code"]
        for status_code, dynamo_errors in exception_mappings.items():
            if error_code in dynamo_errors:
                logger.error("%d error: %s", status_code, e)
                raise HTTPException(
                    status_code=status_code,
                    detail=APIError(
                        message="error",
                        detail=status_messages[status_code] + f" ({error_code})",
                    ).model_dump(),
                )
        logger.error("Unexpected DynamoDB client error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                message="error", detail=status_messages[500] + f" ({error_code})"
            ).model_dump(),
        )
