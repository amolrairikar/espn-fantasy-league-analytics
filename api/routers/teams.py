"""FastAPI router for league team endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from api.dependencies import (
    get_api_key,
    query_dynamodb,
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
    if team_id:
        return query_dynamodb(
            pk=f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}",
            sk_prefix=f"TEAM#{team_id}",
        )
    return query_dynamodb(
        pk=f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}",
        sk_prefix="TEAM#",
    )
