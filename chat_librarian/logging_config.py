"""Logging configuration for Chat Librarian with structured logging support."""

import logging
import sys
from typing import Any, Dict

import structlog
from rich.console import Console

# Global console instance for rich output
console = Console()

# Global logger instance
logger = structlog.get_logger()


def configure_logging(debug: bool = False) -> None:
    """Configure structured logging for the application.

    Args:
        debug: If True, enables debug-level logging with verbose output
    """
    # Set log level based on debug flag
    log_level = logging.DEBUG if debug else logging.INFO

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Configure structlog
    if debug:
        # Debug mode: more verbose, include all fields
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_logger_name,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # Production mode: cleaner output, essential info only
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.processors.add_log_level,
            _clean_console_renderer,
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _clean_console_renderer(
    logger: object, method_name: str, event_dict: Dict[str, Any]
) -> str:
    """Custom renderer for clean console output in production mode."""
    level = event_dict.get("level", "info").upper()
    event = event_dict.get("event", "")

    # Extract additional context
    platform = event_dict.get("platform", "")
    selector = event_dict.get("selector", "")
    count = event_dict.get("count", "")
    duration = event_dict.get("duration_ms", "")

    # Format the message based on available context
    if platform:
        prefix = f"[{platform}]"
    else:
        prefix = ""

    if selector and count:
        suffix = f" (selector: {selector}, found: {count})"
    elif selector:
        suffix = f" (selector: {selector})"
    elif count:
        suffix = f" (count: {count})"
    elif duration:
        suffix = f" ({duration}ms)"
    else:
        suffix = ""

    if level == "DEBUG":
        return f"🔍 {prefix} {event}{suffix}"
    elif level == "INFO":
        return f"ℹ️  {prefix} {event}{suffix}"
    elif level == "WARNING":
        return f"⚠️  {prefix} {event}{suffix}"
    elif level == "ERROR":
        return f"❌ {prefix} {event}{suffix}"
    else:
        return f"{prefix} {event}{suffix}"


def get_logger() -> structlog.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger()


# Convenience functions for common logging patterns
def log_selector_attempt(selector: str, platform: str = "") -> None:
    """Log when trying a DOM selector."""
    logger.debug("Trying selector", selector=selector, platform=platform)


def log_selector_success(selector: str, count: int, platform: str = "") -> None:
    """Log when a selector succeeds."""
    logger.info(
        "Selector found elements", selector=selector, count=count, platform=platform
    )


def log_selector_failure(selector: str, platform: str = "") -> None:
    """Log when a selector fails."""
    logger.debug("Selector found no elements", selector=selector, platform=platform)


def log_platform_action(action: str, platform: str, **kwargs: object) -> None:
    """Log a platform-specific action."""
    logger.info(action, platform=platform, **kwargs)


def log_error(
    message: str, error: Exception, platform: str = "", **kwargs: object
) -> None:
    """Log an error with context."""
    logger.error(
        message,
        error=str(error),
        error_type=type(error).__name__,
        platform=platform,
        **kwargs,
    )


def log_timing(
    action: str, duration_ms: float, platform: str = "", **kwargs: object
) -> None:
    """Log timing information."""
    logger.info(action, duration_ms=round(duration_ms, 2), platform=platform, **kwargs)
