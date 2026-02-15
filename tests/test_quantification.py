"""Tests for quantification XML parsing."""

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
