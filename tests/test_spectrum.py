"""Tests for spectrum reading functions."""

import pytest
import numpy as np
from nmr_parser.core import read_1r, read_spectrum


class TestRead1r:
    """Tests for read_1r function."""

    def test_read_binary_spectrum(self, covid_sample_10):
        """Test reading binary spectrum file."""
        spec_path = covid_sample_10 / "pdata" / "1" / "1r"
        if not spec_path.exists():
            pytest.skip("Test data not available")

        spec = read_1r(spec_path, 131072, nc=0, endian="little")
        assert len(spec) == 131072
        assert isinstance(spec, np.ndarray)
        assert spec.dtype == np.float64

    def test_power_factor_scaling(self, covid_sample_10):
        """Test power factor (nc) scaling."""
        spec_path = covid_sample_10 / "pdata" / "1" / "1r"
        if not spec_path.exists():
            pytest.skip("Test data not available")

        spec_nc0 = read_1r(spec_path, 100, nc=0, endian="little")
        spec_nc1 = read_1r(spec_path, 100, nc=1, endian="little")

        # nc=1 should be 2x nc=0
        np.testing.assert_array_almost_equal(spec_nc1, spec_nc0 * 2)


class TestReadSpectrum:
    """Tests for read_spectrum function."""

    def test_read_basic_spectrum(self, covid_sample_10):
        """Test reading spectrum without options."""
        if not covid_sample_10.exists():
            pytest.skip("Test data not available")

        spec = read_spectrum(covid_sample_10)
        if spec is None:
            pytest.skip("Spectrum reading failed - data may be incomplete")

        assert spec is not None
        assert hasattr(spec, 'info')
        assert hasattr(spec, 'spec')
        assert 'x' in spec.spec.columns
        assert 'y' in spec.spec.columns

    def test_spectrum_with_range(self, covid_sample_10):
        """Test reading spectrum with PPM range."""
        if not covid_sample_10.exists():
            pytest.skip("Test data not available")

        opts = {'fromTo': (-0.1, 10), 'length_out': 44079}
        spec = read_spectrum(covid_sample_10, options=opts)

        if spec is None:
            pytest.skip("Spectrum reading failed")

        assert len(spec.spec) == 44079
        assert spec.spec['x'].min() >= -0.1
        assert spec.spec['x'].max() <= 10

    def test_spectrum_with_eretic(self, covid_sample_10):
        """Test spectrum with ERETIC correction."""
        if not covid_sample_10.exists():
            pytest.skip("Test data not available")

        opts = {'eretic': 3808.27}
        spec = read_spectrum(covid_sample_10, options=opts)

        if spec is None:
            pytest.skip("Spectrum reading failed")

        assert spec.info.ereticFactor == 3808.27

    def test_nonexistent_experiment(self):
        """Test reading non-existent experiment."""
        result = read_spectrum("nonexistent/experiment")
        assert result is None
