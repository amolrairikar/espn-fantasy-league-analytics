"""FastAPI router for league team endpoints."""

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
    prefix="/members",
    dependencies=[Depends(get_api_key)],
)


@router.get("", status_code=status.HTTP_200_OK)
def get_members(
    league_id: str = Query(description="The ID of the league."),
    platform: str = Query(description="The platform the league is on (e.g., ESPN)."),
) -> APIResponse:
    """
    Endpoint to retrieve all unique members for a league.

    Args:
        team_id (str): The ID of the team to retrieve metadata for.
        league_id (str): The ID of the league the team is in.
    """
    try:
        response = dynamodb_client.query(
            TableName=table_name,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}"},
                ":prefix": {
                    "S": "MEMBERS",
                },
            },
        )
        items = [
            {k: deserializer.deserialize(v) for k, v in item.items()}
            for item in response.get("Items", [])
        ]
        return APIResponse(
            detail=f"Found {len(items)} total unique members for league",
            data=items,
        )
    except botocore.exceptions.ClientError as e:
        logger.exception("Unexpected error fetching unique members")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
