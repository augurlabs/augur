"""
Timestamp correction utilities for git commit data.

This module provides functions to validate and correct timestamp strings
before database insertion, specifically handling invalid timezone offsets
that PostgreSQL cannot process. Resides in the db layer so it can be used
by db-layer bulk insert logic without crossing into the tasks layer.
"""

import logging
from typing import List, Optional


# Valid PostgreSQL timezone offsets in format ±HHMM (e.g., -0500, +0530)
# Range: -12:00 to +14:00 including all real-world fractional hour offsets
POSTGRES_VALID_TIMEZONES = {
    -1200, -1100, -1000, -930, -900, -800, -700,
    -600, -500, -430, -400, -330, -300, -230, -200, -100, 0,
    100, 200, 300, 330, 400, 430, 500, 530, 545, 600,
    630, 700, 800, 845, 900, 930, 1000, 1030, 1100, 1130, 1200,
    1245, 1300, 1345, 1400
}


def correct_timestamp(
    timestamp_str: str,
    fallback: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> str:
    """Fix invalid timezone in timestamp string.

    Validates the timezone portion of a timestamp and corrects it if invalid.
    Handles three cases:
    1. Valid timezone → return as-is
    2. Invalid timezone → replace with fallback or UTC
    3. Unparseable format → return fallback or default

    Args:
        timestamp_str: Timestamp string in format 'YYYY-MM-DD HH:MM:SS ±HHMM'
        fallback: Optional fallback timestamp to use if correction needed
        logger: Optional logger for recording corrections

    Returns:
        Corrected timestamp string safe for PostgreSQL insertion
    """
    if not timestamp_str:
        return fallback or "1970-01-01 00:00:15 +0000"

    # Split on last space to separate date/time from timezone
    # Example: '2025-11-03 16:28:43 -0500' → ['2025-11-03 16:28:43', '-0500']
    parts = timestamp_str.strip().rsplit(' ', 1)

    if len(parts) != 2:
        # No space found, can't parse
        if logger:
            logger.warning(f"Unparseable timestamp format (no space): {timestamp_str}")
        return fallback or "1970-01-01 00:00:15 +0000"

    date_time, tz_string = parts

    # Validate timezone starts with + or -
    if not tz_string or tz_string[0] not in ('+', '-'):
        if logger:
            logger.warning(f"Unparseable timezone (no sign): {tz_string}")
        return fallback or "1970-01-01 00:00:15 +0000"

    # Normalize timezone: remove colons (handles both -0500 and -05:00)
    tz_normalized = tz_string.replace(':', '')

    # Try to parse as integer
    try:
        tz_offset = int(tz_normalized)
    except ValueError:
        if logger:
            logger.warning(f"Could not parse timezone as integer: {tz_string}")
        return fallback or "1970-01-01 00:00:15 +0000"

    # Check if timezone is valid
    if tz_offset in POSTGRES_VALID_TIMEZONES:
        # Valid timezone, return original
        return timestamp_str

    # Invalid timezone detected
    if fallback:
        if logger:
            logger.info(f"Invalid timezone {tz_offset} in '{timestamp_str}', using fallback")
        return fallback

    # No fallback, default to UTC
    if logger:
        logger.warning(f"Invalid timezone {tz_offset} in '{timestamp_str}', defaulting to UTC")
    return f"{date_time} +0000"


def clean_commit_timestamps(records: List[dict], logger: logging.Logger) -> None:
    """Validate and correct timestamps in commit records in-place.

    Processes a batch of commit records, validating both author and committer
    timestamps. For invalid committer timestamps, uses the corrected author
    timestamp as a fallback before defaulting to UTC.

    This prevents PostgreSQL insertion failures due to invalid timezone offsets
    (e.g., -13068837 which is outside the valid ±14:00 range).

    Args:
        records: List of commit record dicts with keys:
                 - 'cmt_author_timestamp'
                 - 'cmt_committer_timestamp'
        logger: Logger for recording corrections

    Returns:
        None (modifies records in-place)
    """
    for record in records:
        author_ts = record.get('cmt_author_timestamp', '')
        committer_ts = record.get('cmt_committer_timestamp', '')

        # Correct author timestamp first (no fallback, will use UTC if invalid)
        author_corrected = correct_timestamp(author_ts, fallback=None, logger=logger)

        # Correct committer timestamp, using corrected author as fallback
        # This minimizes data loss per issue discussion (prefer author time over UTC)
        committer_corrected = correct_timestamp(
            committer_ts,
            fallback=author_corrected,
            logger=logger
        )

        record['cmt_author_timestamp'] = author_corrected
        record['cmt_committer_timestamp'] = committer_corrected
