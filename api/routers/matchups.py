"""FastAPI router for league matchup endpoints."""

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
    prefix="/matchups",
    dependencies=[Depends(get_api_key)],
)


def filter_dynamo_db_response(
    response: dict[str, Any], playoff_filter: str
) -> list[dict[str, Any]]:
    """Filter DynamoDB response based on playoff filter value.

    Args:
        response (dict[str, Any]): The DynamoDB response.
        playoff_filter (str): The playoff filter value (include, exclude, or only).

    Returns:
        list[dict[str, Any]]: The filtered list of items.
    """
    items = []
    if playoff_filter == "include":
        items = [
            {
                k: deserializer.deserialize(v)
                for k, v in sorted(item.items())
                if k not in ("PK", "SK") and not k.endswith(("PK", "SK"))
            }
            for item in response.get("Items", [])
        ]
    elif playoff_filter == "exclude":
        items = [
            {
                k: deserializer.deserialize(v)
                for k, v in sorted(item.items())
                if k not in ("PK", "SK") and not k.endswith(("PK", "SK"))
            }
            for item in response.get("Items", [])
            if item.get("playoff_tier_type", {}).get("S") == "NONE"
        ]
    elif playoff_filter == "only":
        items = [
            {
                k: deserializer.deserialize(v)
                for k, v in sorted(item.items())
                if k not in ("PK", "SK") and not k.endswith(("PK", "SK"))
            }
            for item in response.get("Items", [])
            if item.get("playoff_tier_type", {}).get("S") == "WINNERS_BRACKET"
        ]
    return items


def get_specific_matchup_two_teams(
    league_id: str,
    platform: str,
    playoff_filter: str,
    team1_id: str,
    team2_id: str,
    season: str,
    week_number: str,
) -> APIResponse:
    """
    Gets a specific matchups between two teams for a given season and week.

    Args:
        league_id (str): The ID of the league the matchup occurred in.
        platform (str): The platform the league is on (e.g., ESPN).
        playoff_filter (str): Filter value indicating whether to exclude,
            include, or only include playoff matchups.
        team1_id (str): The ID of team 1 in the matchup.
        team2_id (str): The ID of team 2 in the matchup.
        season (str): The fantasy football season year.
        week_number (str): The week the matchup occurred in.

    Returns:
        APIResponse: The API response with data.
    """
    logger.info(
        "Retrieving matchup between team %s and %s for %s season and week %s",
        team1_id,
        team2_id,
        season,
        week_number,
    )
    pk = f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"
    sks = [
        f"MATCHUP#TEAMS#{team1_id}-vs-{team2_id}#WEEK#{week_number}",
        f"MATCHUP#TEAMS#{team2_id}-vs-{team1_id}#WEEK#{week_number}",
    ]
    items = []
    for sk in sks:
        response = dynamodb_client.query(
            TableName=table_name,
            KeyConditionExpression="PK = :pk AND SK = :sk",
            ExpressionAttributeValues={":pk": {"S": pk}, ":sk": {"S": sk}},
        )
        items.extend(
            filter_dynamo_db_response(response=response, playoff_filter=playoff_filter)
        )

    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No matchup between {team1_id} and {team2_id} for {season} week {week_number}",
        )

    return APIResponse(
        detail=f"Found matchup between {team1_id} and {team2_id} for {season} week {week_number}",
        data=items,
    )


def get_specific_matchup_one_team(
    league_id: str,
    platform: str,
    playoff_filter: str,
    team1_id: str,
    season: str,
    week_number: str,
    **_,
) -> APIResponse:
    """
    Gets a specific matchups given one team ID for a given season and week.

    Args:
        league_id (str): The ID of the league the matchup occurred in.
        platform (str): The platform the league is on (e.g., ESPN).
        playoff_filter (str): Filter value indicating whether to exclude,
            include, or only include playoff matchups.
        team1_id (str): The ID of team 1 in the matchup.
        season (str): The fantasy football season year.
        week_number (str): The week the matchup occurred in.

    Returns:
        APIResponse: The API response with data.
    """
    logger.info(
        "Retrieving matchup for team %s for %s season and week %s",
        team1_id,
        season,
        week_number,
    )
    pk = f"LEAGUE#{league_id}#PLATFORM#{platform}#MATCHUP#TEAM#{team1_id}"
    sk = f"SEASON#{season}#WEEK#{week_number}"
    items = []
    response = dynamodb_client.query(
        TableName=table_name,
        IndexName="GSI4",
        KeyConditionExpression="GSI4PK = :pk AND GSI4SK = :sk",
        ExpressionAttributeValues={":pk": {"S": pk}, ":sk": {"S": sk}},
    )
    items.extend(
        filter_dynamo_db_response(response=response, playoff_filter=playoff_filter)
    )

    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No matchup for {team1_id} for {season} week {week_number}",
        )

    return APIResponse(
        detail=f"Found matchup for {team1_id} for {season} week {week_number}",
        data=items,
    )


