"""Tests for the spcglyc biomarker calculation."""

import numpy as np
import pandas as pd
import pytest

from nmr_parser.core.parse_nmr import _calculate_spcglyc


class _SilentLog:
    def debug(self, *a, **k): pass
    def info(self, *a, **k): pass
    def warning(self, *a, **k): pass
    def step(self, *a, **k): pass


def _synthetic_spectrum(n_points=4000):
    """A spectrum with signal in the SPC, Glyc and albumin windows.

    Values are arbitrary; what the tests check is how the calculation
    transforms them, not the numbers themselves.
    """
    ppm = np.linspace(-0.5, 10.5, n_points)
    y = np.zeros(n_points)
    rng = np.random.default_rng(0)
    for centre, height in [(3.28, 40.0), (3.25, 25.0), (3.21, 15.0),
                           (2.07, 30.0), (2.10, 20.0),
                           (0.45, 10.0), (7.5, 8.0)]:
        y += height * np.exp(-0.5 * ((ppm - centre) / 0.01) ** 2)
    y += rng.normal(0, 1e-6, n_points)
    return ppm, y


def _run(paths):
    ppm, y = _synthetic_spectrum()
    spectra = np.vstack([y for _ in paths])
    loe = pd.DataFrame({"dataPath": list(paths),
                        "experiment": ["noesygppr1d"] * len(paths)})
    matrix, var_names, extra = _calculate_spcglyc(spectra, ppm, loe, _SilentLog())
    return pd.DataFrame(matrix, columns=var_names), extra


class TestThreeMillimetreCorrection:
    """The 3mm correction must not reach the ratios (issue #2).

    SPC3_2 is SPC3/SPC2 and SPC_Glyc is SPC_All/Glyc_All. Both numerator and
    denominator are already halved, so the tube divides out and the ratio
    must be left alone.
    """

    def test_the_integrals_are_halved(self):
        df, _ = _run(["/data/normal/10", "/data/3mm/10"])
        for column in ["SPC_All", "SPC3", "SPC2", "SPC1",
                       "Glyc_All", "GlycA", "GlycB", "Alb1", "Alb2"]:
            assert df[column].iloc[1] == pytest.approx(df[column].iloc[0] / 2), column

    @pytest.mark.parametrize("ratio", ["SPC3_2", "SPC_Glyc"])
    def test_the_ratios_are_not(self, ratio):
        df, _ = _run(["/data/normal/10", "/data/3mm/10"])
        assert df[ratio].iloc[1] == pytest.approx(df[ratio].iloc[0]), (
            f"{ratio} was halved along with the integrals")

    def test_the_ratios_still_equal_their_definition_after_correction(self):
        df, _ = _run(["/data/normal/10", "/data/3mm/10"])
        for i in (0, 1):
            assert df["SPC3_2"].iloc[i] == pytest.approx(
                df["SPC3"].iloc[i] / df["SPC2"].iloc[i])
            assert df["SPC_Glyc"].iloc[i] == pytest.approx(
                df["SPC_All"].iloc[i] / df["Glyc_All"].iloc[i])

    def test_a_run_with_no_3mm_paths_is_untouched(self):
        plain, _ = _run(["/data/normal/10"])
        mixed, _ = _run(["/data/normal/10", "/data/3mm/10"])
        for column in plain.columns:
            assert mixed[column].iloc[0] == pytest.approx(plain[column].iloc[0]), column

    def test_the_match_is_case_insensitive(self):
        df, _ = _run(["/data/normal/10", "/data/3MM/10"])
        assert df["SPC_All"].iloc[1] == pytest.approx(df["SPC_All"].iloc[0] / 2)
        assert df["SPC3_2"].iloc[1] == pytest.approx(df["SPC3_2"].iloc[0])
