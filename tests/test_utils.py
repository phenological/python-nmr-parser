"""Tests for utility functions."""

import pytest
from nmr_parser.processing import clean_names


class TestCleanNames:
    """Tests for clean_names function."""

    def test_single_string(self):
        """Test cleaning a single string."""
        assert clean_names("ddd.aaa") == "ddd-aaa"

    def test_list_of_strings(self):
        """Test cleaning a list of strings."""
        result = clean_names(["ddd uuu", "ddd+aaa", "ddd*yyy"])
        assert result == ["ddd-uuu", "dddpaaa", "dddtyyy"]

    def test_special_characters(self):
        """Test handling of special characters."""
        original = ["ddd.aaa", "ddd uuu", "ddd+aaa", "ddd*yyy", "ddd#dd", "ddd_fff"]
        result = clean_names(original)
        assert "ddd-aaa" in result
        assert "ddd-uuu" in result
        assert "dddpaaa" in result
        assert "dddtyyy" in result
        assert "ddd#dd" in result  # # preserved for replicates
        assert "ddd_fff" in result

    def test_trailing_asterisk(self):
        """Test asterisk at end becomes -S."""
        assert clean_names("dad*") == "dad-s"

    def test_lowercase_conversion(self):
        """Test conversion to lowercase."""
        assert clean_names("DDD.AAA") == "ddd-aaa"

    def test_whitespace_handling(self):
        """Test whitespace removal."""
        assert clean_names("  ddd aaa  ") == "ddd-aaa"

    def test_duplicate_handling(self):
        """Test handling of duplicate names."""
        result = clean_names(["test", "test", "test"])
        assert result == ["test", "test#1", "test#2"]