def get_all_time_matchups(
    league_id: str,
    platform: str,
    playoff_filter: str,
    team1_id: str,
    team2_id: str,
    **_,
) -> APIResponse:
    """
    Gets all matchups between two teams.

    Args:
        league_id (str): The ID of the league the matchup occurred in.
        platform (str): The platform the league is on (e.g., ESPN).
        playoff_filter (str): Filter value indicating whether to exclude,
            include, or only include playoff matchups.
        team1_id (str): The ID of team 1 in the matchup.
        team2_id (str): The ID of team 2 in the matchup.

    Returns:
        APIResponse: The API response with data.
    """
    logger.info("Retrieving all matchups between %s and %s", team1_id, team2_id)

    pairs = [
        f"LEAGUE#{league_id}#PLATFORM#{platform}#MATCHUP#{team1_id}-vs-{team2_id}",
        f"LEAGUE#{league_id}#PLATFORM#{platform}#MATCHUP#{team2_id}-vs-{team1_id}",
    ]
    items = []

    for pk in pairs:
        response = dynamodb_client.query(
            TableName=table_name,
            IndexName="GSI1",
            KeyConditionExpression="GSI1PK = :pk AND begins_with(GSI1SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": pk},
                ":sk_prefix": {"S": "SEASON#"},
            },
        )
        items.extend(
            filter_dynamo_db_response(response=response, playoff_filter=playoff_filter)
        )

    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No matchups between {team1_id} and {team2_id}",
        )

    return APIResponse(
        detail=f"Found {len(items)} matchups between {team1_id} and {team2_id}",
        data=items,
    )


def get_weekly_matchups(
    league_id: str,
    platform: str,
    playoff_filter: str,
    season: str,
    week_number: str,
    **_,
):
    """
    Get all matchups for a given week and season combination.

    Args:
        league_id (str): The ID of the league the matchup occurred in.
        platform (str): The platform the league is on (e.g., ESPN).
        playoff_filter (str): Filter value indicating whether to exclude,
            include, or only include playoff matchups.
        season (str): The fantasy football season year.
        week_number (str): The week the matchup occurred in.

    Returns:
        APIResponse: The API response with data.
    """
    logger.info("Retrieving all matchups for %s season week %s", season, week_number)
    response = dynamodb_client.query(
        TableName=table_name,
        IndexName="GSI3",
        KeyConditionExpression="GSI3PK = :pk AND begins_with(GSI3SK, :sk_prefix)",
        ExpressionAttributeValues={
            ":pk": {
                "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}#WEEK#{week_number}"
            },
            ":sk_prefix": {"S": "MATCHUP#"},
        },
    )
    items = filter_dynamo_db_response(response=response, playoff_filter=playoff_filter)
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No matchups found for {season} season week {week_number}",
        )
    return APIResponse(
        detail=f"Found {len(items)} matchups for {season} season week {week_number}",
        data=items,
    )


def get_team_season_matchups(
    league_id: str,
    platform: str,
    playoff_filter: str,
    team1_id: str,
    season: str,
    **_,
) -> APIResponse:
    """
    Get all matchups for a team for a given season.

    Args:
        league_id (str): The ID of the league the matchup occurred in.
        platform (str): The platform the league is on (e.g., ESPN).
        playoff_filter (str): Filter value indicating whether to exclude,
            include, or only include playoff matchups.
        team1_id (str): The ID of team 1 in the matchup.
        season (str): The fantasy football season year.

    Returns:
        APIResponse: The API response with data.
    """
    logger.info("Retrieving all matchups for team %s in %s season", team1_id, season)
    pk = f"LEAGUE#{league_id}#PLATFORM#{platform}#MATCHUP#TEAM#{team1_id}"
    sk = f"SEASON#{season}#"
    response = dynamodb_client.query(
        TableName=table_name,
        IndexName="GSI4",
        KeyConditionExpression="GSI4PK = :pk AND begins_with(GSI4SK, :sk_prefix)",
        ExpressionAttributeValues={
            ":pk": {"S": pk},
            ":sk_prefix": {"S": sk},
        },
    )
    items = filter_dynamo_db_response(response=response, playoff_filter=playoff_filter)
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No matchups found for team {team1_id} in {season} season",
        )
    return APIResponse(
        detail=f"Found {len(items)} matchups for team {team1_id} in {season} season",
        data=items,
    )


