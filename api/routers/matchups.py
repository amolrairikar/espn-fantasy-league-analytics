"""FastAPI router for league matchup endpoints."""

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
    prefix="/matchups",
    dependencies=[Depends(get_api_key)],
)


# pylint: disable=too-many-arguments,too-many-positional-arguments
@router.get("/", status_code=status.HTTP_200_OK)
def get_matchups(
    team1_id: str = Query(description="The ID of team 1 in the matchup."),
    team2_id: str = Query(description="The ID of team 2 in the matchup."),
    league_id: str = Query(description="The ID of the league the matchup occurred in."),
    platform: str = Query(description="The platform the league is on (e.g., ESPN)."),
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
        week_number (str): The week the matchup occurred in.
        season (str): The fantasy football season year.
    """
    try:
        # Get a specific matchup
        if week_number and season:
            response = dynamodb_client.query(
                TableName=table_name,
                KeyConditionExpression="PK = :pk AND SK = :sk",
                ExpressionAttributeValues={
                    ":pk": {
                        "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"
                    },
                    ":sk": {
                        "S": f"MATCHUP#{team1_id}-vs-{team2_id}#WEEK#{week_number}"
                    },
                },
            )
            logger.info(
                "Found matchup between team %s and team %s for season %s week %s",
                team1_id,
                team2_id,
                season,
                week_number,
            )
            items = [
                {k: deserializer.deserialize(v) for k, v in item.items()}
                for item in response.get("Items", [])
            ]
            if not items:
                error_message = f"No matchups between team {team1_id} and team {team2_id} for {season} season week {week_number}"
                logger.warning(error_message)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=APIError(
                        status="error",
                        detail="Matchups not found",
                        developer_detail=error_message,
                    ).model_dump(),
                )
            return APIResponse(
                status="success",
                detail="Found matchup",
                data=items,
            )
        # Get all matchups in a season
        if not week_number and season:
            response = dynamodb_client.query(
                TableName=table_name,
                KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
                ExpressionAttributeValues={
                    ":pk": {
                        "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"
                    },
                    ":prefix": {"S": f"MATCHUP#{team1_id}-vs-{team2_id}"},
                },
            )
            logger.info(
                "Found %d total matchups between team %s and team %s for %s season",
                len(response["Items"]),
                team1_id,
                team2_id,
                season,
            )
            logger.info("Response: %s", response)
            items = [
                {k: deserializer.deserialize(v) for k, v in item.items()}
                for item in response.get("Items", [])
            ]
            logger.info("Items: %s", items)
            if not items:
                log_message = f"No matchups between team {team1_id} and team {team2_id} for {season} season"
                logger.warning(log_message)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=APIError(
                        status="error",
                        detail="Matchups not found",
                        developer_detail=log_message,
                    ).model_dump(),
                )
            return APIResponse(
                status="success",
                detail=f"Found {len(items)} matchups",
                data=items,
            )
        # Get all matchups across all seasons
        response = dynamodb_client.query(
            TableName=table_name,
            IndexName="GSI1",
            KeyConditionExpression="GSI1PK = :pk AND begins_with(GSI1SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": f"MATCHUP#{team1_id}-vs-{team2_id}"},
                ":sk_prefix": {"S": f"LEAGUE#{league_id}"},
            },
        )
        logger.info(
            "Found %d matchups between team %s and team %s",
            len(response["Items"]),
            team1_id,
            team2_id,
        )
        items = [
            {k: deserializer.deserialize(v) for k, v in item.items()}
            for item in response.get("Items", [])
        ]
        if not items:
            log_message = f"No matchups between team {team1_id} and team {team2_id}"
            logger.warning(log_message)
            raise HTTPException(
                status_code=404,
                detail=APIError(
                    status="error",
                    detail="Matchups not found",
                    developer_detail=log_message,
                ).model_dump(),
            )
        return APIResponse(
            status="success",
            detail=f"Found {len(items)} matchups",
            data=items,
        )
    except botocore.exceptions.ClientError as e:
        logger.exception("Unexpected error while getting matchups")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=APIError(
                status="error",
                detail="Internal server error",
                developer_detail=str(e),
            ).model_dump(),
        )
