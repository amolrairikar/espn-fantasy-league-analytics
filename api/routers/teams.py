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
from api.models import APIResponse

router = APIRouter(
    prefix="/teams",
    dependencies=[Depends(get_api_key)],
)


@router.get("", status_code=status.HTTP_200_OK)
def get_teams(
    league_id: str = Query(description="The ID of the league the team is in."),
    platform: str = Query(description="The platform the league is on (e.g., ESPN)."),
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
        platform (str): The platform the league is on (e.g., ESPN).
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
                    detail=f"Team with ID {team_id} found in league {league_id} for {season} season",
                    data=item,
                )
            else:
                log_message = f"Team with ID {team_id} not found in league {league_id} for {season} season"
                logger.warning(log_message)
                raise HTTPException(
                    status_code=404,
                    detail=log_message,
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
                log_message = (
                    f"No teams found in league {league_id} for {season} season"
                )
                logger.warning(log_message)
                raise HTTPException(
                    status_code=404,
                    detail=log_message,
                )
            return APIResponse(
                detail=f"Found teams for league {league_id} for {season} season",
                data=items,
            )
    except botocore.exceptions.ClientError as e:
        logger.exception("Unexpected error fetching team(s)")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
