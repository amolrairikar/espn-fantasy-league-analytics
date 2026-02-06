"""FastAPI router for all-time league records endpoint."""

from fastapi import APIRouter, Depends, Query, status

from api.dependencies import (
    get_api_key,
    query_dynamodb,
)
from api.models import APIResponse

router = APIRouter(
    prefix="/alltime_records",
    dependencies=[Depends(get_api_key)],
)

RECORD_TYPE_MAPPING: dict[str, str] = {
    "all_time_championships": "CHAMPIONSHIPS",
    "top_10_team_scores": "TOP10TEAMSCORES",
    "bottom_10_team_scores": "BOTTOM10TEAMSCORES",
    "top_10_qb_scores": "TOP10PERFORMANCES#QB",
    "top_10_rb_scores": "TOP10PERFORMANCES#RB",
    "top_10_wr_scores": "TOP10PERFORMANCES#WR",
    "top_10_te_scores": "TOP10PERFORMANCES#TE",
    "top_10_dst_scores": "TOP10PERFORMANCES#DST",
    "top_10_k_scores": "TOP10PERFORMANCES#K",
}


@router.get("", status_code=status.HTTP_200_OK)
def get_alltime_records(
    league_id: str = Query(description="The ID of the league the matchup occurred in."),
    platform: str = Query(description="The platform the league is on (e.g., ESPN)."),
    record_type: str = Query(description="The type of all-time record to retrieve."),
) -> APIResponse:
    """
    Endpoint to retrieve all-time league records.

    Args:
        league_id (str): The ID of the league the team is in.
        platform (str): The platform the league is on (e.g., ESPN).
        record_type (str): The type of all-time record to retrieve.
    """
    return query_dynamodb(
        pk=f"LEAGUE#{league_id}#PLATFORM#{platform}",
        sk_prefix=f"HALL_OF_FAME#{RECORD_TYPE_MAPPING[record_type]}#",
    )
