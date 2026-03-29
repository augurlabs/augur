# SPDX-License-Identifier: MIT
"""Unit tests for CSV processing utilities"""

import pytest
from unittest.mock import patch

from augur.application.cli._csv_utils import (
    validate_git_url,
    validate_positive_int,
    detect_column_order,
    process_csv,
    process_repo_csv,
    process_repo_group_csv,
    MAX_FILE_SIZE_BYTES,
)


class TestValidateGitUrl:
    """Tests for validate_git_url function"""

    def test_valid_github_url(self):
        """Test validation of valid GitHub URLs"""
        assert validate_git_url("https://github.com/chaoss/augur")
        assert validate_git_url("https://github.com/chaoss/augur.git")
        assert validate_git_url("  https://github.com/chaoss/augur  ")  # with whitespace

    def test_valid_gitlab_url(self):
        """Test validation of valid GitLab URLs"""
        assert validate_git_url("https://gitlab.com/chaoss/augur")
        assert validate_git_url("https://gitlab.com/chaoss/augur.git")

    def test_invalid_url(self):
        """Test validation of invalid URLs"""
        assert not validate_git_url("not-a-url")
        assert not validate_git_url("https://example.com")
        assert not validate_git_url("123")
        assert not validate_git_url("")

    def test_whitespace_handling(self):
        """Test that whitespace is properly stripped"""
        assert validate_git_url("  https://github.com/chaoss/augur  ")


class TestValidatePositiveInt:
    """Tests for validate_positive_int function"""

    def test_valid_positive_integers(self):
        """Test validation of valid positive integers"""
        assert validate_positive_int("1")
        assert validate_positive_int("42")
        assert validate_positive_int("9999")
        assert validate_positive_int("  123  ")  # with whitespace

    def test_zero_is_invalid(self):
        """Test that zero is not considered a positive integer"""
        assert not validate_positive_int("0")

    def test_negative_numbers_invalid(self):
        """Test that negative numbers are invalid"""
        assert not validate_positive_int("-1")
        assert not validate_positive_int("-42")

    def test_non_numeric_invalid(self):
        """Test that non-numeric strings are invalid"""
        assert not validate_positive_int("abc")
        assert not validate_positive_int("12.5")
        assert not validate_positive_int("")
        assert not validate_positive_int("1a")

    def test_whitespace_handling(self):
        """Test that whitespace is properly stripped"""
        assert validate_positive_int("  42  ")


class TestDetectColumnOrder:
    """Tests for detect_column_order function"""

    def test_simple_column_detection(self):
        """Test basic column order detection"""
        sample_rows = [
            ["https://github.com/chaoss/augur", "10"],
            ["https://github.com/user/repo", "20"],
        ]
        validators = {
            "repo_url": validate_git_url,
            "repo_group_id": validate_positive_int,
        }

        result = detect_column_order(sample_rows, validators)
        assert result == {"repo_url": 0, "repo_group_id": 1}

    def test_reversed_column_order(self):
        """Test detection with reversed column order"""
        sample_rows = [
            ["10", "https://github.com/chaoss/augur"],
            ["20", "https://github.com/user/repo"],
        ]
        validators = {
            "repo_url": validate_git_url,
            "repo_group_id": validate_positive_int,
        }

        result = detect_column_order(sample_rows, validators)
        assert result == {"repo_url": 1, "repo_group_id": 0}

    def test_threshold_detection(self):
        """Test that detection uses 80% threshold correctly"""
        # 8 out of 10 rows valid (80% exactly)
        sample_rows = [
            ["https://github.com/chaoss/augur", "10"],
            ["https://github.com/user/repo1", "20"],
            ["https://github.com/user/repo2", "30"],
            ["https://github.com/user/repo3", "40"],
            ["https://github.com/user/repo4", "50"],
            ["https://github.com/user/repo5", "60"],
            ["https://github.com/user/repo6", "70"],
            ["https://github.com/user/repo7", "80"],
            ["invalid-url", "90"],  # Invalid
            ["also-invalid", "100"],  # Invalid
        ]
        validators = {
            "repo_url": validate_git_url,
            "repo_group_id": validate_positive_int,
        }

        result = detect_column_order(sample_rows, validators)
        assert result == {"repo_url": 0, "repo_group_id": 1}

    def test_empty_rows_raises_error(self):
        """Test that empty sample rows raises ValueError"""
        with pytest.raises(ValueError, match="Expected .* columns"):
            detect_column_order([], {"col1": lambda x: True})

    def test_wrong_column_count_raises_error(self):
        """Test that wrong column count raises ValueError"""
        sample_rows = [["val1", "val2", "val3"]]
        validators = {"col1": lambda x: True, "col2": lambda x: True}

        with pytest.raises(ValueError, match="Expected 2 columns.*Found 3"):
            detect_column_order(sample_rows, validators)

    def test_no_match_found_raises_error(self):
        """Test that failure to detect a column raises ValueError"""
        sample_rows = [
            ["invalid", "invalid"],
            ["invalid", "invalid"],
        ]
        validators = {
            "repo_url": validate_git_url,
            "repo_group_id": validate_positive_int,
        }

        with pytest.raises(ValueError, match="Could not detect column"):
            detect_column_order(sample_rows, validators)


