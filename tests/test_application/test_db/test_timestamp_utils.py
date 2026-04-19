"""
Unit tests for git commit timestamp correction functions.

Tests the timestamp_utils module which validates and corrects invalid
timezone offsets in git commit timestamps before PostgreSQL insertion.
"""

import pytest
import logging
from augur.application.db.timestamp_utils import (
    correct_timestamp,
    clean_commit_timestamps,
    POSTGRES_VALID_TIMEZONES
)


@pytest.fixture
def test_logger():
    """Provide a basic logger for tests."""
    return logging.getLogger("test_correction")


class TestCorrectTimestamp:
    """Tests for the correct_timestamp function."""

    def test_valid_timestamp_unchanged(self, test_logger):
        """Valid timestamp should pass through unchanged."""
        valid_ts = "2025-11-03 16:28:43 -0500"
        result = correct_timestamp(valid_ts, logger=test_logger)
        assert result == valid_ts

    def test_valid_utc_timestamp(self, test_logger):
        """UTC timestamp (offset 0) should pass through unchanged."""
        utc_ts = "2025-11-03 16:28:43 +0000"
        result = correct_timestamp(utc_ts, logger=test_logger)
        assert result == utc_ts

    def test_invalid_timezone_uses_fallback(self, test_logger):
        """Invalid timezone should use fallback timestamp."""
        invalid_ts = "2106-02-07 06:28:23 -13068837"
        fallback_ts = "2025-11-03 16:28:43 -0500"
        result = correct_timestamp(invalid_ts, fallback=fallback_ts, logger=test_logger)
        assert result == fallback_ts

    def test_invalid_timezone_uses_utc_if_no_fallback(self, test_logger):
        """Invalid timezone without fallback should default to UTC."""
        invalid_ts = "2106-02-07 06:28:23 -13068837"
        result = correct_timestamp(invalid_ts, fallback=None, logger=test_logger)
        # Should replace timezone with +0000, keep date/time
        assert result == "2106-02-07 06:28:23 +0000"

    def test_empty_string_returns_default(self, test_logger):
        """Empty timestamp string should return default epoch."""
        result = correct_timestamp("", logger=test_logger)
        assert result == "1970-01-01 00:00:15 +0000"

    def test_unparseable_format_returns_default(self, test_logger):
        """Unparseable timestamp format should return default."""
        unparseable = "not a timestamp"
        result = correct_timestamp(unparseable, logger=test_logger)
        assert result == "1970-01-01 00:00:15 +0000"

    def test_unparseable_with_fallback_returns_fallback(self, test_logger):
        """Unparseable timestamp with fallback should return fallback."""
        unparseable = "not a timestamp"
        fallback = "2025-11-03 16:28:43 -0500"
        result = correct_timestamp(unparseable, fallback=fallback, logger=test_logger)
        assert result == fallback

    def test_none_returns_default(self, test_logger):
        """None timestamp (e.g. from record.get() with no default) should return default epoch."""
        result = correct_timestamp(None, logger=test_logger)
        assert result == "1970-01-01 00:00:15 +0000"

    def test_none_with_fallback_returns_fallback(self, test_logger):
        """None timestamp with fallback should return fallback."""
        fallback = "2025-11-03 16:28:43 -0500"
        result = correct_timestamp(None, fallback=fallback, logger=test_logger)
        assert result == fallback


class TestCleanCommitTimestamps:
    """Tests for the clean_commit_timestamps function."""

    def test_issue_3472_exact_case(self, test_logger):
        """Reproduce the exact bug from issue #3472.

        Author timestamp has valid timezone (-0500).
        Committer timestamp has invalid timezone (-13068837).
        Should use author timestamp as fallback for committer.
        """
        records = [
            {
                'cmt_commit_hash': '5de262a839',
                'cmt_author_timestamp': '2025-11-03 16:28:43 -0500',
                'cmt_committer_timestamp': '2106-02-07 06:28:23 -13068837'
            }
        ]

        clean_commit_timestamps(records, test_logger)

        # Author should be unchanged (valid)
        assert records[0]['cmt_author_timestamp'] == '2025-11-03 16:28:43 -0500'

        # Committer should use author as fallback (invalid → fallback)
        assert records[0]['cmt_committer_timestamp'] == '2025-11-03 16:28:43 -0500'

    def test_clean_commit_timestamps_batch(self, test_logger):
        """Test batch processing of multiple commits."""
        records = [
            {
                'cmt_author_timestamp': '2025-11-03 16:28:43 -0500',  # Valid
                'cmt_committer_timestamp': '2025-11-03 16:28:43 -0500'  # Valid
            },
            {
                'cmt_author_timestamp': '2025-11-04 10:00:00 +0000',  # Valid
                'cmt_committer_timestamp': '2106-02-07 06:28:23 -99999'  # Invalid
            },
            {
                'cmt_author_timestamp': '2025-11-05 12:00:00 -12345',  # Invalid
                'cmt_committer_timestamp': '2025-11-05 13:00:00 +0530'  # Valid
            }
        ]

        clean_commit_timestamps(records, test_logger)

        # Record 1: Both valid, unchanged
        assert records[0]['cmt_author_timestamp'] == '2025-11-03 16:28:43 -0500'
        assert records[0]['cmt_committer_timestamp'] == '2025-11-03 16:28:43 -0500'

        # Record 2: Author valid, committer invalid → use author as fallback
        assert records[1]['cmt_author_timestamp'] == '2025-11-04 10:00:00 +0000'
        assert records[1]['cmt_committer_timestamp'] == '2025-11-04 10:00:00 +0000'

        # Record 3: Author invalid → UTC, committer valid → unchanged
        assert records[2]['cmt_author_timestamp'] == '2025-11-05 12:00:00 +0000'
        assert records[2]['cmt_committer_timestamp'] == '2025-11-05 13:00:00 +0530'

    def test_both_timestamps_invalid(self, test_logger):
        """When both timestamps invalid, both should default to UTC."""
        records = [
            {
                'cmt_author_timestamp': '2025-11-03 16:28:43 -99999',
                'cmt_committer_timestamp': '2106-02-07 06:28:23 -88888'
            }
        ]

        clean_commit_timestamps(records, test_logger)

        # Author invalid → UTC (no fallback)
        assert records[0]['cmt_author_timestamp'] == '2025-11-03 16:28:43 +0000'

        # Committer invalid → fallback to corrected author (which is UTC)
        assert records[0]['cmt_committer_timestamp'] == '2025-11-03 16:28:43 +0000'


class TestPostgresValidTimezones:
    """Verify the POSTGRES_VALID_TIMEZONES set is correct."""

    def test_valid_timezones_range(self):
        """Valid timezones should be in range -12:00 to +14:00."""
        for tz in POSTGRES_VALID_TIMEZONES:
            assert -1200 <= tz <= 1400

    def test_common_timezones_present(self):
        """Common timezone offsets should be in the set."""
        common = [0, -500, -400, -800, 100, 530, 800]  # UTC, EST, EDT, PST, CET, IST, CST
        for tz in common:
            assert tz in POSTGRES_VALID_TIMEZONES
