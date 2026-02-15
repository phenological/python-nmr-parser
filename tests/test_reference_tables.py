"""Tests for reference table functions."""

import pytest
from nmr_parser.reference import (
    get_lipo_table,
    get_qc_table,
    get_pacs_table,
    get_sm_table
)


class TestReferenceTables:
    """Tests for reference table functions."""

    def test_get_lipo_table(self):
        """Test getting lipoprotein reference table."""
        try:
            lipo = get_lipo_table()
            assert lipo is not None
            assert len(lipo) > 0
        except FileNotFoundError:
            pytest.skip("Reference data CSV not available")

    def test_get_qc_table_serum(self):
        """Test getting serum QC reference table."""
        qc = get_qc_table("SER")
        assert qc is not None
        assert 'testName' in qc.columns

    def test_get_qc_table_urine(self):
        """Test getting urine QC reference table."""
        qc = get_qc_table("URI")
        assert qc is not None
        assert 'testName' in qc.columns

    def test_get_pacs_table(self):
        """Test getting PACS reference table."""
        pacs = get_pacs_table()
        assert pacs is not None
        assert len(pacs) == 16  # 16 metabolites
        assert 'name' in pacs.columns

    def test_get_sm_table_plasma(self):
        """Test getting plasma metabolite table."""
        try:
            sm = get_sm_table("PLA")
            assert sm is not None
            assert len(sm) == 41  # 41 plasma metabolites
        except FileNotFoundError:
            pytest.skip("Reference data CSV not available")

    def test_get_sm_table_urine(self):
        """Test getting urine metabolite table."""
        try:
            sm = get_sm_table("URI")
            assert sm is not None
            assert len(sm) == 150  # 150 urine metabolites
        except FileNotFoundError:
            pytest.skip("Reference data CSV not available")

    def test_lipo_table_caching(self):
        """Test that lipo table is cached."""
        try:
            lipo1 = get_lipo_table()
            lipo2 = get_lipo_table()
            # Should be the same object due to @lru_cache
            assert lipo1 is lipo2
        except FileNotFoundError:
            pytest.skip("Reference data CSV not available")
