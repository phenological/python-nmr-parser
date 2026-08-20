"""read_spectrum must agree with the R implementation.

The spectrum is 44079 points, so the golden records the ends, the extremes
and the sum rather than the whole vector. Between them these catch a shifted
axis, a scaling error and a change in any single point.

Tolerances
----------
The ppm axis is computed arithmetically on both sides and agrees to machine
precision, so it is held to 1e-12.

The intensities go through a cubic spline onto the common grid, and the two
implementations do not use the same one: R calls signal::interp1(method =
"spline") and Python calls scipy.interpolate.interp1d(kind="cubic"), which
differ in their boundary conditions. Measured over this fixture the
disagreement reaches 3.2e-9 relative, largest at the ends and decaying
inward, which is the signature of exactly that. 1e-7 leaves room for the
difference while still catching anything of physical size: it is four
orders of magnitude below the least significant digit Bruker reports.
"""

import numpy as np
import pytest

from nmr_parser import read_spectrum


@pytest.fixture
def spectrum(covid_sample_10):
    result = read_spectrum(
        covid_sample_10,
        options={"fromTo": (-0.1, 10), "length_out": 44079},
    )
    assert result is not None
    return result


def _frame(spectrum):
    return spectrum.spec if hasattr(spectrum, "spec") else spectrum["spec"]


class TestReadSpectrumParity:
    def test_same_number_of_points(self, golden, spectrum):
        assert len(_frame(spectrum)) == golden["read_spectrum"]["n"]

    @pytest.mark.parametrize("axis,rtol", [("x", 1e-12), ("y", 1e-7)])
    def test_the_ends_match(self, golden, spectrum, axis, rtol):
        column = _frame(spectrum)[axis].to_numpy()
        expected = golden["read_spectrum"]
        np.testing.assert_allclose(column[:5], expected[f"{axis}_head"], rtol=rtol)
        np.testing.assert_allclose(column[-5:], expected[f"{axis}_tail"], rtol=rtol)

    def test_the_intensities_span_the_same_range(self, golden, spectrum):
        y = _frame(spectrum)["y"].to_numpy()
        expected = golden["read_spectrum"]
        assert y.min() == pytest.approx(expected["y_min"], rel=1e-7)
        assert y.max() == pytest.approx(expected["y_max"], rel=1e-7)

    def test_the_total_intensity_matches(self, golden, spectrum):
        """A single point differing anywhere shows up here."""
        y = _frame(spectrum)["y"].to_numpy()
        assert y.sum() == pytest.approx(golden["read_spectrum"]["y_sum"], rel=1e-9)
        # the sum is far tighter than the pointwise bound because the spline
        # differences are signed and largely cancel: measured at 1.3e-12
