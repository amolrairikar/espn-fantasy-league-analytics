"""FastAPI router for league draft endpoints."""

from fastapi import APIRouter, Depends, Query, status

from api.dependencies import (
    get_api_key,
    query_dynamodb,
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
    return query_dynamodb(
        pk=f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}",
        sk_prefix="DRAFT#",
    )
