# Test Suite for nmr-parser

Comprehensive test suite for the Python nmr-parser package.

## Test Structure

```
tests/
├── conftest.py              # Pytest fixtures and configuration
├── test_utils.py            # Utility function tests
├── test_parameters.py       # Parameter reading tests
├── test_spectrum.py         # Spectrum reading tests
├── test_quantification.py   # Quantification XML tests
├── test_lipoproteins.py     # Lipoprotein tests
├── test_xml_parsers.py      # Other XML parser tests
├── test_experiment.py       # Main orchestrator tests
├── test_reference_tables.py # Reference table tests
└── data/                    # Test data directory
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=nmr_parser --cov-report=html --cov-report=term-missing
```

### Run specific test file
```bash
pytest tests/test_experiment.py
```

### Run specific test class
```bash
pytest tests/test_experiment.py::TestReadExperiment
```

### Run specific test
```bash
pytest tests/test_experiment.py::TestReadExperiment::test_read_single_experiment
```

### Run with verbose output
```bash
pytest -v
```

### Run tests matching pattern
```bash
pytest -k "spectrum"
```

## Test Data

Test data should be placed in `tests/data/` directory with the following structure:

```
tests/data/
├── HB-COVID0001/
│   ├── 10/          # Test experiment 1
│   ├── 11/          # Test experiment 2
│   └── 12/          # Test experiment 3
├── HB-COVID0001_noEretic/
│   └── 10/          # Experiment without ERETIC
├── EXTERNAL-comet-nmr-urine-R20/
│   └── 10/          # Urine sample
├── plasma_quant_report.xml
├── plasma_quant_report_2_1_0.xml
├── urine_quant_report_b.xml
├── urine_quant_report_e.xml
├── lipo_results.xml
├── plasma_qc_report.xml
├── urine_qc_report.xml
├── QuantFactorSample.xml
├── plasma_pacs_report.xml
├── title_singleline
└── title_multiline
```

## Test Coverage Goals

- **Line coverage**: >90%
- **Branch coverage**: >85%
- **Function coverage**: 100%

## Fixtures

Common fixtures available in all tests (defined in `conftest.py`):

- `test_data_dir` - Path to test data directory
- `covid_sample_10` - Path to HB-COVID0001/10
- `covid_sample_11` - Path to HB-COVID0001/11
- `covid_sample_no_eretic` - Path to experiment without ERETIC
- `urine_sample` - Path to urine sample
- `plasma_quant_xml` - Path to plasma quantification XML
- `lipo_xml` - Path to lipoprotein XML
- `qc_plasma_xml` - Path to plasma QC XML
- `eretic_xml` - Path to ERETIC XML
- And more...

## Writing New Tests

### Example test structure:

```python
import pytest
from nmr_parser import some_function

class TestSomeFunction:
    """Tests for some_function."""

    def test_basic_functionality(self, test_data_dir):
        """Test basic functionality."""
        result = some_function(test_data_dir / "some_file")
        assert result is not None
        assert len(result) > 0

    def test_edge_case(self):
        """Test edge case handling."""
        result = some_function("nonexistent")
        assert result is None

    @pytest.mark.parametrize("input,expected", [
        ("input1", "output1"),
        ("input2", "output2"),
    ])
    def test_multiple_inputs(self, input, expected):
        """Test with multiple inputs."""
        result = some_function(input)
        assert result == expected
```

## Continuous Integration

Tests should be run in CI/CD pipeline on:
- Push to main branch
- Pull requests
- Scheduled daily builds

## Notes

- Tests use `pytest.skip()` when test data is not available
- All tests should be independent and can run in any order
- Use fixtures to avoid code duplication
- Add docstrings to all test functions
- Use descriptive test names that explain what is being tested
