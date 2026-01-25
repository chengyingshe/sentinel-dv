"""Time utilities for Sentinel DV."""

from datetime import datetime, timezone
from typing import Optional


def now_utc() -> datetime:
    """Get current UTC time as timezone-aware datetime.

    Returns:
        Current UTC timestamp.
    """
    return datetime.now(timezone.utc)


def parse_rfc3339(timestamp: str) -> datetime:
    """Parse RFC3339/ISO8601 timestamp string.

    Args:
        timestamp: RFC3339 formatted timestamp string.

    Returns:
        Parsed datetime object (timezone-aware).

    Raises:
        ValueError: If timestamp format is invalid.
    """
    try:
        # Try parsing with timezone
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as e:
        raise ValueError(f"Invalid RFC3339 timestamp: {timestamp}") from e


def to_rfc3339(dt: datetime) -> str:
    """Format datetime as RFC3339 string.

    Args:
        dt: Datetime object to format.

    Returns:
        RFC3339 formatted string (with 'Z' suffix for UTC).
    """
    if dt.tzinfo is None:
        # Assume UTC if naive
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def ns_to_human(nanoseconds: int) -> str:
    """Convert nanoseconds to human-readable time string.

    Args:
        nanoseconds: Time in nanoseconds.

    Returns:
        Human-readable string (e.g., "1.25us", "3.5ms", "2.1s").
    """
    if nanoseconds < 0:
        raise ValueError("nanoseconds must be non-negative")

    if nanoseconds == 0:
        return "0ns"

    # Convert to appropriate unit
    if nanoseconds < 1000:
        return f"{nanoseconds}ns"
    elif nanoseconds < 1_000_000:
        return f"{nanoseconds / 1000:.2f}us"
    elif nanoseconds < 1_000_000_000:
        return f"{nanoseconds / 1_000_000:.2f}ms"
    else:
        return f"{nanoseconds / 1_000_000_000:.2f}s"


def parse_simulation_time(time_str: str) -> Optional[int]:
    """Parse simulation time string to nanoseconds.

    Supports formats:
    - "1250ns"
    - "1.25us"
    - "3.5ms"
    - "2s"

    Args:
        time_str: Time string to parse.

    Returns:
        Time in nanoseconds, or None if parsing fails.
    """
    time_str = time_str.strip().lower()

    try:
        if time_str.endswith("ns"):
            return int(float(time_str[:-2]))
        elif time_str.endswith("us"):
            return int(float(time_str[:-2]) * 1_000)
        elif time_str.endswith("ms"):
            return int(float(time_str[:-2]) * 1_000_000)
        elif time_str.endswith("s"):
            return int(float(time_str[:-1]) * 1_000_000_000)
        else:
            # Try parsing as plain integer (assume ns)
            return int(float(time_str))
    except (ValueError, IndexError):
        return None
