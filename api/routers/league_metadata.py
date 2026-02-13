"""FastAPI router for league metadata endpoints."""

from collections import OrderedDict

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


def validate_espn_credentials(
    league_id: str,
    season: str,
    swid_cookie: str,
    espn_s2_cookie: str,
) -> None:
    """
    Validates ESPN credentials by executing a simple Fantasy Football API request.

    Args:
        league_id (str): Unique ID for the league.
        season (str): Season to validate league information for.
        swid_cookie (str): SWID cookie from browser cookies.
        espn_s2_cookie (str): ESPN S2 cookie from browser cookies.
    """
    url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}"
    headers = {}
    headers = build_api_request_headers(
        cookies={
            "swid": swid_cookie,
            "espn_s2": espn_s2_cookie,
        },
    )
    logger.info("API headers: %s", headers)
    response = requests.get(url=url, headers=headers)
    response.raise_for_status()


@router.get(
    "/validate", status_code=status.HTTP_200_OK, response_model_exclude_none=True
)
def validate_league_info(
    league_id: str = Query(description="Unique ID for the league."),
    platform: str = Query(description="Platform the fantasy league is on."),
    season: str = Query(description="Season to validate league information for."),
    swid_cookie: str = Query(
        default=None, description="SWID cookie from browser cookies."
    ),
    espn_s2_cookie: str = Query(
        default=None, description="ESPN S2 cookie from browser cookies."
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
        try:
            logger.info("Validating ESPN league")
            validate_espn_credentials(
                league_id=league_id,
                season=season,
                swid_cookie=swid_cookie,
                espn_s2_cookie=espn_s2_cookie,
            )
            log_message = "League information validated successfully."
            logger.info(log_message)
            return APIResponse(detail=log_message)
        except requests.RequestException as e:
            status_code = getattr(e.response, "status_code", None)
            if not status_code:
                logger.exception(
                    "Unexpected error while validating league information."
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Internal server error: {str(e)}",
                )
            logger.exception("Error validating league: %s", str(e))
            raise HTTPException(
                status_code=status_code,
                detail=str(e),
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
                for k, v in item.items()
                if k not in ("PK", "SK") and not k.endswith(("PK", "SK"))
            }

            # Sort the seasons for organizational purposes
            item["seasons"] = sorted(item["seasons"])
            logger.info("Retrieved item: %s", item)

            # Order response for API
            ordered_item = OrderedDict()
            ordered_item["league_id"] = item["league_id"]
            ordered_item["platform"] = item["platform"]
            ordered_item["espn_s2_cookie"] = item["espn_s2_cookie"]
            ordered_item["swid_cookie"] = item["swid_cookie"]
            ordered_item["seasons"] = item["seasons"]
            ordered_item["onboarded_status"] = item.get("onboarded_status", "")
            ordered_item["onboarded_date"] = item.get("onboarded_date", "")
            return APIResponse(detail=log_message, data=ordered_item)
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
                "GSI5PK": {"S": f"LEAGUE#{data.league_id}"},
                "GSI5SK": {"S": "FOR_DELETION_USE_ONLY"},
                "league_id": {"S": data.league_id},
                "platform": {"S": data.platform},
                "espn_s2_cookie": {"S": data.espn_s2},
                "swid_cookie": {"S": data.swid},
                "seasons": {"SS": data.seasons},
            },
            ConditionExpression="attribute_not_exists(PK)",
        )
        log_message = f"League with ID {data.league_id} added to database."
        logger.info(log_message)
        return APIResponse(detail=log_message)
    except botocore.exceptions.ClientError as e:
        error_response = e.response.get("Error", {})
        error_code = error_response.get("Code")
        if error_code == "ConditionalCheckFailedException":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"League with ID {data.league_id} already exists.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.patch("/{league_id}", status_code=status.HTTP_200_OK)
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
        dynamodb_client.update_item(
            TableName=table_name,
            Key={
                "PK": {"S": f"LEAGUE#{league_id}#PLATFORM#{data.platform}"},
                "SK": {"S": "METADATA"},
            },
            UpdateExpression="SET onboarded_date = :date, onboarded_status = :status",
            ExpressionAttributeValues={
                ":date": {"S": data.onboarded_date},
                ":status": {"BOOL": True},
            },
            ReturnValues="UPDATED_NEW",
        )
        log_message = f"League with ID {data.league_id} updated in database."
        logger.info(log_message)
        return APIResponse(detail=log_message)
    except botocore.exceptions.ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
