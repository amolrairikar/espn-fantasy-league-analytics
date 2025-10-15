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
from api.models import APIError, APIResponse

router = APIRouter(
    prefix="/standings",
    dependencies=[Depends(get_api_key)],
)


@router.get("", status_code=status.HTTP_200_OK)
def get_matchups(
    league_id: str = Query(description="The ID of the league the matchup occurred in."),
    platform: str = Query(description="The platform the league is on (e.g., ESPN)."),
    season: Optional[str] = Query(
        default=None, description="The fantasy football season to get standings for."
    ),
    h2h_standings: Optional[str] = Query(
        default=None,
        description="Optional parameter indicating whether to pull H2H standings.",
    ),
) -> APIResponse:
    """
    Endpoint to retrieve standings for a league.

    Args:
        league_id (str): The ID of the league the team is in.
        platform (str): The platform the league is on (e.g., ESPN).
        season (Optional[str]): The fantasy football season to get standings for.
        h2h_standings (Optional[str]): Optional parameter indicating whether to pull H2H standings.
    """
    try:
        if season:
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
                {k: deserializer.deserialize(v) for k, v in item.items()}
                for item in response.get("Items", [])
            ]
            return APIResponse(
                status="success",
                detail=f"Found season standings for {season} season",
                data=items,
            )
        elif h2h_standings:
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
                {k: deserializer.deserialize(v) for k, v in item.items()}
                for item in response.get("Items", [])
            ]
            return APIResponse(
                status="success",
                detail="Found H2H standings",
                data=items,
            )
        response = dynamodb_client.query(
            TableName=table_name,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
                ":prefix": {
                    "S": "STANDINGS#ALL-TIME",
                },
            },
        )
        items = [
            {k: deserializer.deserialize(v) for k, v in item.items()}
            for item in response.get("Items", [])
        ]
        return APIResponse(
            status="success",
            detail=f"Found all-time standings for {len(items)} teams",
            data=items,
        )
    except botocore.exceptions.ClientError as e:
        logger.exception("Unexpected error while getting standings")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                status="error",
                detail="Internal server error",
                developer_detail=str(e),
            ).model_dump(),
        )
