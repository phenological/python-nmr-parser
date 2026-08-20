"""Tests for quantification XML parsing."""

from pathlib import Path

import pandas as pd
import pytest

from nmr_parser.xml_parsers import read_quant


class TestReadQuant:
    """Tests for read_quant function."""

    def test_plasma_quant_standard(self, plasma_quant_xml):
        """Test reading plasma quantification (standard format)."""
        if not plasma_quant_xml.exists():
            pytest.skip("Test data not available")

        quant = read_quant(plasma_quant_xml)
        assert quant is not None
        assert 'data' in quant
        assert 'version' in quant
        assert len(quant['data']) == 41  # 41 compounds in plasma
        assert 'name' in quant['data'].columns
        assert 'rawConc' in quant['data'].columns

    def test_plasma_quant_2_1_0(self, plasma_quant_2_1_0_xml):
        """Test reading plasma quantification v2.1.0."""
        if not plasma_quant_2_1_0_xml.exists():
            pytest.skip("Test data not available")

        quant = read_quant(plasma_quant_2_1_0_xml)
        assert quant is not None
        assert len(quant['data']) == 41
        assert '2.1.0' in quant['version']

    def test_urine_quant_b(self, urine_quant_b_xml):
        """Test reading urine B quantification."""
        if not urine_quant_b_xml.exists():
            pytest.skip("Test data not available")

        quant = read_quant(urine_quant_b_xml)
        assert quant is not None
        assert len(quant['data']) == 50  # 50 compounds in urine B

    def test_urine_quant_e(self, urine_quant_e_xml):
        """Test reading urine E quantification."""
        if not urine_quant_e_xml.exists():
            pytest.skip("Test data not available")

        quant = read_quant(urine_quant_e_xml)
        assert quant is not None
        assert len(quant['data']) == 150  # 150 compounds in urine E

    def test_version_detection(self, plasma_quant_xml):
        """Test version detection."""
        if not plasma_quant_xml.exists():
            pytest.skip("Test data not available")

        quant = read_quant(plasma_quant_xml)
        assert 'Quant' in quant['version']

    def test_nonexistent_file(self):
        """Test reading non-existent file."""
        result = read_quant("nonexistent.xml")
        assert result is None


def _mutate(xml_path, tmp_path, transform):
    """Write a copy of the report with one PARAMETER rewritten."""
    import re
    source = Path(xml_path).read_text()
    params = list(re.finditer(r"<PARAMETER\b.*?</PARAMETER>", source, re.S))
    out = transform(source, params)
    target = tmp_path / "mutated_quant_report.xml"
    target.write_text(out)
    return target


class TestStandardFormatAlignment:
    """A parameter with fewer children must not shift the others (issue #8).

    Every attribute used to be swept from the whole document and the lists
    zipped by position, then padded to length, so one missing node moved
    every later compound onto its neighbour's numbers with no error.
    """

    def test_a_missing_reference_affects_only_that_compound(self, urine_quant_e_xml, tmp_path):
        import re
        def drop_reference_of_param_5(source, params):
            victim = params[5]
            return (source[:victim.start()]
                    + re.sub(r"\s*<REFERENCE\b[^>]*/>", "", victim.group(0))
                    + source[victim.end():])

        mutated = _mutate(urine_quant_e_xml, tmp_path, drop_reference_of_param_5)

        ok = read_quant(urine_quant_e_xml)["data"]
        got = read_quant(mutated)["data"]

        assert len(got) == len(ok)
        assert list(got["name"]) == list(ok["name"])

        # the one that lost its reference reads as missing
        assert pd.isna(got["refMax"].iloc[5])
        # and nothing else moved
        for i in range(len(ok)):
            if i == 5:
                continue
            assert got["refMax"].iloc[i] == ok["refMax"].iloc[i], f"row {i} shifted"

    def test_the_compound_without_a_valuerelative_is_the_one_that_reads_missing(
            self, urine_quant_e_xml):
        """Creatinine has no VALUERELATIVE in the urine reports. The old code
        hard coded a pad at the front, which is right only while that
        compound happens to be first."""
        data = read_quant(urine_quant_e_xml)["data"]
        creatinine = data.index[data["name"] == "Creatinine"]
        assert len(creatinine) == 1
        assert pd.isna(data["conc_vr"].iloc[creatinine[0]])
        # every other compound has one
        others = data.drop(index=creatinine[0])
        assert others["conc_vr"].notna().all()

    def test_moving_the_gap_moves_the_missing_value_with_it(self, urine_quant_e_xml, tmp_path):
        """Give the first compound a VALUERELATIVE and take another's away.
        The count is unchanged, so a positional reader cannot tell."""
        import re
        def move_the_gap(source, params):
            donor = re.search(r"<VALUERELATIVE\b[^>]*/>", params[1].group(0)).group(0)
            first = params[0].group(0).replace("</PARAMETER>", "  " + donor + "</PARAMETER>")
            tenth = re.sub(r"\s*<VALUERELATIVE\b[^>]*/>", "", params[10].group(0))
            return (source[:params[0].start()] + first
                    + source[params[0].end():params[10].start()] + tenth
                    + source[params[10].end():])

        mutated = _mutate(urine_quant_e_xml, tmp_path, move_the_gap)
        data = read_quant(mutated)["data"]

        # the gap is now on compound 10, not compound 0
        assert data["conc_vr"].notna().iloc[0]
        assert pd.isna(data["conc_vr"].iloc[10])
        assert data["conc_vr"].isna().sum() == 1