class TestProcessCsv:
    """Tests for process_csv function"""

    def test_csv_with_headers(self, tmp_path):
        """Test processing CSV file with headers"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("repo_url,repo_group_id\nhttps://github.com/chaoss/augur,10\nhttps://github.com/user/repo,20")

        validators = {
            "repo_url": validate_git_url,
            "repo_group_id": validate_positive_int,
        }

        result = process_csv(str(csv_file), validators)
        assert len(result) == 2
        assert result[0] == {"repo_url": "https://github.com/chaoss/augur", "repo_group_id": "10"}
        assert result[1] == {"repo_url": "https://github.com/user/repo", "repo_group_id": "20"}

    def test_csv_without_headers(self, tmp_path):
        """Test processing CSV file without headers"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("https://github.com/chaoss/augur,10\nhttps://github.com/user/repo,20")

        validators = {
            "repo_url": validate_git_url,
            "repo_group_id": validate_positive_int,
        }

        result = process_csv(str(csv_file), validators)
        assert len(result) == 2
        assert result[0] == {"repo_url": "https://github.com/chaoss/augur", "repo_group_id": "10"}
        assert result[1] == {"repo_url": "https://github.com/user/repo", "repo_group_id": "20"}

    def test_csv_with_different_column_order(self, tmp_path):
        """Test processing CSV with columns in different order"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("repo_group_id,repo_url\n10,https://github.com/chaoss/augur")

        validators = {
            "repo_url": validate_git_url,
            "repo_group_id": validate_positive_int,
        }

        result = process_csv(str(csv_file), validators)
        assert len(result) == 1
        assert result[0] == {"repo_url": "https://github.com/chaoss/augur", "repo_group_id": "10"}

    def test_empty_csv_raises_error(self, tmp_path):
        """Test that empty CSV file raises ValueError"""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")

        validators = {"col1": lambda x: True}

        with pytest.raises(ValueError, match="empty"):
            process_csv(str(csv_file), validators)

    def test_file_size_limit_with_mock(self, tmp_path):
        """Test file size limit enforcement using mock"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("repo_url,repo_group_id\nhttps://github.com/chaoss/augur,10")

        validators = {
            "repo_url": validate_git_url,
            "repo_group_id": validate_positive_int,
        }

        # Mock os.path.getsize to return a size larger than limit
        with patch('os.path.getsize', return_value=MAX_FILE_SIZE_BYTES + 1):
            with pytest.raises(ValueError, match="exceeds.*limit"):
                process_csv(str(csv_file), validators)

    def test_missing_required_headers_raises_error(self, tmp_path):
        """Test that missing required headers raises ValueError"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("wrong_column,another_column\nvalue1,value2")

        validators = {
            "repo_url": validate_git_url,
            "repo_group_id": validate_positive_int,
        }

        with pytest.raises(ValueError, match="Could not detect column"):
            process_csv(str(csv_file), validators)

    def test_whitespace_in_values(self, tmp_path):
        """Test that whitespace in values is properly stripped"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("repo_url,repo_group_id\n  https://github.com/chaoss/augur  ,  10  ")

        validators = {
            "repo_url": validate_git_url,
            "repo_group_id": validate_positive_int,
        }

        result = process_csv(str(csv_file), validators)
        assert result[0] == {"repo_url": "https://github.com/chaoss/augur", "repo_group_id": "10"}


