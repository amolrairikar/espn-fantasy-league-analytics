"""FastAPI router for league metadata endpoints."""

from typing import Optional

import botocore.exceptions
import requests
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from api.dependencies import (
    build_api_request_headers,
    deserializer,
    dynamodb_client,
    get_api_key,
    table_name,
    logger,
)
from api.models import APIResponse, LeagueMetadata

router = APIRouter(
    prefix="/leagues",
    dependencies=[Depends(get_api_key)],
)


@router.get(
    "/validate", status_code=status.HTTP_200_OK, response_model_exclude_none=True
)
def validate_league_info(
    league_id: str = Query(description="Unique ID for the league."),
    platform: str = Query(description="Platform the fantasy league is on."),
    privacy: str = Query(description="League privacy settings (public/private)."),
    season: str = Query(description="Season to validate league information for."),
    swid_cookie: Optional[str] = Query(
        default=None, description="League privacy settings (public/private)."
    ),
    espn_s2_cookie: Optional[str] = Query(
        default=None, description="League privacy settings (public/private)."
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
    if platform == "ESPN":
        logger.info("Validating ESPN league")
        url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}"
        headers = build_api_request_headers(
            privacy=privacy,
            cookies={
                "swid": swid_cookie,
                "espn_s2": espn_s2_cookie,
            },
        )
        logger.info("API headers: %s", headers)
        try:
            response = requests.get(url=url, headers=headers)
            response.raise_for_status()
            log_message = "League information validated successfully."
            logger.info(log_message)
            return APIResponse(detail=log_message)
        except requests.RequestException as e:
            status_code = getattr(e.response, "status_code", None)
            errors = {
                400: "Bad request",
                401: "Unauthorized",
                404: "League ID not found",
            }
            if status_code in errors:
                error_message = errors[status_code]
                logger.exception(error_message)
                raise HTTPException(
                    status_code=status_code,
                    detail=str(e),
                )
            else:
                logger.exception(
                    "Unexpected error while validating league information."
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Internal server error: {str(e)}",
                )
    else:
        log_message = "Platforms besides ESPN not currently supported."
        logger.warning(log_message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=log_message,
        )


@router.get("/{league_id}", status_code=status.HTTP_200_OK)
def get_league_metadata(
    league_id: str = Path(description="The ID of the league to retrieve metadata for."),
    platform: str = Query(description="The platform the league is on (e.g., ESPN)."),
) -> APIResponse:
    """
    Endpoint to check metadata for a league.

    Args:
        league_id (str): The ID of the league to retrieve metadata for.
        platform (str): The platform the league is on (e.g., ESPN).

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
            item = {
                k: v
                for k, v in sorted(item.items())
                if k not in ("PK", "SK") and not k.endswith(("PK", "SK"))
            }

            # Sort the seasons for organizational purposes
            item["seasons"] = sorted(item["seasons"])
            logger.info("Retrieved item: %s", item)
            return APIResponse(detail=log_message, data=item)
        log_message = f"League with ID {league_id} not found in database."
        logger.warning(log_message)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=log_message,
        )
    except botocore.exceptions.ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.post("", status_code=status.HTTP_201_CREATED)
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
                "league_id": {"S": data.league_id},
                "platform": {"S": data.platform},
                "privacy": {"S": data.privacy},
                "espn_s2_cookie": {"S": data.espn_s2},
                "swid_cookie": {"S": data.swid},
                "seasons": {"SS": data.seasons},
            },
        )
        log_message = f"League with ID {data.league_id} added to database."
        logger.info(log_message)
        return APIResponse(detail=log_message)
    except botocore.exceptions.ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.put("/{league_id}", status_code=status.HTTP_201_CREATED)
def update_league_metadata(
    data: LeagueMetadata,
    league_id: str = Path(description="The ID of the league to retrieve metadata for."),
) -> APIResponse:
    """
    Endpoint to update metadata for a league.

    Args:
        data (LeagueMetadata): The JSON object containing updated league metadata.
        league_id (str): The ID of the league to update metadata for.

    Returns:
        APIResponse: A JSON response with a message field indicating success/failure
            and an optional data field to capture additional details.
    """
    try:
        dynamodb_client.put_item(
            TableName=table_name,
            Item={
                "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{data.platform}"},
                "SK": {"S": "METADATA"},
                "league_id": {"S": league_id},
                "platform": {"S": data.platform},
                "privacy": {"S": data.privacy},
                "espn_s2_cookie": {"S": data.espn_s2},
                "swid_cookie": {"S": data.swid},
                "seasons": {"SS": data.seasons},
                "onboarded_date": {"S": data.onboarded_date},
                "onboarded_status": {"BOOL": True},
            },
        )
        log_message = f"League with ID {data.league_id} updated in database."
        logger.info(log_message)
        return APIResponse(detail=log_message)
    except botocore.exceptions.ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
