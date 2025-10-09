# """FastAPI router for utility endpoints."""

# import boto3
# import botocore.exceptions
# from fastapi import APIRouter, Depends, HTTPException

# from api.dependencies import (
#     get_api_key,
#     table_name,
# )

# router = APIRouter(
#     prefix="/utilities",
#     dependencies=[Depends(get_api_key)],
# )

# dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
# table = dynamodb.Table(table_name)

# @router.delete("/delete")
# def clear_table():
#     try:
#         # Scan table to get all keys
#         response = table.scan(
#             ProjectionExpression="#pk, #sk",
#             ExpressionAttributeNames={"#pk": "PK", "#sk": "SK"}
#         )
#         items = response.get("Items", [])

#         # Batch write to delete items
#         with table.batch_writer() as batch:
#             for item in items:
#                 batch.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})

#         return {"status": "success", "deleted_items": len(items)}

#     except botocore.exceptions.ClientError as e:
#         raise HTTPException(status_code=500, detail=str(e))
