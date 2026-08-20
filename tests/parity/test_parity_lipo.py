"""The lipoprotein readers must agree with the R implementation.

The two packages ship byte-identical fixtures, so R's answers are recorded
in golden_r.json and asserted here. Running these does not need R.
"""

import pytest

from nmr_parser import read_lipo, extend_lipo


def _extended(lipo_file):
    ext = extend_lipo(read_lipo(lipo_file))
    data = ext["data"] if isinstance(ext, dict) else ext
    return dict(zip(data["id"], data["value"]))


class TestReadLipoParity:
    def test_same_parameters_in_the_same_order(self, golden, lipo_xml):
        assert list(read_lipo(lipo_xml)["data"]["id"]) == golden["read_lipo"]["id"]

    def test_same_version(self, golden, lipo_xml):
        assert read_lipo(lipo_xml)["version"] == golden["read_lipo"]["version"]

    @pytest.mark.parametrize("column", ["value", "refMax", "refMin"])
    def test_same_values(self, golden, lipo_xml, column):
        got = list(read_lipo(lipo_xml)["data"][column])
        assert got == pytest.approx(golden["read_lipo"][column], rel=1e-9)


class TestExtendLipoParity:
    """This is the one issue #1 broke: 36 of 316 values disagreed with R."""

    def test_same_parameters(self, golden, lipo_xml):
        assert set(_extended(lipo_xml)) == set(golden["extend_lipo"]["id"])

    @pytest.mark.xfail(
        reason="known divergence: pivot() alphabetises the raw block while R "
               "keeps Bruker's document order. Values agree, only the row "
               "order differs.",
        strict=True,
    )
    def test_same_order_as_r(self, golden, lipo_xml):
        assert list(_extended(lipo_xml)) == golden["extend_lipo"]["id"]

    def test_every_derived_value_matches_r(self, golden, lipo_xml):
        values = _extended(lipo_xml)
        mismatched = [
            ident
            for ident, expected in zip(golden["extend_lipo"]["id"],
                                       golden["extend_lipo"]["value"])
            if values[ident] != pytest.approx(expected, rel=1e-9, nan_ok=True)
        ]
        assert mismatched == []
