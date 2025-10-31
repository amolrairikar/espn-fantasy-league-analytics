"""FastAPI router for league standings endpoints."""

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
    prefix="/standings",
    dependencies=[Depends(get_api_key)],
)


@router.get("", status_code=status.HTTP_200_OK)
def get_standings(
    league_id: str = Query(description="The ID of the league the matchup occurred in."),
    platform: str = Query(description="The platform the league is on (e.g., ESPN)."),
    standings_type: str = Query(
        description="The type of standings to pull (season, H2H, etc.)."
    ),
    season: Optional[str] = Query(
        default=None,
        description="The fantasy football season to get standings for. Only used for season standings_type.",
    ),
    team: Optional[str] = Query(
        default=None,
        description="The team to get standings across all seasons for. Only used for season standings_type.",
    ),
) -> APIResponse:
    """
    Endpoint to retrieve standings for a league.

    Args:
        league_id (str): The ID of the league the team is in.
        platform (str): The platform the league is on (e.g., ESPN).
        standings_type (str): The type of standings to pull (season, H2H, etc.).
        season (Optional[str]): The fantasy football season to get standings for. Only used for season standings_type.
        team (Optional[str]): The team to get standings across all seasons for. Only used for season standings_type.
    """
    try:
        if standings_type == "season":
            if not season and not team:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing `season` parameter which is required to pull season standings.",
                )
            if team:
                response = dynamodb_client.query(
                    TableName=table_name,
                    IndexName="GSI2",
                    KeyConditionExpression="GSI2PK = :pk AND begins_with(GSI2SK, :prefix)",
                    ExpressionAttributeValues={
                        ":pk": {"S": f"STANDINGS#SEASON#TEAM#{team}"},
                        ":prefix": {
                            "S": f"LEAGUE#{league_id}#PLATFORM#{platform}",
                        },
                    },
                )
                items = [
                    {
                        k: deserializer.deserialize(v)
                        for k, v in sorted(item.items())
                        if k not in ("PK", "SK") and not k.endswith(("PK", "SK"))
                    }
                    for item in response.get("Items", [])
                ]
                return APIResponse(
                    detail=f"Found season standings for team {team}",
                    data=items,
                )
            response = dynamodb_client.query(
                TableName=table_name,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
                ExpressionAttributeValues={
                    ":pk": {
                        "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"
                    },
                    ":prefix": {
                        "S": "STANDINGS#SEASON",
                    },
                },
            )
            items = [
                {
                    k: deserializer.deserialize(v)
                    for k, v in sorted(item.items())
                    if k not in ("PK", "SK") and not k.endswith(("PK", "SK"))
                }
                for item in response.get("Items", [])
            ]
            return APIResponse(
                detail=f"Found season standings for {season} season",
                data=items,
            )
        elif standings_type == "h2h":
            response = dynamodb_client.query(
                TableName=table_name,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
                    ":prefix": {
                        "S": "STANDINGS#H2H",
                    },
                },
            )
            items = [
                {
                    k: deserializer.deserialize(v)
                    for k, v in sorted(item.items())
                    if k not in ("PK", "SK") and not k.endswith(("PK", "SK"))
                }
                for item in response.get("Items", [])
            ]
            return APIResponse(
                detail="Found H2H standings",
                data=items,
            )
        elif standings_type == "all_time":
            response = dynamodb_client.query(
                TableName=table_name,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
                    ":prefix": {
                        "S": "STANDINGS#ALL-TIME#",
                    },
                },
            )
            items = [
                {
                    k: deserializer.deserialize(v)
                    for k, v in sorted(item.items())
                    if k not in ("PK", "SK") and not k.endswith(("PK", "SK"))
                }
                for item in response.get("Items", [])
            ]
            return APIResponse(
                detail=f"Found all-time standings for {len(items)} teams",
                data=items,
            )
        elif standings_type == "playoff":
            response = dynamodb_client.query(
                TableName=table_name,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
                ExpressionAttributeValues={
                    ":pk": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
                    ":prefix": {
                        "S": "STANDINGS#ALL-TIME-PLAYOFFS#",
                    },
                },
            )
            items = [
                {
                    k: deserializer.deserialize(v)
                    for k, v in sorted(item.items())
                    if k not in ("PK", "SK") and not k.endswith(("PK", "SK"))
                }
                for item in response.get("Items", [])
            ]
            return APIResponse(
                detail=f"Found all-time standings for {len(items)} teams",
                data=items,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid standings_type. Should be one of all_time, h2h, playoff, or season",
            )
    except botocore.exceptions.ClientError as e:
        logger.exception("Unexpected error while getting standings")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
