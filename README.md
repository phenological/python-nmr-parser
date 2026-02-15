# nmr-parser

Python package for parsing NMR IVDr data from Bruker instruments.

This is a Python migration of the R package `nmr.parser` (v0.3.4), preserving all functionality while adopting Python best practices and the scientific Python ecosystem (NumPy, pandas, SciPy).

## Features

- **Binary spectrum reading** with endianness handling and power factor scaling
- **Parameter file parsing** for acqus/procs files (xwin-nmr and TopSpin formats)
- **XML parsing** for quantification, lipoprotein, QC, PACS, and ERETIC data
- **Multiple format support** with automatic version detection
- **Spectrum processing** with calibration, interpolation, and ERETIC correction
- **Type hints** for better IDE support and code clarity
- **Modern Python packaging** with pyproject.toml

## Installation

```bash
# From source
pip install -e .

# With development dependencies
pip install -e ".[dev]"
```

## Quick Start

```python
from nmr_parser import read_experiment

# Read all data from a single experiment
exp = read_experiment("data/HB-COVID0001/10")

# Access different data types
print(exp['acqus'])       # Acquisition parameters
print(exp['procs'])       # Processing parameters
print(exp['spec'])        # Spectrum data
print(exp['quant'])       # Quantification results
print(exp['lipo'])        # Lipoprotein profiles
print(exp['qc'])          # Quality control data

# Read multiple experiments
exps = read_experiment([
    "data/HB-COVID0001/10",
    "data/HB-COVID0001/11",
    "data/HB-COVID0001/12"
])

# Read only specific components
exp = read_experiment(
    "data/HB-COVID0001/10",
    opts={"what": ["acqus", "spec", "quant"]}
)

# Read spectrum with custom options
opts = {
    "what": ["spec"],
    "specOpts": {
        "fromTo": (-0.1, 10),      # PPM range
        "length_out": 44079,        # Number of points
        "uncalibrate": False,       # Keep calibration
        "eretic": 3808.27           # ERETIC factor (optional)
    }
}
exp = read_experiment("data/HB-COVID0001/10", opts=opts)

# Access spectrum data
spec_df = exp['spec']['spec'].iloc[0]
x = spec_df['x']  # PPM axis
y = spec_df['y']  # Intensity
```

## Command-Line Usage Examples

The `examples/` directory contains ready-to-use scripts with argument parsing and data export options.

### Basic Usage

```bash
# Read parameters with default test data
python examples/read_params_example.py

# Read from your own data
python examples/read_params_example.py /path/to/experiment/10

# Export all data to CSV
python examples/read_params_example.py -o output.csv

# Display all data in terminal
python examples/read_params_example.py --show-all

# Combine: use your data and export
python examples/read_params_example.py /path/to/exp/10 -o params.csv
```

### Available Examples

All examples support `--help`, `-o/--output` for CSV export, and most support `--show-all`:

```bash
# Parameters
python examples/read_params_example.py [exp_path] [-o output.csv] [--show-all]

# Quantification
python examples/read_quant_example.py [xml_file] [-o output.csv] [--show-all]

# Lipoproteins
python examples/read_lipo_example.py [xml_file] [-o output.csv] [--show-all]

# Complete experiment
python examples/read_experiment_example.py [exp_path] [exp_path2...] [-o output.csv]

# Scan folders
python examples/scan_folder_example.py [folder_path] [-o output.csv]

# Process spectrum
python examples/process_spectrum_example.py [exp_path] [-o spectrum.csv]

# Batch processing
python examples/batch_processing_example.py [exp1 exp2 exp3...]
```

### Export Options

All examples can export full datasets to CSV:

```bash
# Export parameters (all ~1,128 rows)
python examples/read_params_example.py -o my_params.csv

# Export quantification (~41-150 metabolites)
python examples/read_quant_example.py -o metabolites.csv

# Export lipoproteins (~112+ measurements)
python examples/read_lipo_example.py -o lipoproteins.csv
```

