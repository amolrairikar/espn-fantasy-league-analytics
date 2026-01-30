import boto3
from boto3.dynamodb.types import TypeDeserializer
import botocore.exceptions
from behave import given, when, then, use_step_matcher
from behave.runner import Context

from lambda_layer.common_utils.batch_write_dynamodb import batch_write_to_dynamodb
from lambda_layer.common_utils.query_dynamodb import fetch_league_data

deserializer = TypeDeserializer()


@given("a DynamoDB table named {table_name}")  # type: ignore[reportCallIssue]
def create_dynamodb_table(context: Context, table_name: str):
    """Check for, create, and wait for a DynamoDB table to be ACTIVE."""
    context.table_name = table_name
    print(
        f"DEBUG: create_dynamodb_table - table_name is currently '{context.table_name}'"
    )
    dynamodb = boto3.client("dynamodb")

    # Attempt to create the table
    try:
        dynamodb.create_table(
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            BillingMode="PAY_PER_REQUEST",
            TableClass="STANDARD",
        )
        print(f"Creating table {table_name}...")

    # If it already exists, move on to the waiter
    except dynamodb.exceptions.ResourceInUseException:
        print(f"Table {table_name} already exists.")

    except botocore.exceptions.ClientError as e:
        print(f"Unexpected error: {e}")
        raise

    # Wait for the table to reach 'ACTIVE' status
    # This will poll every 20 seconds (by default) until successful or timed out
    waiter = dynamodb.get_waiter("table_exists")
    try:
        waiter.wait(TableName=table_name, WaiterConfig={"Delay": 2, "MaxAttempts": 10})
        print(f"Table {table_name} is now ACTIVE.")
    except botocore.exceptions.WaiterError as e:
        print(f"Table {table_name} failed to reach ACTIVE state: {e}")
        raise


# Enables regex patterns in next step decorator
use_step_matcher("re")


@when(r"we write (a single batch|multiple batches) of data")  # type: ignore[reportCallIssue]
def write_to_dynamodb(context: Context, condition: str):
    """Call the batch_write_to_dynamodb function to write sample data to DynamoDB."""
    mock_data = []
    if condition == "a single batch":
        mock_data = [
            {
                "PutRequest": {
                    "Item": {
                        "PK": {"S": "test_pk"},
                        "SK": {"S": "sk-1"},
                    }
                }
            },
            {
                "PutRequest": {
                    "Item": {
                        "PK": {"S": "test_pk"},
                        "SK": {"S": "sk-2"},
                    }
                }
            },
        ]
    elif condition == "multiple batches":
        for i in range(3, 36):
            mock_data.append(
                {
                    "PutRequest": {
                        "Item": {
                            "PK": {"S": "test_pk"},
                            "SK": {"S": f"sk-{i}"},
                        }
                    }
                }
            )
    batch_write_to_dynamodb(
        batched_objects=mock_data,
        table_name="integration-test-table",
    )


@then(r"the table will contain (\d+) records")  # type: ignore[reportCallIssue]
def query_dynamodb(context: Context, num_records: str):
    """Query DynamoDB table to verify record count."""
    items = fetch_league_data(
        table_name=context.table_name,
        pk="test_pk",
        sk_prefix="sk-",
    )
    assert len(items) == int(num_records), (
        f"Expected {num_records} items, but found {len(items)}"
    )
