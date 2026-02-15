# Testing Guide for nmr-parser

This guide documents all commands needed to test the Python nmr-parser package.

## Prerequisites

Ensure you have `uv` installed:
```bash
pip install uv
```

## Initial Setup

### 1. Install Dependencies

Install the package and all dependencies:
```bash
uv sync
```

Install with development dependencies (required for testing):
```bash
uv sync --extra dev
```

## Running Tests

### Run All Tests

```bash
uv run pytest
```

With verbose output:
```bash
uv run pytest -v
```

With short traceback:
```bash
uv run pytest -v --tb=short
```

### Run Specific Test Files

```bash
# Test utility functions
uv run pytest tests/test_utils.py -v

# Test parameter reading
uv run pytest tests/test_parameters.py -v

# Test spectrum reading
uv run pytest tests/test_spectrum.py -v

# Test quantification XML parsing
uv run pytest tests/test_quantification.py -v

# Test lipoprotein functions
uv run pytest tests/test_lipoproteins.py -v

# Test XML parsers
uv run pytest tests/test_xml_parsers.py -v

# Test main experiment reader
uv run pytest tests/test_experiment.py -v

# Test reference tables
uv run pytest tests/test_reference_tables.py -v
```

### Run Specific Test Classes

```bash
# Test clean_names function
uv run pytest tests/test_utils.py::TestCleanNames -v

# Test read_experiment function
uv run pytest tests/test_experiment.py::TestReadExperiment -v

# Test lipoprotein reading
uv run pytest tests/test_lipoproteins.py::TestReadLipo -v
```

### Run Specific Test Functions

```bash
# Test single experiment reading
uv run pytest tests/test_experiment.py::TestReadExperiment::test_read_single_experiment -v

# Test clean_names with special characters
uv run pytest tests/test_utils.py::TestCleanNames::test_special_characters -v

# Test lipoprotein extension
uv run pytest tests/test_lipoproteins.py::TestExtendLipo::test_extend_lipo_full -v
```

### Run Tests Matching Pattern

```bash
# Run all tests with "spectrum" in the name
uv run pytest -k "spectrum" -v

# Run all tests with "lipo" in the name
uv run pytest -k "lipo" -v

# Run all tests with "xml" in the name
uv run pytest -k "xml" -v
```

## Code Coverage

### Run Tests with Coverage

```bash
# Generate coverage report
uv run pytest --cov=nmr_parser --cov-report=term-missing
```

### Generate HTML Coverage Report

```bash
# Generate HTML report (opens in browser)
uv run pytest --cov=nmr_parser --cov-report=html --cov-report=term-missing

# View the HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage for Specific Modules

```bash
# Coverage for utils module only
uv run pytest tests/test_utils.py --cov=nmr_parser.processing.utils --cov-report=term-missing

# Coverage for XML parsers only
uv run pytest tests/test_xml_parsers.py tests/test_quantification.py tests/test_lipoproteins.py \
    --cov=nmr_parser.xml_parsers --cov-report=term-missing
```

## Test Output Options

### Minimal Output (Quiet Mode)

```bash
uv run pytest -q
```

### Verbose Output with Full Traceback

```bash
uv run pytest -vv --tb=long
```

### Show Print Statements

```bash
uv run pytest -s
```

### Stop on First Failure

```bash
uv run pytest -x
```

### Run Last Failed Tests Only

```bash
uv run pytest --lf
```

### Run Failed Tests First

```bash
uv run pytest --ff
```

## Continuous Testing

### Watch for Changes and Re-run Tests

Install pytest-watch:
```bash
uv add --dev pytest-watch
```

Run continuous testing:
```bash
uv run ptw
```

## Performance Testing

### Show Slowest Tests

```bash
uv run pytest --durations=10
```

### Run Tests in Parallel

Install pytest-xdist:
```bash
uv add --dev pytest-xdist
```

Run tests in parallel:
```bash
uv run pytest -n auto
```

## Test Status Summary

As of last test run:
- **Total tests**: 56
- **Passed**: 21 (tests with available data)
- **Skipped**: 35 (tests requiring test data files)
- **Failed**: 0

### Tests Requiring Data

The following tests require test data in `tests/data/`:

**Experiment Tests** (covid_sample_10, covid_sample_11):
- `test_read_single_experiment`
- `test_read_multiple_experiments`
- `test_read_with_options`
- `test_read_spectrum_only`
- `test_read_with_spec_options`

**Parameter Tests** (covid_sample_10):
- `test_read_acqus`
- `test_read_procs`
- `test_read_multiple_params`

**Spectrum Tests** (covid_sample_10):
- `test_read_1r_basic`
- `test_read_spectrum_basic`

**XML Parser Tests**:
- Quantification: `plasma_quant_xml`, `urine_quant_xml`
- Lipoproteins: `lipo_xml`
- QC: `qc_plasma_xml`, `qc_urine_xml`
- PACS: `pacs_xml`
- ERETIC: `eretic_xml`

**Reference Table Tests**:
- Lipoprotein table
- Metabolite tables (plasma/urine)

## Debugging Failed Tests

### Run with Python Debugger

```bash
uv run pytest --pdb
```

### Run with Detailed Error Messages

```bash
uv run pytest -vv --tb=long --showlocals
```

### Check Specific Assertion

```bash
uv run pytest tests/test_utils.py::TestCleanNames::test_special_characters -vv
```

## Type Checking

Run mypy for type checking:
```bash
uv run mypy src/nmr_parser
```

## Code Quality

### Run Black (Code Formatter)

```bash
uv run black src/ tests/
```

Check without modifying:
```bash
uv run black --check src/ tests/
```

### Run Ruff (Linter)

```bash
uv run ruff check src/ tests/
```

Auto-fix issues:
```bash
uv run ruff check --fix src/ tests/
```

## Integration Testing Workflow

Complete testing workflow for development:

```bash
# 1. Sync dependencies
uv sync --extra dev

# 2. Run all tests with coverage
uv run pytest --cov=nmr_parser --cov-report=html --cov-report=term-missing

# 3. Check code quality
uv run black src/ tests/
uv run ruff check src/ tests/
uv run mypy src/nmr_parser

# 4. View coverage report
open htmlcov/index.html
```

## CI/CD Testing

For continuous integration pipelines:

```bash
# Install and test in one go
uv sync --extra dev && uv run pytest --cov=nmr_parser --cov-report=xml --cov-report=term-missing
```

## Notes

- Tests use `pytest.skip()` when test data files are not available
- All tests are independent and can run in any order
- Coverage goal: >90% line coverage, >85% branch coverage
- Test data should mirror the R package structure in `inst/`
