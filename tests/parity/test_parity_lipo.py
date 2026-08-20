"""The lipoprotein readers must agree with the R implementation.

The two packages ship byte-identical fixtures, so R's answers are recorded
in golden_r.json and asserted here. Running these does not need R.

Two report versions are covered. lipo_results.xml is PL-5009-01/001, the
older name the fixtures grew up with; plasma_lipo_report_1_1_0.xml is /002
and is what the instruments write now. They carry the same 112 parameters,
the same units and the same reference ranges, so this is about keeping
parity asserted on the version that actually occurs, not about a difference
in behaviour.
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


class TestCurrentReportVersionParity:
    """The same assertions against PL-5009-01/002, the version in use."""

    @pytest.fixture
    def current_lipo(self, test_data_dir):
        return test_data_dir / "plasma_lipo_report_1_1_0.xml"

    def test_same_version(self, golden, current_lipo):
        assert read_lipo(current_lipo)["version"] == golden["read_lipo_current"]["version"]

    def test_same_parameters_in_the_same_order(self, golden, current_lipo):
        assert list(read_lipo(current_lipo)["data"]["id"]) == golden["read_lipo_current"]["id"]

    @pytest.mark.parametrize("column", ["value", "refMax", "refMin"])
    def test_same_values(self, golden, current_lipo, column):
        got = list(read_lipo(current_lipo)["data"][column])
        assert got == pytest.approx(golden["read_lipo_current"][column], rel=1e-9)

    def test_every_derived_value_matches_r(self, golden, current_lipo):
        values = _extended(current_lipo)
        mismatched = [
            ident
            for ident, expected in zip(golden["extend_lipo_current"]["id"],
                                       golden["extend_lipo_current"]["value"])
            if values[ident] != pytest.approx(expected, rel=1e-9, nan_ok=True)
        ]
        assert mismatched == []

    def test_the_two_report_versions_carry_the_same_parameters(self, lipo_xml, current_lipo):
        """Same schema, so a change that broke one would break the other."""
        old = read_lipo(lipo_xml)["data"]
        new = read_lipo(current_lipo)["data"]
        assert list(old["id"]) == list(new["id"])
        assert list(old["unit"]) == list(new["unit"])
        assert list(old["refMax"]) == list(new["refMax"])
