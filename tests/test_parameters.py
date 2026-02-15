"""Tests for parameter reading functions."""

import pytest
from nmr_parser.core import read_param, read_params


class TestReadParam:
    """Tests for read_param function."""

    def test_read_single_param(self, covid_sample_10):
        """Test reading a single parameter."""
        acqus_path = covid_sample_10 / "acqus"
        if not acqus_path.exists():
            pytest.skip("Test data not available")

        pulprog = read_param(acqus_path, "PULPROG")
        assert pulprog is not None
        assert isinstance(pulprog, str)

    def test_read_multiple_params(self, covid_sample_10):
        """Test reading multiple parameters."""
        acqus_path = covid_sample_10 / "acqus"
        if not acqus_path.exists():
            pytest.skip("Test data not available")

        params = read_param(acqus_path, ["BF1", "NS"])
        assert params is not None
        assert len(params) == 2

    def test_nonexistent_file(self):
        """Test reading from non-existent file."""
        result = read_param("nonexistent/acqus", "PULPROG")
        assert result is None

    def test_nonexistent_param(self, covid_sample_10):
        """Test reading non-existent parameter."""
        acqus_path = covid_sample_10 / "acqus"
        if not acqus_path.exists():
            pytest.skip("Test data not available")

        result = read_param(acqus_path, "NONEXISTENT_PARAM")
        assert result is None


class TestReadParams:
    """Tests for read_params function."""

    def test_read_all_params(self, covid_sample_10):
        """Test reading all parameters from file."""
        acqus_path = covid_sample_10 / "acqus"
        if not acqus_path.exists():
            pytest.skip("Test data not available")

        params = read_params(acqus_path)
        assert params is not None
        assert len(params) > 0
        assert 'name' in params.columns
        assert 'value' in params.columns
        assert 'path' in params.columns

    def test_nonexistent_file(self):
        """Test reading from non-existent file."""
        result = read_params("nonexistent/acqus")
        assert result is None

    def test_empty_file(self, tmp_path):
        """Test reading empty file."""
        empty_file = tmp_path / "empty_acqus"
        empty_file.touch()
        result = read_params(empty_file)
        assert result is None