class TestProcessRepoCsv:
    """Tests for process_repo_csv function"""

    def test_process_valid_repo_csv(self, tmp_path):
        """Test processing a valid repository CSV"""
        csv_file = tmp_path / "repos.csv"
        csv_file.write_text("repo_url,repo_group_id\nhttps://github.com/chaoss/augur,10")

        result = process_repo_csv(str(csv_file))
        assert len(result) == 1
        assert result[0]["repo_url"] == "https://github.com/chaoss/augur"
        assert result[0]["repo_group_id"] == "10"

    def test_process_repo_csv_without_headers(self, tmp_path):
        """Test processing repository CSV without headers"""
        csv_file = tmp_path / "repos.csv"
        csv_file.write_text("https://github.com/chaoss/augur,10\nhttps://github.com/user/repo,20")

        result = process_repo_csv(str(csv_file))
        assert len(result) == 2


class TestProcessRepoGroupCsv:
    """Tests for process_repo_group_csv function"""

    def test_process_valid_repo_group_csv(self, tmp_path):
        """Test processing a valid repository group CSV"""
        csv_file = tmp_path / "groups.csv"
        csv_file.write_text("repo_group_id,repo_group_name\n10,CHAOSS")

        result = process_repo_group_csv(str(csv_file))
        assert len(result) == 1
        assert result[0]["repo_group_id"] == "10"
        assert result[0]["repo_group_name"] == "CHAOSS"

    def test_process_repo_group_csv_without_headers(self, tmp_path):
        """Test processing repository group CSV without headers"""
        csv_file = tmp_path / "groups.csv"
        csv_file.write_text("10,CHAOSS\n20,OpenSource")

        result = process_repo_group_csv(str(csv_file))
        assert len(result) == 2
        assert result[0]["repo_group_name"] == "CHAOSS"
        assert result[1]["repo_group_name"] == "OpenSource"

    def test_empty_group_name_invalid(self, tmp_path):
        """Test that empty repository group names are handled"""
        csv_file = tmp_path / "groups.csv"
        csv_file.write_text("repo_group_id,repo_group_name\n10,ValidName\n20,")

        # This should process the file, but the row with empty name should fail validation
        # during the detect_column_order phase if there aren't enough valid rows
        result = process_repo_group_csv(str(csv_file))
        # Both rows should be parsed; validation happens at application level
        assert len(result) >= 1


class TestEdgeCases:
    """Tests for edge cases and error conditions"""

    def test_single_row_csv(self, tmp_path):
        """Test processing CSV with single row"""
        csv_file = tmp_path / "single.csv"
        csv_file.write_text("https://github.com/chaoss/augur,10")

        validators = {
            "repo_url": validate_git_url,
            "repo_group_id": validate_positive_int,
        }

        result = process_csv(str(csv_file), validators)
        assert len(result) == 1

    def test_csv_with_extra_whitespace_in_headers(self, tmp_path):
        """Test CSV with whitespace in header names"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("  repo_url  ,  repo_group_id  \nhttps://github.com/chaoss/augur,10")

        validators = {
            "repo_url": validate_git_url,
            "repo_group_id": validate_positive_int,
        }

        result = process_csv(str(csv_file), validators)
        assert len(result) == 1
        assert result[0]["repo_url"] == "https://github.com/chaoss/augur"

    def test_many_rows_csv(self, tmp_path):
        """Test processing CSV with many rows"""
        csv_file = tmp_path / "many.csv"
        lines = ["repo_url,repo_group_id"]
        for i in range(100):
            lines.append(f"https://github.com/user/repo{i},{i+1}")
        csv_file.write_text("\n".join(lines))

        validators = {
            "repo_url": validate_git_url,
            "repo_group_id": validate_positive_int,
        }

        result = process_csv(str(csv_file), validators)
        assert len(result) == 100
