"""FastAPI router for league standings endpoints."""

from typing import Any, Callable, Optional

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
    prefix="/standings",
    dependencies=[Depends(get_api_key)],
)


def deserialize_items(items: list[dict]) -> list[dict]:
    """
    Helper function to deserialize DynamoDB items.

    Args:
        items (list[dict]): List of DynamoDB items.

    Returns:
        list[dict]: List of deserialized items.
    """
    return [
        {
            k: deserializer.deserialize(v)
            for k, v in item.items()
            if k not in ("PK", "SK") and not k.endswith(("PK", "SK"))
        }
        for item in items
    ]


def get_season_standings_one_team(
    league_id: str,
    platform: str,
    team: str,
    **_,
):
    """
    Get season standings for one team across all seasons.

    Args:
        league_id (str): The ID of the league.
        platform (str): The platform the league is on (e.g., ESPN).
        team (str): The ID of the team to get standings for.

    Returns:
        APIResponse: The API response containing the standings data.
    """
    pk = f"LEAGUE#{league_id}#PLATFORM#{platform}#STANDINGS#SEASON#TEAM#{team}"
    sk = "SEASON#"
    response = dynamodb_client.query(
        TableName=table_name,
        IndexName="GSI2",
        KeyConditionExpression="GSI2PK = :pk AND begins_with(GSI2SK, :sk_prefix)",
        ExpressionAttributeValues={":pk": {"S": pk}, ":sk_prefix": {"S": sk}},
    )
    items = deserialize_items(response.get("Items", []))
    return APIResponse(
        detail=f"Found standings for team {team}",
        data=items,
    )


def get_standings_for_season(
    league_id: str,
    platform: str,
    season: str,
    **_,
):
    """
    Get season standings for all teams in a single season.

    Args:
        league_id (str): The ID of the league.
        platform (str): The platform the league is on (e.g., ESPN).
        season (str): The season to get standings for.

    Returns:
        APIResponse: The API response containing the standings data.
    """
    pk = f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"
    sk = "STANDINGS#SEASON#"
    response = dynamodb_client.query(
        TableName=table_name,
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={":pk": {"S": pk}, ":sk_prefix": {"S": sk}},
    )
    items = deserialize_items(response.get("Items", []))
    return APIResponse(
        detail=f"Found standings for {season} season",
        data=items,
    )


def get_head_to_head_standings(
    league_id: str,
    platform: str,
    **_,
):
    """
    Get head-to-head standings for all teams.

    Args:
        league_id (str): The ID of the league.
        platform (str): The platform the league is on (e.g., ESPN).

    Returns:
        APIResponse: The API response containing the standings data.
    """
    pk = f"LEAGUE#{league_id}#PLATFORM#{platform}"
    sk = "STANDINGS#H2H"
    response = dynamodb_client.query(
        TableName=table_name,
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={":pk": {"S": pk}, ":sk_prefix": {"S": sk}},
    )
    items = deserialize_items(response.get("Items", []))
    return APIResponse(
        detail="Found head to head standings",
        data=items,
    )


def get_all_time_standings(
    league_id: str,
    platform: str,
    **_,
):
    """
    Get all-time standings for the fantasy league.

    Args:
        league_id (str): The ID of the league.
        platform (str): The platform the league is on (e.g., ESPN).

    Returns:
        APIResponse: The API response containing the standings data.
    """
    pk = f"LEAGUE#{league_id}#PLATFORM#{platform}"
    sk = "STANDINGS#ALL-TIME#"
    response = dynamodb_client.query(
        TableName=table_name,
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={":pk": {"S": pk}, ":sk_prefix": {"S": sk}},
    )
    items = deserialize_items(response.get("Items", []))
    return APIResponse(
        detail="Found all-time standings",
        data=items,
    )


def get_playoff_standings(
    league_id: str,
    platform: str,
    **_,
):
    """
    Get all-time playoff standings for the fantasy league.

    Args:
        league_id (str): The ID of the league.
        platform (str): The platform the league is on (e.g., ESPN).

    Returns:
        APIResponse: The API response containing the standings data.
    """
    pk = f"LEAGUE#{league_id}#PLATFORM#{platform}"
    sk = "STANDINGS#ALL-TIME-PLAYOFFS#"
    response = dynamodb_client.query(
        TableName=table_name,
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={":pk": {"S": pk}, ":sk_prefix": {"S": sk}},
    )
    items = deserialize_items(response.get("Items", []))
    return APIResponse(
        detail="Found playoff standings",
        data=items,
    )


def get_weekly_standings_single_team(
    league_id: str,
    platform: str,
    season: str,
    team: str,
    week: str,
    **_,
):
    """
    Get weekly standings for a given team, season, and week.

    Args:
        league_id (str): The ID of the league.
        platform (str): The platform the league is on (e.g., ESPN).
        season (str): The season to get standings for.
        week (str): The week number to get standings for.

    Returns:
        APIResponse: The API response containing the standings data.
    """
    pk = f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}#WEEK#{week}"
    sk = f"STANDINGS#WEEKLY#{team}"
    response = dynamodb_client.query(
        TableName=table_name,
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={":pk": {"S": pk}, ":sk_prefix": {"S": sk}},
    )
    items = deserialize_items(response.get("Items", []))
    return APIResponse(
        detail="Found weekly standings",
        data=items,
    )


QUERY_HANDLERS: dict[tuple[str, bool, bool, bool], Callable[..., Any]] = {
    # (standings_type, season, team)
    ("season", False, True, False): get_season_standings_one_team,
    ("season", True, False, False): get_standings_for_season,
    ("h2h", False, False, False): get_head_to_head_standings,
    ("all_time", False, False, False): get_all_time_standings,
    ("playoffs", False, False, False): get_playoff_standings,
    ("weekly", True, True, True): get_weekly_standings_single_team,
}


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
    week: Optional[int] = Query(
        default=None,
        description="The week number to get weekly standings for. Only used for weekly standings_type.",
    ),
):
    """
    Endpoint to retrieve standings for a league.

    Args:
        league_id (str): The ID of the league the team is in.
        platform (str): The platform the league is on (e.g., ESPN).
        standings_type (str): The type of standings to pull (season, H2H, etc.).
        season (Optional[str]): The fantasy football season to get standings for. Only used for season standings_type.
        team (Optional[str]): The team to get standings across all seasons for. Only used for season standings_type.
    """
    key = (standings_type, bool(season), bool(team), bool(week))
    handler = QUERY_HANDLERS.get(key)
    if not handler:
        log_message = (
            f"Invalid combination of query parameters: "
            f"standings_type={standings_type}, season={season}, team={team}"
        )
        logger.error(log_message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=log_message)

    return query_with_handling(
        handler,
        league_id=league_id,
        platform=platform,
        standings_type=standings_type,
        season=season,
        team=team,
        week=week,
    )
