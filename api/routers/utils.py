"""FastAPI router for utility endpoints."""

from fastapi import APIRouter, Depends

from api.dependencies import (
    get_api_key,
)

router = APIRouter(
    dependencies=[Depends(get_api_key)],
)

# dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
# table = dynamodb.Table(table_name)


# @router.delete("/delete_league", status_code=status.HTTP_200_OK)
# def delete_league_items(
#     league_id: str = Query(description="The ID of the league the team is in."),
# ):
#     """
#     Delete all items associated with a specific league and platform from the database.

#     Args:
#         league_id (str): The ID of the league.
#     """
#     gsi_pk = f"LEAGUE#{league_id}"
#     gsi_sk = "FOR_DELETION_USE_ONLY"
#     deleted_count = 0

#     try:
#         query_kwargs = {
#             "IndexName": "GSI5",
#             "KeyConditionExpression": Key("GSI5PK").eq(gsi_pk)
#             & Key("GSI5SK").eq(gsi_sk),
#             "ProjectionExpression": "#pk, #sk",
#             "ExpressionAttributeNames": {"#pk": "PK", "#sk": "SK"},
#         }

#         done = False
#         start_key = None

#         while not done:
#             if start_key:
#                 query_kwargs["ExclusiveStartKey"] = start_key

#             response = table.query(**query_kwargs)
#             items = response.get("Items", [])

#             if items:
#                 with table.batch_writer() as batch:
#                     for item in items:
#                         batch.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})
#                         deleted_count += 1

#             start_key = response.get("LastEvaluatedKey")
#             done = start_key is None

#         return APIResponse(
#             detail=f"Deleted {deleted_count} items for league_id {league_id}.",
#         )

#     except botocore.exceptions.ClientError as e:
#         raise HTTPException(status_code=500, detail=str(e))
