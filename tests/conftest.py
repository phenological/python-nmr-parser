"""Pytest configuration and fixtures for nmr-parser tests."""

import pytest
from pathlib import Path


@pytest.fixture
def test_data_dir():
    """Path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def covid_sample_10(test_data_dir):
    """Path to HB-COVID0001/10 test sample."""
    return test_data_dir / "HB-COVID0001" / "10"


@pytest.fixture
def covid_sample_11(test_data_dir):
    """Path to HB-COVID0001/11 test sample."""
    return test_data_dir / "HB-COVID0001" / "11"


@pytest.fixture
def covid_sample_no_eretic(test_data_dir):
    """Path to sample without ERETIC calibration."""
    return test_data_dir / "HB-COVID0001_noEretic" / "10"


@pytest.fixture
def urine_sample(test_data_dir):
    """Path to urine sample."""
    return test_data_dir / "EXTERNAL-comet-nmr-urine-R20" / "10"


@pytest.fixture
def plasma_quant_xml(test_data_dir):
    """Path to plasma quantification XML."""
    return test_data_dir / "plasma_quant_report.xml"


@pytest.fixture
def plasma_quant_2_1_0_xml(test_data_dir):
    """Path to plasma quantification XML v2.1.0."""
    return test_data_dir / "plasma_quant_report_2_1_0.xml"


@pytest.fixture
def urine_quant_b_xml(test_data_dir):
    """Path to urine B quantification XML."""
    return test_data_dir / "urine_quant_report_b.xml"


@pytest.fixture
def urine_quant_e_xml(test_data_dir):
    """Path to urine E quantification XML."""
    return test_data_dir / "urine_quant_report_e.xml"


@pytest.fixture
def lipo_xml(test_data_dir):
    """Path to lipoprotein XML."""
    return test_data_dir / "lipo_results.xml"


@pytest.fixture
def qc_plasma_xml(test_data_dir):
    """Path to plasma QC XML."""
    return test_data_dir / "plasma_qc_report.xml"


@pytest.fixture
def qc_urine_xml(test_data_dir):
    """Path to urine QC XML."""
    return test_data_dir / "urine_qc_report.xml"


@pytest.fixture
def eretic_xml(test_data_dir):
    """Path to ERETIC XML."""
    return test_data_dir / "QuantFactorSample.xml"


@pytest.fixture
def pacs_xml(test_data_dir):
    """Path to PACS XML."""
    return test_data_dir / "plasma_pacs_report.xml"


@pytest.fixture
def title_singleline(test_data_dir):
    """Path to single-line title file."""
    return test_data_dir / "title_singleline"


@pytest.fixture
def title_multiline(test_data_dir):
    """Path to multi-line title file."""
    return test_data_dir / "title_multiline"
