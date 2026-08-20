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


class TestParamAnchoring:
    """A name must match the declaration, not anywhere in the line (issue #10).

    acqus files are ordered alphabetically, so the first substring hit was
    routinely a longer parameter ending in the same letters.
    """

    @pytest.mark.parametrize("param,expected", [
        ("SW", 30.0344201255777),   # not LOCSW's 0
        ("TE", 310.0016),           # not DATE's timestamp
        ("RG", 83.46),              # not CPDPRG's "(0..8)"
        ("TD", 98304),              # not NusTD
        ("NS", 32),
        ("DE", 6.794558),
        ("BF1", 600.27),
    ])
    def test_reads_the_declared_value(self, covid_sample_10, param, expected):
        assert read_param(covid_sample_10 / "acqus", param) == pytest.approx(expected)

    def test_a_longer_parameter_does_not_answer_for_a_missing_one(self, covid_sample_10):
        """procs has no EXP, but it has MddCEXP, which used to answer for it."""
        procs = covid_sample_10 / "pdata" / "1" / "procs"
        assert read_param(procs, "EXP") is None

    def test_a_name_with_regexp_characters_is_taken_literally(self, tmp_path):
        acqus = tmp_path / "acqus"
        acqus.write_text("##TITLE= Parameter file\n##$A.B= 1\n##$AXB= 2\n##END=\n")
        assert read_param(acqus, "A.B") == 1
        assert read_param(acqus, "AXB") == 2

    def test_a_value_containing_equals_survives(self, tmp_path):
        acqus = tmp_path / "acqus"
        acqus.write_text("##TITLE= Parameter file\n##$USERA1= <a=b>\n##END=\n")
        assert read_param(acqus, "USERA1") == "a=b"