**Note:** Examples show summaries by default (first 5-10 rows) for readability. Use `-o` to export complete data or `--show-all` to display everything.

## Individual Parser Functions

```python
from nmr_parser import (
    read_spectrum,
    read_param,
    read_params,
    read_quant,
    read_lipo,
    read_qc,
    read_eretic
)

# Read single parameter
pulprog = read_param("experiment/acqus", "PULPROG")

# Read all parameters
params = read_params("experiment/acqus")

# Read spectrum
spec = read_spectrum(
    "experiment/10",
    procno=1,
    options={'fromTo': (-0.1, 10), 'length_out': 44079}
)

# Read quantification data (handles multiple XML versions)
quant = read_quant("experiment/pdata/1/plasma_quant_report.xml")
print(quant['data'])     # DataFrame with 41-150 compounds
print(quant['version'])  # Version string

# Read lipoprotein profiles
lipo = read_lipo("experiment/pdata/1/lipo_results.xml")
print(lipo['data'])      # DataFrame with 112 measurements

# Read QC data
qc = read_qc("experiment/pdata/1/plasma_qc_report.xml")

# Read ERETIC calibration
eretic = read_eretic("experiment/QuantFactorSample.xml")
print(eretic['ereticFactor'].iloc[0])
```

## Architecture

```
nmr_parser/
├── core/              # Core I/O functions
│   ├── experiment.py  # Main orchestrator
│   ├── spectrum.py    # Spectrum reading
│   └── parameters.py  # Parameter file parsing
├── xml_parsers/       # XML parsing functions
│   ├── quantification.py
│   ├── lipoproteins.py
│   ├── quality_control.py
│   ├── pacs.py
│   └── eretic.py
├── processing/        # Data processing utilities
└── reference/         # Reference tables and data
```

## Dependencies

- **lxml** (>=4.9.0) - XML parsing with XPath support
- **pandas** (>=2.0.0) - Data manipulation
- **numpy** (>=1.24.0) - Numerical operations
- **scipy** (>=1.10.0) - Signal processing (interpolation)
- **rich** (>=13.0.0) - Terminal output

## Compatibility

This Python package maintains full compatibility with the R `nmr.parser` package (v0.3.4):

- **Same function names** (snake_case in Python vs camelCase in R)
- **Same data structures** (pandas DataFrames instead of R data.frames)
- **Same logic** for all parsers and calculations
- **Same XML version detection** and priority systems

### R to Python Function Mapping

| R Function | Python Function | Module |
|------------|-----------------|--------|
| `readExperiment()` | `read_experiment()` | `nmr_parser` |
| `readSpectrum()` | `read_spectrum()` | `nmr_parser.core` |
| `readParam()` | `read_param()` | `nmr_parser.core` |
| `readParams()` | `read_params()` | `nmr_parser.core` |
| `readQuant()` | `read_quant()` | `nmr_parser.xml_parsers` |
| `readLipo()` | `read_lipo()` | `nmr_parser.xml_parsers` |
| `readQc()` | `read_qc()` | `nmr_parser.xml_parsers` |
| `readEretic()` | `read_eretic()` | `nmr_parser.xml_parsers` |
| `cleanNames()` | `clean_names()` | `nmr_parser.processing` |

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests (once implemented)
pytest

# Run with coverage
pytest --cov=nmr_parser

# Format code
black src/

# Lint code
ruff check src/

# Type check
mypy src/
```

## License

MIT License - See LICENSE file for details

## Authors

- Julien Wist (julien.wist@murdoch.edu.au)
- Reika Masuda (reika.masuda@murdoch.edu.au)

## Citation

If you use this package, please cite:
- Original R package: nmr.parser v0.3.4
- Python package: nmr-parser v0.4.0

## Contributing

This is a migration of an R package. Contributions should maintain compatibility with the original R implementation while following Python best practices.
