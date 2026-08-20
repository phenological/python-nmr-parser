"""read_quant must agree with the R implementation on both document shapes."""

import pandas as pd
import pytest

from nmr_parser import read_quant


FIXTURES = {
    "plasma_standard": "HB-COVID0001/10/pdata/1/plasma_quant_report.xml",
    "plasma_extended": "HB-COVID0001/10/pdata/1/plasma_quant_report_ver_1_0.xml",
    "urine_e": "urine_quant_report_e.xml",
}


def _as_r(series):
    """R records NA as null; pandas carries NaN or None. Compare as text."""
    return [None if pd.isna(v) else str(v) for v in series]


@pytest.fixture(params=sorted(FIXTURES))
def case(request, golden, test_data_dir):
    name = request.param
    if name not in golden["read_quant"]:
        pytest.skip(f"no golden recorded for {name}")
    data = read_quant(test_data_dir / FIXTURES[name])["data"]
    return name, golden["read_quant"][name], data


class TestReadQuantParity:
    def test_same_compounds_in_the_same_order(self, case):
        _, expected, got = case
        assert list(got["name"]) == expected["name"]

    def test_same_count(self, case):
        _, expected, got = case
        assert len(got) == expected["n"]

    @pytest.mark.parametrize("column", ["conc_v", "rawConc", "conc_vr", "refMax", "refMin"])
    def test_same_values(self, case, column):
        name, expected, got = case
        assert _as_r(got[column]) == expected[column], f"{name}.{column}"
