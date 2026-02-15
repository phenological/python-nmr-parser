"""Tests for other XML parser functions."""

import pytest
from nmr_parser.xml_parsers import (
    read_qc,
    read_pacs,
    read_eretic,
    read_title
)


class TestReadQc:
    """Tests for read_qc function."""

    def test_read_plasma_qc(self, qc_plasma_xml):
        """Test reading plasma QC data."""
        if not qc_plasma_xml.exists():
            pytest.skip("Test data not available")

        qc = read_qc(qc_plasma_xml)
        assert qc is not None
        assert 'data' in qc
        assert 'version' in qc
        assert 'infos' in qc['data']
        assert 'tests' in qc['data']

    def test_read_urine_qc(self, qc_urine_xml):
        """Test reading urine QC data."""
        if not qc_urine_xml.exists():
            pytest.skip("Test data not available")

        qc = read_qc(qc_urine_xml)
        assert qc is not None

    def test_nonexistent_file(self):
        """Test reading non-existent file."""
        result = read_qc("nonexistent.xml")
        assert result is None


class TestReadPacs:
    """Tests for read_pacs function."""

    def test_read_pacs_xml(self, pacs_xml):
        """Test reading PACS data."""
        if not pacs_xml.exists():
            pytest.skip("Test data not available")

        pacs = read_pacs(pacs_xml)
        assert pacs is not None
        assert 'data' in pacs
        assert 'version' in pacs
        assert len(pacs['data']) == 16  # 16 metabolites

    def test_nonexistent_file(self):
        """Test reading non-existent file."""
        result = read_pacs("nonexistent.xml")
        assert result is None


class TestReadEretic:
    """Tests for read_eretic function."""

    def test_read_eretic_xml(self, eretic_xml):
        """Test reading ERETIC calibration."""
        if not eretic_xml.exists():
            pytest.skip("Test data not available")

        eretic = read_eretic(eretic_xml)
        assert eretic is not None
        assert 'ereticFactor' in eretic.columns
        assert eretic['ereticFactor'].iloc[0] > 0

    def test_nonexistent_file(self):
        """Test reading non-existent file."""
        result = read_eretic("nonexistent.xml")
        assert result is None


class TestReadTitle:
    """Tests for read_title function."""

    def test_read_singleline_title(self, title_singleline):
        """Test reading single-line title."""
        if not title_singleline.exists():
            pytest.skip("Test data not available")

        title = read_title(title_singleline)
        assert title is not None
        assert 'value' in title
        assert isinstance(title['value'], str)

    def test_read_multiline_title(self, title_multiline):
        """Test reading multi-line title."""
        if not title_multiline.exists():
            pytest.skip("Test data not available")

        title = read_title(title_multiline)
        assert title is not None
        assert '\n' in title['value']  # Should contain newlines

    def test_nonexistent_file(self):
        """Test reading non-existent file."""
        result = read_title("nonexistent")
        assert result is None
