"""FastAPI router for league team endpoints."""

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
    prefix="/teams",
    dependencies=[Depends(get_api_key)],
)


@router.get(
    "/",
    response_model=APIResponse,
    response_model_exclude_none=True,
    responses={
        404: {"model": APIError, "description": "Team(s) not found"},
        429: {"model": APIError, "description": "Too many requests"},
        500: {"model": APIError, "description": "Internal server error"},
    },
)
def get_teams(
    league_id: str = Query(description="The ID of the league the team is in."),
    platform: str = Query(
        description="The platform the league is on (e.g., ESPN, Sleeper)."
    ),
    season: str = Query(description="The fantasy football season year."),
    team_id: Optional[str] = Query(
        None, description="The ID of the team to retrieve metadata for."
    ),
) -> APIResponse:
    """
    Endpoint to retrieve team(s) for a league.

    Args:
        team_id (str): The ID of the team to retrieve metadata for.
        league_id (str): The ID of the league the team is in.
        platform (str): The platform the league is on (e.g., ESPN, Sleeper).
        season (str): The fantasy football season year.
    """
    try:
        if team_id:
            response = dynamodb_client.get_item(
                TableName=table_name,
                Key={
                    "PK": {
                        "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"
                    },
                    "SK": {"S": f"TEAM#{team_id}"},
                },
            )
            if "Item" in response:
                item = {
                    k: deserializer.deserialize(v) for k, v in response["Item"].items()
                }
                return APIResponse(
                    message="success",
                    detail=f"Team with ID {team_id} found.",
                    data=item,
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=APIError(
                        message="error", detail="Team ID not found"
                    ).model_dump(),
                )
        else:
            response = dynamodb_client.query(
                TableName=table_name,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
                ExpressionAttributeValues={
                    ":pk": {
                        "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"
                    },
                    ":prefix": {"S": "TEAM#"},
                },
            )
            items = [
                {k: deserializer.deserialize(v) for k, v in item.items()}
                for item in response.get("Items", [])
            ]
            if not items:
                raise HTTPException(
                    status_code=404,
                    detail=APIError(
                        message="error", detail="Teams not found"
                    ).model_dump(),
                )
            return APIResponse(
                message="success",
                detail="Found teams",
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
