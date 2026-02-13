import json
import os

import requests
from behave import given, when, then
from behave.runner import Context
from dotenv import load_dotenv


@given("a valid API configuration")  # type: ignore[reportCallIssue]
def get_valid_inputs(context: Context):
    """Fetch valid league onboarding inputs from a .env file."""
    load_dotenv()
    context.api_base_url = os.environ["API_BASE_URL"]
    context.api_key = os.environ["API_KEY"]


@given("query parameter {param_name} with value {param_value}")  # type: ignore[reportCallIssue]
def set_query_parameter(context: Context, param_name: str, param_value: str):
    """Set a query parameter for the API request."""
    if not hasattr(context, "params"):
        context.params = {}
    context.params[param_name] = param_value if param_value != "null" else None
    print(f"Set query parameter: {param_name} = {context.params[param_name]}")


@given("secure query parameter {param_name}")  # type: ignore[reportCallIssue]
def set_secure_query_parameter(context: Context, param_name: str):
    """Set a secure query parameter for the API request."""
    if not hasattr(context, "params"):
        context.params = {}
    context.params[param_name] = os.environ[param_name.upper()]
    print(f"Set secure query parameter: {param_name} = {context.params[param_name]}")


@given("request body field {field_name} with value {field_value}")  # type: ignore[reportCallIssue]
def set_body_field(context: Context, field_name: str, field_value: str):
    """Set a request body field for the API request."""
    if not hasattr(context, "body_fields"):
        context.body_fields = {}
    try:
        parsed = json.loads(field_value)
    except Exception:
        parsed = str(field_value)
    context.body_fields[field_name] = parsed


@given("secure request body field {param_name}")  # type: ignore[reportCallIssue]
def set_secure_body_field(context: Context, param_name: str):
    """Set a secure request body field for the API request."""
    if not hasattr(context, "body_fields"):
        context.body_fields = {}
    context.body_fields[param_name] = os.environ[param_name.upper()]


@when("we make a {request_type} request to the {endpoint} endpoint")  # type: ignore[reportCallIssue]
def make_api_request(context: Context, request_type: str, endpoint: str):
    """Make a request of request_type (GET, POST, PUT, DELETE) to the specified API endpoint."""
    base_url = context.api_base_url
    url = f"{base_url}/{endpoint}"
    print(f"Making {request_type} request to URL: {url}")
    headers = {"x-api-key": context.api_key}
    if request_type.upper() == "GET":
        context.response = requests.get(
            url,
            headers=headers,
            params=context.params if hasattr(context, "params") else None,
        )
    elif request_type.upper() == "POST":
        print(
            f"Request body: {json.dumps(context.body_fields) if hasattr(context, 'body_fields') else None}"
        )
        context.response = requests.post(
            url,
            headers=headers,
            params=context.params if hasattr(context, "params") else None,
            json=context.body_fields if hasattr(context, "body_fields") else None,
        )
    elif request_type.upper() == "PATCH":
        print(
            f"Request body: {json.dumps(context.body_fields) if hasattr(context, 'body_fields') else None}"
        )
        context.response = requests.patch(
            url,
            headers=headers,
            params=context.params if hasattr(context, "params") else None,
            json=context.body_fields if hasattr(context, "body_fields") else None,
        )
    elif request_type.upper() == "DELETE":
        context.response = requests.delete(
            url,
            headers=headers,
            params=context.params if hasattr(context, "params") else None,
        )
    else:
        raise ValueError(f"Unsupported request type: {request_type}")


@then("the request will return a {status_code} status code")  # type: ignore[reportCallIssue]
def check_status_code(context: Context, status_code: str):
    """Check that the API response has the expected status code."""
    print(context.response.text)
    assert context.response is not None, "No response found in context"
    assert str(context.response.status_code) == status_code, (
        f"Expected status code {status_code} but got {context.response.status_code}"
    )
