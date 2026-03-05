"""Tests for reference table functions."""

import pandas as pd
import pytest
from pathlib import Path
from nmr_parser.reference import (
    get_lipo_table,
    get_qc_table,
    get_pacs_table,
    get_sm_table
)
from nmr_parser.xml_parsers import read_qc
from nmr_parser.xml_parsers.lipoproteins import read_lipo
from nmr_parser.xml_parsers.pacs import read_pacs

DATA_DIR = Path(__file__).parent.parent / "src" / "nmr_parser" / "reference" / "data"


class TestReferenceTables:
    """Tests for reference table functions."""

    def test_get_lipo_table(self):
        """Test getting lipoprotein reference table."""
        lipo = get_lipo_table()
        assert lipo is not None
        assert len(lipo) == 112  # 114 PARAMETER elements minus 2 duplicate ids

    def test_get_lipo_table_matches_xml(self):
        """Test that get_lipo_table() matches the raw XML content."""
        xml_path = DATA_DIR / "lipo_results.xml"
        raw = read_lipo(xml_path)
        assert raw is not None

        lipo = get_lipo_table()
        pd.testing.assert_frame_equal(lipo.reset_index(drop=True), raw['data'].reset_index(drop=True))

    def test_get_qc_table_serum(self):
        """Test getting serum QC reference table (returns dict keyed by version)."""
        qc = get_qc_table("SER")
        assert isinstance(qc, dict)
        assert len(qc) == 2
        for version, tables in qc.items():
            assert isinstance(version, str)
            assert 'tests' in tables
            assert 'infos' in tables
            assert len(tables['tests']) == 22
            assert len(tables['infos']) == 24

    def test_get_qc_table_urine(self):
        """Test getting urine QC reference table (returns dict keyed by version)."""
        qc = get_qc_table("URI")
        assert isinstance(qc, dict)
        assert len(qc) == 1
        for version, tables in qc.items():
            assert isinstance(version, str)
            assert 'tests' in tables
            assert 'infos' in tables
            assert len(tables['tests']) == 28
            assert len(tables['infos']) == 27

    def test_get_qc_table_urine_matches_xml(self):
        """Test that get_qc_table('URI') matches the raw XML content."""
        xml_path = DATA_DIR / "urine_qc_report.xml"
        raw = read_qc(xml_path)
        assert raw is not None

        version = raw['version']
        tables = get_qc_table("URI")[version]

        expected_tests = pd.DataFrame(raw['data']['tests'])[['name', 'type', 'unit', 'refMax', 'refMin']].reset_index(drop=True)
        pd.testing.assert_frame_equal(tables['tests'].reset_index(drop=True), expected_tests)

        expected_infos = pd.DataFrame(raw['data']['infos'])[['name', 'comment', 'value', 'ref']].reset_index(drop=True)
        pd.testing.assert_frame_equal(tables['infos'].reset_index(drop=True), expected_infos)

    def test_get_pacs_table(self):
        """Test getting PACS reference table."""
        pacs = get_pacs_table()
        assert pacs is not None
        assert len(pacs) == 16
        assert list(pacs.columns) == ['name', 'unit', 'refMax', 'refMin', 'refUnit']

    def test_get_pacs_table_matches_xml(self):
        """Test that get_pacs_table() matches the raw XML content."""
        xml_path = DATA_DIR / "plasma_pacs_report.xml"
        raw = read_pacs(xml_path)
        assert raw is not None

        pacs = get_pacs_table()

        # get_pacs_table drops conc_v and renames concUnit_v -> unit
        expected = raw['data'][['name', 'concUnit_v', 'refMax', 'refMin', 'refUnit']].rename(
            columns={'concUnit_v': 'unit'}
        ).reset_index(drop=True)
        pd.testing.assert_frame_equal(pacs.reset_index(drop=True), expected)

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

    def test_get_qc_table_serum_matches_xml(self):
        """Test that get_qc_table('SER') matches the raw XML content for each version."""
        qc_tables = get_qc_table("SER")

        xml_files = {
            "plasma_qc_report_2.xml": DATA_DIR / "plasma_qc_report_2.xml",
            "plasma_qc_report_1_1_0.xml": DATA_DIR / "plasma_qc_report_1_1_0.xml",
        }

        for filename, xml_path in xml_files.items():
            raw = read_qc(xml_path)
            assert raw is not None, f"read_qc returned None for {filename}"

            version = raw['version']
            assert version in qc_tables, f"Version '{version}' from {filename} not in get_qc_table result"

            tables = qc_tables[version]

            expected_tests = pd.DataFrame(raw['data']['tests'])[['name', 'type', 'unit', 'refMax', 'refMin']].reset_index(drop=True)
            pd.testing.assert_frame_equal(tables['tests'].reset_index(drop=True), expected_tests)

            expected_infos = pd.DataFrame(raw['data']['infos'])[['name', 'comment', 'value', 'ref']].reset_index(drop=True)
            pd.testing.assert_frame_equal(tables['infos'].reset_index(drop=True), expected_infos)

    def test_lipo_table_caching(self):
        """Test that lipo table is cached."""
        try:
            lipo1 = get_lipo_table()
            lipo2 = get_lipo_table()
            # Should be the same object due to @lru_cache
            assert lipo1 is lipo2
        except FileNotFoundError:
            pytest.skip("Reference data CSV not available")
