"""FastAPI router for utility endpoints."""

import boto3
import botocore.exceptions
from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import (
    get_api_key,
    table_name,
)

router = APIRouter(
    dependencies=[Depends(get_api_key)],
)

dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
table = dynamodb.Table(table_name)


@router.delete("/delete_league")
def delete_league_items(
    league_id: str = Query(description="The ID of the league the team is in."),
    platform: str = Query(description="The platform the league is on (e.g., ESPN)."),
):
    """
    Delete all items associated with a specific league and platform from the database.

    Args:
        league_id (str): The ID of the league.
        platform (str): The platform of the league.
    """
    prefix = f"LEAGUE#{league_id}#PLATFORM#{platform}"
    deleted_count = 0

    try:
        # DynamoDB scan with pagination
        scan_kwargs = {
            "ProjectionExpression": "#pk, #sk",
            "ExpressionAttributeNames": {"#pk": "PK", "#sk": "SK"},
            "FilterExpression": "begins_with(PK, :prefix)",
            "ExpressionAttributeValues": {":prefix": prefix},
        }

        done = False
        start_key = None

        while not done:
            if start_key:
                scan_kwargs["ExclusiveStartKey"] = start_key

            response = table.scan(**scan_kwargs)
            items = response.get("Items", [])

            # Batch delete
            if items:
                with table.batch_writer() as batch:
                    for item in items:
                        batch.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})
                        deleted_count += 1

            start_key = response.get("LastEvaluatedKey")
            done = start_key is None

        return {"status": "success", "deleted_items": deleted_count}

    except botocore.exceptions.ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
