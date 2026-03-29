# SPDX-License-Identifier: MIT
"""
CSV processing utilities for Augur CLI
"""
import csv
import logging
import os
from typing import Callable

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def validate_git_url(value: str) -> bool:
    """Validate if value is a valid git repository URL.

    Checks if the provided string is a valid GitHub or GitLab repository URL
    using the Repo model's URL parsing methods.

    Args:
        value: String to validate as a git repository URL

    Returns:
        True if the value is a valid GitHub or GitLab URL, False otherwise
    """
    from augur.application.db.models import Repo

    value = value.strip()
    github_parse = Repo.parse_github_repo_url(value)
    gitlab_parse = Repo.parse_gitlab_repo_url(value)
    return github_parse != (None, None) or gitlab_parse != (None, None)


def validate_positive_int(value: str) -> bool:
    """Validate if value is a positive integer.

    Args:
        value: String to validate as a positive integer

    Returns:
        True if the value can be converted to a positive integer, False otherwise
    """
    try:
        return int(value.strip()) > 0
    except (ValueError, AttributeError):
        return False


def detect_column_order(
    sample_rows: list[list[str]], validators: dict[str, Callable[[str], bool]]
) -> dict[str, int]:
    """Detect column order by testing validators against sample data.

    For headerless CSV files, this function determines which column index
    corresponds to which expected field by validating sample data against
    validator functions. Uses an 80% threshold for matching.

    Args:
        sample_rows: List of rows from CSV file, where each row is a list of strings
        validators: Dictionary mapping column names to validator functions

    Returns:
        Dictionary mapping column names to their detected column indices

    Raises:
        ValueError: If column count doesn't match expected validators or if
                   a column cannot be detected with sufficient confidence
    """
    if not sample_rows or len(sample_rows[0]) != len(validators):
        raise ValueError(
            f"Expected {len(validators)} columns. "
            f"Found {len(sample_rows[0]) if sample_rows else 0} columns."
        )

    # Sample first 10 rows to determine column types
    sample_size = min(10, len(sample_rows))
    sample_data = sample_rows[:sample_size]

    # Try to match each validator to a column using 80% threshold
    column_mapping = {}
    used_indices = set()

    for col_name, validator in validators.items():
        best_match_idx = None

        # Test each column
        for col_idx in range(len(sample_data[0])):
            if col_idx in used_indices:
                continue

            # Count how many values in this column pass validation
            matches = 0
            for row in sample_data:
                if col_idx < len(row) and validator(row[col_idx]):
                    matches += 1

            # If >80% of values pass validation, this is the correct column
            match_rate = matches / len(sample_data)
            if match_rate >= 0.8:
                best_match_idx = col_idx
                break

        if best_match_idx is not None:
            column_mapping[col_name] = best_match_idx
            used_indices.add(best_match_idx)
        else:
            # No match found for this column
            raise ValueError(
                f"Could not detect column '{col_name}'. "
                f"Ensure CSV has valid format or add headers: {', '.join(validators.keys())}"
            )

    return column_mapping


def process_csv(
    filename: str, expected_columns: dict[str, Callable[[str], bool]]
) -> list[dict[str, str]]:
    """Generic CSV processor with header detection.

    Processes CSV files with or without headers by automatically detecting the
    column order. For files with headers, uses DictReader directly. For headerless
    files, detects column order by validating sample data against expected validators.

    Args:
        filename: Path to the CSV file to process
        expected_columns: Dictionary mapping column names to validator functions
                         that check if a value is valid for that column

    Returns:
        List of dictionaries, where each dictionary represents a row with
        column names as keys and cell values as strings

    Raises:
        ValueError: If file is empty, exceeds size limit, has wrong number of
                   columns, or missing required headers
    """
    # Validate file size
    size = os.path.getsize(filename)
    if size > MAX_FILE_SIZE_BYTES:
        size_mb = size / (1024 * 1024)
        raise ValueError(
            f"File size ({size_mb:.1f}MB) exceeds {MAX_FILE_SIZE_MB}MB limit. "
            f"Consider splitting into smaller batches."
        )

    rows: list[dict[str, str]] = []

    with open(filename, "r", newline="") as f:
        # Create DictReader - it will auto-read first row as fieldnames
        reader = csv.DictReader(f)

        # Check if auto-detected fieldnames are actual headers or data
        detected_fieldnames = reader.fieldnames
        if detected_fieldnames is None:
            raise ValueError("CSV file is empty")

        # Normalize and check if they match expected columns
        normalized_fieldnames = {fn.strip().lower() for fn in detected_fieldnames}
        expected_column_names = set(expected_columns.keys())

        has_headers = expected_column_names.issubset(normalized_fieldnames)

        if has_headers:
            # Headers exist - proceed normally with DictReader
            logger.info("CSV has headers, using DictReader")

            # Normalize fieldnames for consistent access
            reader.fieldnames = [fn.strip().lower() for fn in reader.fieldnames]

            # Validate required columns present
            if not expected_column_names.issubset(set(reader.fieldnames)):
                missing = expected_column_names - set(reader.fieldnames)
                raise ValueError(
                    f"Missing required columns: {missing}. "
                    f"Expected: {', '.join(expected_column_names)}"
                )

            # Process all rows
            for row in reader:
                row_normalized = {k.strip().lower(): v.strip() for k, v in row.items()}
                rows.append(row_normalized)

        else:
            # No headers - detected_fieldnames are actually data
            logger.info("CSV has no headers, using intelligent column detection")

            # We need to:
            # 1. Read more rows to sample for column detection
            # 2. Detect column order
            # 3. Process first row (which is in detected_fieldnames) manually
            # 4. Continue with remaining rows

            # Seek back to start and read all rows as raw data
            f.seek(0)
            all_rows = list(csv.reader(f))

            if not all_rows:
                raise ValueError("CSV file is empty")

            # Detect column order using sample rows
            col_mapping = detect_column_order(all_rows, expected_columns)

            # Process all rows with detected column order
            for row in all_rows:
                if len(row) != len(expected_columns):
                    logger.warning(
                        f"Expected {len(expected_columns)} columns, got {len(row)}, skipping"
                    )
                    continue

                # Build dict using detected column mapping
                row_dict = {}
                for col_name, col_idx in col_mapping.items():
                    row_dict[col_name] = row[col_idx].strip()

                rows.append(row_dict)

    logger.info(f"Parsed {len(rows)} rows from CSV")
    return rows


def process_repo_csv(filename: str) -> list[dict[str, str]]:
    """Process repository CSV file with header detection.

    Processes a CSV file containing repository information with columns for
    repo_url and repo_group_id. Supports both header and headerless formats.

    Args:
        filename: Path to the repository CSV file

    Returns:
        List of dictionaries with keys 'repo_url' and 'repo_group_id'

    Raises:
        ValueError: If file format is invalid or columns cannot be detected
    """
    return process_csv(
        filename,
        expected_columns={
            "repo_url": validate_git_url,
            "repo_group_id": validate_positive_int,
        },
    )


def process_repo_group_csv(filename: str) -> list[dict[str, str]]:
    """Process repository group CSV file with header detection.

    Processes a CSV file containing repository group information with columns
    for repo_group_id and repo_group_name. Supports both header and headerless formats.

    Args:
        filename: Path to the repository group CSV file

    Returns:
        List of dictionaries with keys 'repo_group_id' and 'repo_group_name'

    Raises:
        ValueError: If file format is invalid or columns cannot be detected
    """
    return process_csv(
        filename,
        expected_columns={
            "repo_group_id": validate_positive_int,
            "repo_group_name": lambda v: bool(v.strip()),
        },
    )
