"""Common utility to batch write data to DynamoDB with retries."""

import math
import time

import boto3
import botocore.exceptions

from common_utils.logging_config import logger


def batch_write_to_dynamodb(
    batched_objects: list,
    table_name: str,
) -> None:
    """
    Writes data in batches to DynamoDB with retries of unprocessed items using
    exponential backoff.

    Args:
        batched_objects (list): List of items to write to DynamoDB.
        table_name (str): The name of the DynamoDB table.

    Raises:
        botocore.exceptions.ClientError: If a boto3 error occurs while writing to DynamoDB
        RuntimeError: If maximum retries are exceeded for unprocessed items.
    """
    dynamodb = boto3.client("dynamodb")
    try:
        backoff = 1.0
        max_retries = 5

        # BatchWriteItem has max limit of 25 items
        batch_number = 0
        for i in range(0, len(batched_objects), 25):
            logger.info(
                "Processing batch %d/%d",
                batch_number + 1,
                math.ceil(len(batched_objects) / 25),
            )
            batch = batched_objects[i : i + 25]
            request_items = {table_name: batch}
            retries = 0
            while True:
                logger.info("Attempt number: %d", retries + 1)
                response = dynamodb.batch_write_item(RequestItems=request_items)
                unprocessed = response.get("UnprocessedItems", {})
                if not unprocessed.get(table_name):
                    batch_number += 1
                    break  # success, go to next batch

                if retries >= max_retries:
                    raise RuntimeError(
                        f"Max retries exceeded. Still unprocessed: {unprocessed}"
                    )

                logger.info(
                    "Failed to write %d items, retrying unprocessed items...",
                    len(unprocessed),
                )
                retries += 1
                sleep_time = backoff * (2 ** (retries - 1))
                time.sleep(sleep_time)

                # Retry only the failed items
                request_items = unprocessed

    except botocore.exceptions.ClientError:
        logger.exception("Error writing member and team data to DynamoDB")
        raise
