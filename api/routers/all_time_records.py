"""FastAPI router for all-time league records endpoint."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import (
    deserializer,
    dynamodb_client,
    get_api_key,
    logger,
    table_name,
    query_with_handling,
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


def filter_dynamodb_response(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Filters and deserializes DynamoDB query response items.

    Args:
        response (dict): The raw response from DynamoDB.

    Returns:
        list[dict]: A list of deserialized items.
    """
    items = [
        {
            k: deserializer.deserialize(v)
            for k, v in sorted(item.items())
            if k not in ("PK", "SK") and not k.endswith(("PK", "SK"))
        }
        for item in response.get("Items", [])
    ]
    return items


def get_specific_alltime_record(
    league_id: str,
    platform: str,
    record_type: str,
):
    """
    Retrieve a specific type of all-time league record.

    Args:
        league_id (str): The ID of the league the team is in.
        platform (str): The platform the league is on (e.g., ESPN).
        record_type (str): The type of all-time record to retrieve.
    """
    logger.info("Retrieving %s", record_type)
    pk = f"LEAGUE#{league_id}#PLATFORM#{platform}"
    sk = f"HALL_OF_FAME#{RECORD_TYPE_MAPPING[record_type]}#"
    response = dynamodb_client.query(
        TableName=table_name,
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={
            ":pk": {"S": pk},
            ":sk_prefix": {"S": sk},
        },
    )
    items = filter_dynamodb_response(response=response)
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No entries found for record type {record_type}",
        )
    return APIResponse(
        detail=f"Found all-time records for {record_type}",
        data=items,
    )


@router.get("", status_code=status.HTTP_200_OK)
def get_alltime_records(
    league_id: str = Query(description="The ID of the league the matchup occurred in."),
    platform: str = Query(description="The platform the league is on (e.g., ESPN)."),
    record_type: str = Query(description="The type of all-time record to retrieve."),
):
    """
    Endpoint to retrieve all-time league records.

    Args:
        league_id (str): The ID of the league the team is in.
        platform (str): The platform the league is on (e.g., ESPN).
        record_type (str): The type of all-time record to retrieve.
    """
    return query_with_handling(
        get_specific_alltime_record,
        league_id=league_id,
        platform=platform,
        record_type=record_type,
    )
