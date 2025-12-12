import json
import logging
import unittest
from unittest.mock import Mock, patch

from lambda_layer.common_utils.logging_config import JsonFormatter, setup_logger


class TestJsonFormatter(unittest.TestCase):
    """Tests for JsonFormatter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.formatter = JsonFormatter()

    def test_format_returns_valid_json(self):
        """
        Test that format() returns a valid JSON string and
        contains all required fields.
        """
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_func",
        )
        result = self.formatter.format(record)
        parsed = json.loads(result)
        self.assertIsInstance(parsed, dict)
        self.assertIn("timestamp", parsed)
        self.assertIn("level", parsed)
        self.assertIn("message", parsed)
        self.assertIn("function", parsed)

    def test_format_field_value_accuracy(self):
        """Test that JSON fields contains correct values."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_func",
        )
        result = self.formatter.format(record)
        parsed = json.loads(result)
        self.assertEqual(parsed["message"], "Test message")
        self.assertEqual(parsed["level"], "INFO")
        self.assertEqual(parsed["function"], "test_func")
        self.assertIsInstance(parsed["timestamp"], int)
        self.assertGreater(parsed["timestamp"], 0)

    def test_format_with_formatted_message(self):
        """Test that getMessage() is used for message formatting."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Hello %s",
            args=("World",),
            exc_info=None,
            func="test_func",
        )
        result = self.formatter.format(record)
        parsed = json.loads(result)
        self.assertEqual(parsed["message"], "Hello World")


class TestSetupLogger(unittest.TestCase):
    """Tests for setup_logger function."""

    def test_setup_logger_returns_logger_instance(self):
        """Test that setup_logger returns a Logger."""
        with patch(
            "lambda_layer.common_utils.logging_config.logging.getLogger"
        ) as mock_get:
            mock_logger = Mock(spec=logging.Logger)
            mock_get.return_value = mock_logger
            result = setup_logger()
            self.assertIsNotNone(result)

    def test_setup_logger_sets_info_level(self):
        """Test that logger is set to INFO level."""
        with patch(
            "lambda_layer.common_utils.logging_config.logging.getLogger"
        ) as mock_get:
            mock_logger = Mock(spec=logging.Logger)
            mock_get.return_value = mock_logger
            setup_logger()
            mock_logger.setLevel.assert_called_with(logging.INFO)

    def test_setup_logger_configures_stream_handler(self):
        """Test that logger has StreamHandler configured."""
        with patch(
            "lambda_layer.common_utils.logging_config.logging.getLogger"
        ) as mock_get:
            mock_logger = Mock(spec=logging.Logger)
            mock_get.return_value = mock_logger
            setup_logger()
            self.assertEqual(len(mock_logger.handlers), 1)
