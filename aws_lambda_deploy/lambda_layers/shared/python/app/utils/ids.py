"""
UUID and timestamp utilities for DynamoDB-compatible IDs.

Design Principles:
- UUIDs for all IDs (no auto-increment for portability)
- ISO8601 strings for dates (cross-database compatibility)
- Designed to work with both SQLite (local) and DynamoDB (cloud)
"""
import uuid
from datetime import datetime, timezone


def generate_uuid() -> str:
    """
    Generate a new UUID4 string.

    Returns:
        str: UUID string (e.g., '7c9e6679-7425-40de-944b-e07fc1f90ae7')
    """
    return str(uuid.uuid4())


def now_iso8601() -> str:
    """
    Get current timestamp in ISO8601 format (UTC).

    Returns:
        str: ISO8601 timestamp (e.g., '2026-01-31T14:30:00Z')
    """
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def parse_iso8601(date_str: str) -> datetime:
    """
    Parse an ISO8601 string to datetime.

    Args:
        date_str: ISO8601 formatted string

    Returns:
        datetime: Parsed datetime object (UTC)
    """
    if not date_str:
        return None

    # Handle different ISO8601 formats
    try:
        # Format: 2026-01-31T14:30:00Z
        if date_str.endswith('Z'):
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        # Format with timezone offset
        return datetime.fromisoformat(date_str)
    except ValueError:
        return None


def generate_sort_key(prefix: str, entity_id: str) -> str:
    """
    Generate a DynamoDB-compatible sort key.

    Args:
        prefix: Entity type prefix (e.g., 'AD', 'PAGE', 'RUN')
        entity_id: The entity's unique ID

    Returns:
        str: Sort key (e.g., 'AD#7c9e6679-7425-40de-944b-e07fc1f90ae7')
    """
    return f"{prefix}#{entity_id}"


def generate_run_sort_key(timestamp: str, run_id: str) -> str:
    """
    Generate a sort key for collection runs.
    Includes timestamp for chronological sorting.

    Args:
        timestamp: ISO8601 timestamp
        run_id: UUID of the run

    Returns:
        str: Sort key (e.g., 'RUN#2026-01-31T14:30:00Z#uuid')
    """
    return f"RUN#{timestamp}#{run_id}"
