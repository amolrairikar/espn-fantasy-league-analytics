import boto3
import botocore.exceptions
from behave.runner import Context


def after_all(context: Context):
    """Tear down DynamoDB table used for testing."""
    dynamodb = boto3.client("dynamodb")
    table_name = "integration-test-table"

    # Uncomment the below section if the DynamoDB table needs to be left up to debug failing tests
    # # Check if the test suite failed
    # if context.failed:
    #     print(f"Tests failed. Leaving table '{table_name}' active for debugging.")
    #     return

    print(f"Starting teardown for table: {table_name}")
    try:
        dynamodb.delete_table(TableName=table_name)

        # Wait for deletion to complete
        waiter = dynamodb.get_waiter("table_not_exists")
        waiter.wait(TableName=table_name, WaiterConfig={"Delay": 2, "MaxAttempts": 10})
        print(f"Table {table_name} deleted successfully.")

    # If the table wasn't there, we've achieved our goal anyway
    except dynamodb.exceptions.ResourceNotFoundException:
        print(f"Table {table_name} not found; skipping deletion.")

    except botocore.exceptions.ClientError as e:
        print(f"Unexpected error during teardown: {e}")
