# nmr-parser Examples

This directory contains practical examples demonstrating how to use the nmr-parser package.

## Prerequisites

Make sure the package is installed:
```bash
cd ..
uv sync
```

## Running Examples

All examples can be run from this directory:

```bash
# Basic examples
python read_params_example.py
python read_quant_example.py
python read_lipo_example.py
python read_experiment_example.py
python scan_folder_example.py

# Advanced examples
python process_spectrum_example.py
python batch_processing_example.py
```

## Examples Overview

### Basic Examples

**`read_params_example.py`**
- Read acquisition and processing parameters from Bruker files
- Extract specific parameters by name
- Handle both xwin-nmr and TopSpin formats

**`read_quant_example.py`**
- Read quantification XML files (plasma and urine)
- Handle multiple XML schema versions automatically
- Access metabolite concentrations and metadata

**`read_lipo_example.py`**
- Read lipoprotein profile data
- Extend with calculated metrics (percentages, fractions)
- Access reference ranges

**`read_experiment_example.py`**
- Read complete NMR experiment folder
- Access all data types (parameters, spectrum, quantification, etc.)
- Use selective reading with options

**`scan_folder_example.py`**
- Recursively scan directories for Bruker experiments
- Filter by experiment type (EXP) and pulse program (PULPROG)
- Extract experiment paths for batch processing
- Export scan results to CSV

### Advanced Examples

**`process_spectrum_example.py`**
- Read and process 1D spectrum data
- Apply calibration and ERETIC correction
- Interpolate to specific PPM range
- Plot spectrum (requires matplotlib)

**`batch_processing_example.py`**
- Process multiple experiment folders
- Extract specific data across samples
- Create summary reports
- Export to CSV

## Test Data

Examples expect test data in `../tests/data/`. If you don't have test data:

```bash
# The examples will show you what paths they expect
# You can modify the paths in each script to point to your data
```

## Modifying Examples

Each example script is self-contained and can be modified to work with your data:

1. Change the file paths at the top of each script
2. Adjust parameters and options as needed
3. Add your own analysis or export code

## Getting Help

For more information about each function:
```python
from nmr_parser import read_experiment
help(read_experiment)
```

Or check the main README.md in the parent directory.
