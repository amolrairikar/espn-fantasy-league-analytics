"""FastAPI router for league draft endpoints."""

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
    prefix="/draft-results",
    dependencies=[Depends(get_api_key)],
)


@router.get("", status_code=status.HTTP_200_OK)
def get_draft_results(
    league_id: str = Query(description="The ID of the league."),
    platform: str = Query(description="The platform the league is on (e.g., ESPN)."),
    season: str = Query(description="The fantasy football season year."),
) -> APIResponse:
    """
    Endpoint to retrieve draft results from a season for a league.

    Args:
        league_id (str): The ID of the league the team is in.
        platform (str): The platform the league is on (e.g., ESPN).
        season (str): The fantasy football season year.
    """
    try:
        response = dynamodb_client.query(
            TableName=table_name,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"},
                ":prefix": {
                    "S": "DRAFT#",
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
            detail=f"Fetched draft results for {season} season",
            data=items,
        )
    except botocore.exceptions.ClientError as e:
        logger.exception("Unexpected error fetching draft results")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
