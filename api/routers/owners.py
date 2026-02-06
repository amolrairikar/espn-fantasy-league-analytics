"""FastAPI router for league team endpoints."""

from fastapi import APIRouter, Depends, Query, status

from api.dependencies import (
    get_api_key,
    query_dynamodb,
)
from api.models import APIResponse

router = APIRouter(
    prefix="/owners",
    dependencies=[Depends(get_api_key)],
)


@router.get("", status_code=status.HTTP_200_OK)
def get_owners(
    league_id: str = Query(description="The ID of the league."),
    platform: str = Query(description="The platform the league is on (e.g., ESPN)."),
) -> APIResponse:
    """
    Endpoint to retrieve all unique owners for a league.

    Args:
        team_id (str): The ID of the team to retrieve metadata for.
        league_id (str): The ID of the league the team is in.
    """
    return query_dynamodb(
        pk=f"LEAGUE#{league_id}#PLATFORM#{platform}",
        sk_prefix="OWNERS",
    )
