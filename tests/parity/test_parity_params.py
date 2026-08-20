"""read_param must agree with the R implementation on the same acqus."""

import pytest

from nmr_parser import read_param


class TestReadParamParity:
    def test_every_recorded_parameter_matches_r(self, golden, covid_sample_10):
        acqus = covid_sample_10 / "acqus"
        mismatched = {}
        for name, expected in golden["read_param"].items():
            got = read_param(acqus, name)
            if isinstance(expected, (int, float)) and not isinstance(expected, bool):
                if got != pytest.approx(expected, rel=1e-9):
                    mismatched[name] = (expected, got)
            elif str(got) != str(expected):
                mismatched[name] = (expected, got)
        assert mismatched == {}
