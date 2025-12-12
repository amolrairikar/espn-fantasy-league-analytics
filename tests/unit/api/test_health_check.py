"""Module for testing API health check endpoint."""

from unittest.mock import patch

from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import API_KEY_NAME

client = TestClient(app)


@patch("api.dependencies.API_KEY", new="test-api-key")
def test_health_check_with_valid_api_key():
    """Test that /health returns 200 when the API key is provided."""
    response = client.get("/health", headers={API_KEY_NAME: "test-api-key"})
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
