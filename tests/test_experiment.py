"""Tests for read_experiment function."""

import pytest
from nmr_parser import read_experiment


class TestReadExperiment:
    """Tests for read_experiment function."""

    def test_read_single_experiment(self, covid_sample_10):
        """Test reading a single experiment."""
        if not covid_sample_10.exists():
            pytest.skip("Test data not available")

        result = read_experiment(covid_sample_10)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_read_multiple_experiments(self, covid_sample_10, covid_sample_11):
        """Test reading multiple experiments."""
        if not covid_sample_10.exists() or not covid_sample_11.exists():
            pytest.skip("Test data not available")

        result = read_experiment([covid_sample_10, covid_sample_11])
        assert isinstance(result, dict)

    def test_read_with_options(self, covid_sample_10):
        """Test reading with specific options."""
        if not covid_sample_10.exists():
            pytest.skip("Test data not available")

        opts = {"what": ["acqus", "procs"]}
        result = read_experiment(covid_sample_10, opts=opts)

        if 'acqus' in result:
            assert len(result['acqus']) > 0
        if 'procs' in result:
            assert len(result['procs']) > 0

    def test_read_spectrum_only(self, covid_sample_10):
        """Test reading spectrum only."""
        if not covid_sample_10.exists():
            pytest.skip("Test data not available")

        opts = {"what": ["spec"]}
        result = read_experiment(covid_sample_10, opts=opts)
        assert 'spec' in result

    def test_nonexistent_folder(self, test_data_dir):
        """Test reading non-existent folder."""
        result = read_experiment(test_data_dir / "nonexistent")
        assert isinstance(result, dict)

    def test_read_with_spec_options(self, covid_sample_10):
        """Test reading with spectrum options."""
        if not covid_sample_10.exists():
            pytest.skip("Test data not available")

        opts = {
            "what": ["spec"],
            "specOpts": {
                "fromTo": (-0.1, 10),
                "length_out": 44079
            }
        }
        result = read_experiment(covid_sample_10, opts=opts)
        assert 'spec' in result
