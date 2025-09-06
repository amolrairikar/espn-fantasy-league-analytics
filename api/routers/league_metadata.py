"""FastAPI router for league metadata endpoints."""

import botocore.exceptions
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from api.dependencies import get_api_key, dynamodb_client, table_name

router = APIRouter(
    prefix="/leagues",
    dependencies=[Depends(get_api_key)],
)


@router.get("/{league_id}")
def get_league_metadata(league_id: str, _: str = Depends(get_api_key)) -> JSONResponse:
    """
    Endpoint to get league metadata (authentication cookies, seasons, etc.).

    Args:
        league_id (str): The ID of the ESPN league to retrieve metadata for.

    Returns:
        JSONResponse: A JSON response containing the league metadata.
    """
    try:
        response = dynamodb_client.get_item(
            TableName=table_name,
            Key={
                "entity": {"S": f"LEAGUE#{league_id}"},
                "entityId": {"S": "METADATA"},
            },
        )
        try:
            cookies = response["Item"]["cookies"]["SS"]
            seasons = response["Item"]["seasons"]["SS"]
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message": "success",
                    "data": {
                        "cookies": cookies,
                        "seasons": seasons,
                    },
                },
            )
        except KeyError:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "message": "error",
                    "data": {},
                    "error": f"Cookies not found for league with ID {league_id}.",
                },
            )
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "message": "error",
                    "data": {},
                    "error": f"League with ID {league_id} not found.",
                },
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "message": "error",
                    "data": {},
                    "error": "An internal server error occurred.",
                },
            )
