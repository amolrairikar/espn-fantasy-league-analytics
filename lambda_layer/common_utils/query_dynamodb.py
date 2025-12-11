"""Common utility to query data from DynamoDB."""

from typing import Any

import boto3
import botocore.exceptions
from boto3.dynamodb.types import TypeDeserializer

from common_utils.logging_config import logger

deserializer = TypeDeserializer()
DYNAMODB_TABLE_NAME = "fantasy-analytics-app-db"


def fetch_league_data(pk: str, sk_prefix: str) -> list[dict[str, Any]]:
    """
    Generic helper to fetch items from DynamoDB for a given SK prefix.

    Args:
        pk (str): The primary key for the record(s).
        sk_prefix (str): The hash/sort key prefix for the record(s).

    Returns:
        list[dict[str, Any]]: A list of dictionary mappings containing the fetched data.
    """
    try:
        dynamodb = boto3.client("dynamodb")
        response = dynamodb.query(
            TableName=DYNAMODB_TABLE_NAME,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": pk},
                ":prefix": {"S": sk_prefix},
            },
        )
        items = [
            {k: deserializer.deserialize(v) for k, v in item.items()}
            for item in response.get("Items", [])
        ]
        return items
    except botocore.exceptions.ClientError:
        logger.exception(
            "Unexpected error while fetching data with PK '%s' and SK prefix '%s'",
            pk,
            sk_prefix,
        )
        raise
