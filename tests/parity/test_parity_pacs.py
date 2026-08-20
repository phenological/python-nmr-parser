"""read_pacs must agree with the R implementation."""

import pandas as pd
import pytest

from nmr_parser import read_pacs


def _as_r(series):
    return [None if pd.isna(v) else str(v) for v in series]


class TestReadPacsParity:
    def test_same_version(self, golden, pacs_xml):
        assert read_pacs(pacs_xml)["version"] == golden["read_pacs"]["version"]

    def test_same_parameters_in_the_same_order(self, golden, pacs_xml):
        assert list(read_pacs(pacs_xml)["data"]["name"]) == golden["read_pacs"]["name"]

    @pytest.mark.parametrize("column", ["conc_v", "refMax", "refMin"])
    def test_same_values(self, golden, pacs_xml, column):
        got = _as_r(read_pacs(pacs_xml)["data"][column])
        assert got == golden["read_pacs"][column]
