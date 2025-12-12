import typing
import unittest

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from lambda_layer.common_utils.retryable_request_session import create_retry_session


class TestCreateRetrySession(unittest.TestCase):
    """Tests for create_retry_session function."""

    def test_returns_session_instance(self):
        """Test that create_retry_session returns a requests.Session."""
        session = create_retry_session()
        self.assertIsInstance(session, requests.Session)

    def test_http_adapter_mounted(self):
        """Test that HTTP adapter is mounted."""
        session = create_retry_session()
        adapter = session.get_adapter("http://example.com")
        self.assertIsInstance(adapter, HTTPAdapter)

    def test_https_adapter_mounted(self):
        """Test that HTTPS adapter is mounted."""
        session = create_retry_session()
        adapter = session.get_adapter("https://example.com")
        self.assertIsInstance(adapter, HTTPAdapter)

    def test_adapter_has_retry_strategy(self):
        """Test that adapters have correct retry strategy configured."""
        session = create_retry_session()
        # Use typing.cast to inform the type checker that 'adapter' is an HTTPAdapter
        adapter = typing.cast(HTTPAdapter, session.get_adapter("https://example.com"))
        expected_statuses = [429, 500, 502, 503, 504]
        expected_methods = ["GET", "POST", "PUT", "DELETE"]

        self.assertIsNotNone(adapter.max_retries)
        self.assertIsInstance(adapter.max_retries, Retry)
        self.assertEqual(adapter.max_retries.total, 3)
        self.assertEqual(adapter.max_retries.backoff_factor, 0.3)
        self.assertEqual(list(adapter.max_retries.status_forcelist), expected_statuses)
        self.assertEqual(adapter.max_retries.allowed_methods, expected_methods)

    def test_session_is_independent(self):
        """Test that multiple sessions are independent instances."""
        session1 = create_retry_session()
        session2 = create_retry_session()
        self.assertIsNot(session1, session2)

    def test_adapter_configuration_persists(self):
        """Test that adapter configuration persists across mounts."""
        session = create_retry_session()
        # Use typing.cast to inform the type checker that 'adapter' is an HTTPAdapter
        http_adapter = typing.cast(
            HTTPAdapter, session.get_adapter("https://example.com")
        )
        https_adapter = typing.cast(
            HTTPAdapter, session.get_adapter("https://example.com")
        )
        self.assertEqual(http_adapter.max_retries.total, 3)
        self.assertEqual(https_adapter.max_retries.total, 3)

    def test_session_can_be_used_for_requests(self):
        """Test that returned session is usable for making requests."""
        session = create_retry_session()
        self.assertTrue(callable(session.get))
        self.assertTrue(callable(session.post))
        self.assertTrue(callable(session.put))
        self.assertTrue(callable(session.delete))
