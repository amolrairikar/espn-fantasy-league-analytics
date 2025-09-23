"""FastAPI router for league matchup endpoints."""

from typing import Optional

import botocore.exceptions
from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import (
    deserializer,
    dynamodb_client,
    get_api_key,
    table_name,
    logger,
)
from api.models import APIError, APIResponse

router = APIRouter(
    prefix="/matchups",
    dependencies=[Depends(get_api_key)],
)


@router.get(
    "/",
    response_model=APIResponse,
    response_model_exclude_none=True,
    responses={
        404: {"model": APIError, "description": "Matchup(s) not found"},
        429: {"model": APIError, "description": "Too many requests"},
        500: {"model": APIError, "description": "Internal server error"},
    },
)
def get_matchups(
    team1_id: str = Query(description="The ID of team 1 in the matchup."),
    team2_id: str = Query(description="The ID of team 2 in the matchup."),
    league_id: str = Query(
        None, description="The ID of the league the matchup occurred in."
    ),
    platform: str = Query(
        description="The platform the league is on (e.g., ESPN, Sleeper)."
    ),
    week_number: Optional[str] = Query(
        None, description="The week the matchup occurred in."
    ),
    season: Optional[str] = Query(
        None, description="The fantasy football season year."
    ),
) -> APIResponse:
    """
    Endpoint to retrieve matchup(s) for a league.

    Args:
        team1_id (str): The ID of team 1 in the matchup.
        team2_id (str): The ID of team 2 in the matchup.
        week_number (str): The week the matchup occurred in.
        league_id (str): The ID of the league the team is in.
        platform (str): The platform the league is on (e.g., ESPN, Sleeper).
        season (str): The fantasy football season year.
    """
    try:
        # Get a specific matchup
        if week_number and season:
            response = dynamodb_client.query(
                TableName=table_name,
                KeyConditionExpression="PK = :pk AND SK = :sk",
                ExpressionAttributeValues={
                    ":pk": {
                        "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"
                    },
                    ":sk": {
                        "S": f"MATCHUP#{team1_id}-vs-{team2_id}#WEEK#{week_number}"
                    },
                },
            )
            logger.info(
                "Found matchup between team %s and team %s for season %s week %s",
                team1_id,
                team2_id,
                season,
                week_number,
            )
            items = [
                {k: deserializer.deserialize(v) for k, v in item.items()}
                for item in response.get("Items", [])
            ]
            if not items:
                raise HTTPException(
                    status_code=404,
                    detail=APIError(
                        message="error", detail="Matchups not found"
                    ).model_dump(),
                )
            return APIResponse(
                message="success",
                detail="Found matchups",
                data=items,
            )
        # Get all matchups in a season
        elif not week_number and season:
            response = dynamodb_client.query(
                TableName=table_name,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
                ExpressionAttributeValues={
                    ":pk": {
                        "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"
                    },
                    ":prefix": {"S": f"MATCHUP#{team1_id}-vs-{team2_id}"},
                },
            )
            logger.info(
                "Found %d total matchups between team %s and team %s for %s season",
                len(response["Items"]),
                team1_id,
                team2_id,
                season,
            )
            logger.info("Response: %s", response)
            items = [
                {k: deserializer.deserialize(v) for k, v in item.items()}
                for item in response.get("Items", [])
            ]
            logger.info("Items: %s", items)
            if not items:
                raise HTTPException(
                    status_code=404,
                    detail=APIError(
                        message="error", detail="Matchups not found"
                    ).model_dump(),
                )
            return APIResponse(
                message="success",
                detail="Found matchups",
                data=items,
            )
        # Get all matchups across all seasons
        else:
            response = dynamodb_client.query(
                TableName=table_name,
                IndexName="GSI1",
                KeyConditionExpression="GSI1PK = :pk AND begins_with(GSI1SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"MATCHUP#{team1_id}-vs-{team2_id}"},
                    ":sk_prefix": {"S": f"LEAGUE#{league_id}"},
                },
            )
            logger.info(
                "Found %d matchups between team %s and team %s",
                len(response["Items"]),
                team1_id,
                team2_id,
            )
            items = [
                {k: deserializer.deserialize(v) for k, v in item.items()}
                for item in response.get("Items", [])
            ]
            if not items:
                raise HTTPException(
                    status_code=404,
                    detail=APIError(
                        message="error", detail="Matchups not found"
                    ).model_dump(),
                )
            return APIResponse(
                message="success",
                detail="Found matchups",
                data=items,
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
