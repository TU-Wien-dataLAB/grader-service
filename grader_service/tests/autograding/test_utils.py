import logging
from unittest.mock import Mock

from grader_service.autograding.utils import collect_logs


def test_collect_logs_with_real_logger():
    """Test collect_logs with a real logger instance."""
    # Create a real logger
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)

    original_handlers_count = len(logger.handlers)

    with collect_logs(logger) as log_stream:
        # Log some messages
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")

        # Verify that logs were captured
        captured_logs = log_stream.getvalue()

    assert "[INFO] Test info message" in captured_logs
    assert "[WARNING] Test warning message" in captured_logs
    assert "[ERROR] Test error message" in captured_logs

    # Verify that the handler was removed after context exit
    assert len(logger.handlers) == original_handlers_count


def test_collect_logs_exception_handling():
    """Test that handler is cleaned up even when an exception occurs."""
    logger = Mock()
    logger.handlers = []

    try:
        with collect_logs(logger):
            # Simulate an exception
            raise ValueError("Test exception")
    except ValueError:
        pass

    # Verify that cleanup still happened despite the exception
    logger.removeHandler.assert_called_once()
    assert len(logger.handlers) == 0