def get_team_all_time_matchups(
    league_id: str,
    platform: str,
    playoff_filter: str,
    team1_id: str,
    **_,
) -> APIResponse:
    """
    Get all matchups for a team across all seasons.

    Args:
        league_id (str): The ID of the league the matchup occurred in.
        platform (str): The platform the league is on (e.g., ESPN).
        playoff_filter (str): Filter value indicating whether to exclude,
            include, or only include playoff matchups.
        team1_id (str): The ID of team 1 in the matchup.

    Returns:
        APIResponse: The API response with data.
    """
    logger.info("Retrieving all matchups for team %s across all seasons", team1_id)
    response = dynamodb_client.query(
        TableName=table_name,
        IndexName="GSI4",
        KeyConditionExpression="GSI4PK = :pk AND begins_with(GSI4SK, :sk_prefix)",
        ExpressionAttributeValues={
            ":pk": {
                "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#MATCHUP#TEAM#{team1_id}"
            },
            ":sk_prefix": {"S": "SEASON#"},
        },
    )
    items = filter_dynamo_db_response(response=response, playoff_filter=playoff_filter)
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No matchups found for team {team1_id} across all seasons",
        )
    return APIResponse(
        detail=f"Found {len(items)} matchups for team {team1_id} across all seasons",
        data=items,
    )


QUERY_HANDLERS: dict[tuple[bool, bool, bool, bool], Callable[..., Any]] = {
    # (team1_id, team2_id, season, week_number)
    (True, True, True, True): get_specific_matchup_two_teams,
    (True, False, True, True): get_specific_matchup_one_team,
    (True, True, False, False): get_all_time_matchups,
    (False, False, True, True): get_weekly_matchups,
    (True, False, True, False): get_team_season_matchups,
    (True, False, False, False): get_team_all_time_matchups,
}


# pylint: disable=too-many-arguments,too-many-positional-arguments
@router.get("", status_code=status.HTTP_200_OK)
def get_matchups(
    league_id: str = Query(description="The ID of the league the matchup occurred in."),
    platform: str = Query(description="The platform the league is on (e.g., ESPN)."),
    playoff_filter: str = Query(
        description="Filter value indicating whether to exclude, include, or only include playoff matchups."
        "Valid values are 'exclude', 'include', and 'only'.",
    ),
    team1_id: Optional[str] = Query(
        default=None, description="The ID of team 1 in the matchup."
    ),
    team2_id: Optional[str] = Query(
        default=None, description="The ID of team 2 in the matchup."
    ),
    week_number: Optional[str] = Query(
        default=None, description="The week the matchup occurred in."
    ),
    season: Optional[str] = Query(
        default=None, description="The fantasy football season year."
    ),
) -> APIResponse:
    """
    Endpoint to retrieve matchup(s) for a league.

    Args:
        team1_id (str): The ID of team 1 in the matchup.
        team2_id (str): The ID of team 2 in the matchup.
        league_id (str): The ID of the league the team is in.
        platform (str): The platform the league is on (e.g., ESPN).
        include_playoff_matchups (bool): Filter value indicating whether to
            exclude, include, or only include playoff matchups. Valid values
            are 'exclude', 'include', and 'only'.
        week_number (Optional[str]): The week the matchup occurred in.
        season (Optional[str]): The fantasy football season year.
    """
    key = (bool(team1_id), bool(team2_id), bool(season), bool(week_number))
    handler = QUERY_HANDLERS.get(key)
    if not handler:
        log_message = (
            f"Invalid combination of query parameters: "
            f"season={season}, week_number={week_number}, team1_id={team1_id}, team2_id={team2_id}"
        )
        logger.error(log_message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=log_message)

    return query_with_handling(
        handler,
        league_id=league_id,
        platform=platform,
        playoff_filter=playoff_filter,
        team1_id=team1_id,
        team2_id=team2_id,
        season=season,
        week_number=week_number,
    )
