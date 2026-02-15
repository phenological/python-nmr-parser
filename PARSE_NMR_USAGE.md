# ParseNMR - Python Migration Guide

## Overview

The `parse_nmr()` function is a Python migration of the R `parseNMR()` function from the `fusion` package. It converts NMR data from Bruker folders into **parquet files** instead of the complex `dataElement` R objects.

**Key principle**: All research decisions from the original R code have been preserved, especially the critical spcglyc biomarker calculations.

## Quick Start

```python
from nmr_parser import parse_nmr

# Basic usage - parse spectra from a folder
result = parse_nmr(
    "data/experiments/",
    opts={
        'what': ['spec'],
        'projectName': 'HB',
        'cohortName': 'COVID',
        'runName': 'EXTr01',
        'sampleMatrixType': 'plasma',
        'outputDir': 'output/'
    }
)
```

This creates four parquet files plus a DuckDB database:
- `HB_COVID_plasma_EXTr01_noesygppr1d@PROF_PLASMA_NOESY_data.parquet`
- `HB_COVID_plasma_EXTr01_noesygppr1d@PROF_PLASMA_NOESY_metadata.parquet`
- `HB_COVID_plasma_EXTr01_noesygppr1d@PROF_PLASMA_NOESY_params.parquet`
- `HB_COVID_plasma_EXTr01_noesygppr1d@PROF_PLASMA_NOESY_variables.parquet`
- `HB_COVID_plasma_EXTr01_noesygppr1d@PROF_PLASMA_NOESY.duckdb` (SQL database)

## Output Structure

### 1. **{run_id}_data.parquet** - Main data matrix

```python
import pandas as pd

data = pd.read_parquet('run_data.parquet')
# Index: sample_key (unique identifier)
# Columns: var_00001, var_00002, ... (PPM bins or metabolites)
```

### 2. **{run_id}_metadata.parquet** - Sample metadata

```python
metadata = pd.read_parquet('run_metadata.parquet')
# Columns:
# - sample_key, data_path, sample_id, sample_type
# - experiment, project_name, cohort_name, run_name
# - sample_matrix_type, method, data_type
# - is_ivdr, tube_type, created_at, parser_version
```

### 3. **{run_id}_params.parquet** - Parameters (long format)

```python
params = pd.read_parquet('run_params.parquet')
# Index: (sample_key, param_name)
# Columns: param_value, param_source
```

### 4. **{run_id}_variables.parquet** - Variable definitions

```python
variables = pd.read_parquet('run_variables.parquet')
# Columns:
# - var_id, var_name, var_type, var_unit
# - ppm_center, ppm_min, ppm_max, description
```

## Usage Examples

### Basic Spectral Analysis

```python
from nmr_parser import parse_nmr

# Parse NMR spectra with default parameters
result = parse_nmr(
    "/path/to/experiments/",
    opts={
        'projectName': 'MyProject',
        'cohortName': 'MyCohort',
        'runName': 'Run001',
        'sampleMatrixType': 'plasma',
        'outputDir': 'parquet_output/'
    }
)

# Access the data
print(f"Processed {len(result['data'])} samples")
print(f"Data shape: {result['data'].shape}")
```

### spcglyc Biomarkers

```python
# Calculate glycoprotein and SPC biomarkers
result = parse_nmr(
    "/path/to/experiments/",
    opts={
        'what': ['spcglyc'],  # Special biomarker mode
        'projectName': 'HB',
        'cohortName': 'COVID',
        'runName': 'EXTr01',
        'sampleMatrixType': 'plasma',
        'outputDir': 'spcglyc_output/'
    }
)

# This creates 11 biomarkers:
# SPC_All, SPC3, SPC2, SPC1
# Glyc_All, GlycA, GlycB
# Alb1, Alb2
# SPC3_2 (ratio), SPC_Glyc (ratio)

# Plus additional region files:
# - {run_id}_tsp.parquet (TSP reference region)
# - {run_id}_spc_region.parquet (full SPC region)
# - {run_id}_glyc_region.parquet (full Glyc region)
```

### Custom Spectral Parameters

```python
result = parse_nmr(
    "/path/to/experiments/",
    opts={
        'what': ['spec'],
        'specOpts': {
            'fromTo': (-0.5, 12),     # Extended PPM range
            'length_out': 50000,       # More points
            'uncalibrate': True,       # Remove calibration
            'procno': 1                # Processing number
        },
        'outputDir': 'output/'
    }
)
```

### Direct Paths (No Writing)

```python
# Read specific experiments without writing files
paths = [
    'exp1/10',
    'exp2/10',
    'exp3/10'
]

result = parse_nmr(
    {'dataPath': paths},
    opts={'noWrite': True}
)

# Now you have DataFrames in memory
data_df = result['data']
metadata_df = result['metadata']
```

### Quantification Data

```python
# Parse Bruker lipoprotein data
result = parse_nmr(
    "/path/to/experiments/",
    opts={
        'what': ['brxlipo'],
        'projectName': 'Study',
        'runName': 'Lipo01',
        'outputDir': 'lipo_output/'
    }
)

# Parse Bruker PACS data
result = parse_nmr(
    "/path/to/experiments/",
    opts={
        'what': ['brxpacs'],
        'outputDir': 'pacs_output/'
    }
)

# Parse Bruker small molecule data
result = parse_nmr(
    "/path/to/experiments/",
    opts={
        'what': ['brxsm'],
        'outputDir': 'sm_output/'
    }
)
```

## Joining with nmrCatalog

The parquet files are designed to be easily joined with the nmrCatalog database:

```python
import pandas as pd
import sqlite3

# Load parquet files
data = pd.read_parquet('run_data.parquet')
metadata = pd.read_parquet('run_metadata.parquet')
params = pd.read_parquet('run_params.parquet')

# Load catalog from SQLite
conn = sqlite3.connect('/Users/jul/docker/plt-binder-docker/db/binder.sqlite')
catalog = pd.read_sql('SELECT * FROM nmrCatalog', conn)

# Join everything
full_dataset = (
    data
    .merge(metadata, on='sample_key', how='left')
    .merge(catalog, on='sample_id', how='left')
)

# Filter specific parameters
key_params = params[params['param_name'].isin(['NS', 'RG', 'PULPROG'])]
param_wide = key_params.pivot(
    index='sample_key',
    columns='param_name',
    values='param_value'
)
full_dataset = full_dataset.merge(param_wide, on='sample_key', how='left')

# Now you have everything in one DataFrame
print(full_dataset.head())
```

## Working with Parquet Files

### Using Pandas

```python
import pandas as pd

# Read full file
data = pd.read_parquet('run_data.parquet')

# Read specific columns
data_subset = pd.read_parquet('run_data.parquet', columns=['var_00001', 'var_00002'])

# Read with filters
metadata = pd.read_parquet(
    'run_metadata.parquet',
    filters=[('sample_type', '==', 'qc')]
)
```

### Using Polars (faster)

```python
import polars as pl

# Read with Polars (much faster for large datasets)
data = pl.read_parquet('run_data.parquet')
metadata = pl.read_parquet('run_metadata.parquet')

# Filter and join
qc_samples = (
    data
    .join(metadata, on='sample_key')
    .filter(pl.col('sample_type') == 'qc')
)
```

### Using DuckDB (SQL queries) ⭐ NEW

A DuckDB database is automatically created with views to all parquet files:

```python
import duckdb

# Connect to the auto-generated database
con = duckdb.connect('HB_COVID_plasma_EXTr01_noesygppr1d@PROF_PLASMA_NOESY.duckdb')

# Query using SQL - super fast!
result = con.sql("""
    SELECT * FROM data_with_metadata
    WHERE sample_type = 'qc'
    LIMIT 10
""").df()

# Available views:
# - data: Main data matrix
# - metadata: Sample metadata
# - params: Parameters (long format)
# - variables: Variable definitions
# - data_with_metadata: Convenient joined view
# - params_wide: Parameters in wide format (top 20)

# Complex queries are easy
result = con.sql("""
    SELECT
        m.sample_type,
        COUNT(*) as n_samples,
        AVG(d.var_00001) as mean_intensity
    FROM data d
    JOIN metadata m USING (sample_key)
    GROUP BY m.sample_type
""").df()

# Or query parquet files directly (without database)
result = duckdb.sql("""
    SELECT *
    FROM 'run_data.parquet' d
    JOIN 'run_metadata.parquet' m USING (sample_key)
    WHERE m.sample_type = 'qc'
""").df()
```

## Preserved Research Decisions

### 1. Sample Type Classification (Critical)

```python
# Automatic classification based on sample names
# Lines 98-108 in parseNMR.R
if 'sltr' in sample_id.lower():
    sample_type = 'sltr'  # Serum LTR
elif sample_id.lower().startswith('ltr'):
    sample_type = 'ltr'   # Long-term reference
elif sample_id.lower().startswith('pqc'):
    sample_type = 'pqc'   # Pooled QC
elif sample_id.lower().startswith('qc'):
    sample_type = 'qc'    # Quality control
else:
    sample_type = 'sample'  # Regular sample
```

### 2. spcglyc Calculations (Critical)

All biomarker calculations from lines 280-359 preserved:

```python
# PPM regions excluded:
# - 4.6-4.85 ppm (water)
# - below 0.2 ppm (baseline)
# - above 10.0 ppm (high PPM)

# 180° flip detection:
# If sum of 3.2-3.3 ppm region is negative, multiply spectrum by -1

# Integration regions (all use sum * dw):
SPC_All  = 3.18-3.32 ppm
SPC3     = 3.262-3.3 ppm
SPC2     = 3.236-3.262 ppm
SPC1     = 3.2-3.236 ppm
Glyc_All = 2.050-2.118 ppm
GlycA    = 2.050-2.089 ppm
GlycB    = 2.089-2.118 ppm
Alb1     = 0.2-0.7 ppm
Alb2     = 6.0-10.0 ppm

# Ratios:
SPC3_2   = SPC3 / SPC2
SPC_Glyc = SPC_All / Glyc_All

# 3mm tube correction:
# All values divided by 2 if '3mm' in path
```

### 3. Data Merging Strategy (Critical)

Lines 425-545 in parseNMR.R:

```python
# Find intersection of all data paths
intersection = set(spec_paths) & set(acqus_paths) & set(loe_paths)

# Only keep samples present in ALL sources
# Log excluded paths for transparency
```

### 4. IVDr Detection

Lines 415-422 in parseNMR.R:

```python
# Check if QC data exists
has_qc = any(qc_data is not None for qc_data in qc_results)
is_ivdr = has_qc
```

## Command-Line Usage

```bash
# Basic usage
python examples/parse_nmr_example.py data/experiments/ -o output/

# With metadata
python examples/parse_nmr_example.py data/ \
    --project HB \
    --cohort COVID \
    --run EXTr01 \
    --matrix plasma

# spcglyc biomarkers
python examples/parse_nmr_example.py data/ --what spcglyc

# Custom PPM range
python examples/parse_nmr_example.py data/ \
    --ppm-range -0.5 12 \
    --n-points 50000

# Direct paths (no write)
python examples/parse_nmr_example.py \
    --paths exp1/10 exp2/10 exp3/10 \
    --no-write
```

## Migration from R dataElement

### Old R workflow:

```r
# R code
library(fusion)
da <- parseNMR(folder, opts)
save(da, file = "run.daE")

# Later...
da <- local(get(load("run.daE")))
data_matrix <- da@.Data
metadata <- da@obsDescr
varnames <- da@varName
```

### New Python workflow:

```python
# Python code
from nmr_parser import parse_nmr

result = parse_nmr(folder, opts)
# Files saved automatically

# Later...
import pandas as pd
data = pd.read_parquet('run_data.parquet')
metadata = pd.read_parquet('run_metadata.parquet')
variables = pd.read_parquet('run_variables.parquet')
```

## Advantages of Parquet Format

1. **Standard format**: Works with pandas, polars, DuckDB, Arrow, Spark
2. **Efficient**: Column-oriented, compressed, fast I/O
3. **Type-safe**: Explicit data types, no mixed types
4. **Scalable**: Can handle very large datasets
5. **Simple joins**: Easy to merge with other data sources
6. **No proprietary format**: Unlike R's .daE files

## Troubleshooting

### Missing pyarrow

```bash
pip install pyarrow
```

### Memory issues with large datasets

```python
# Read parquet in chunks or specific columns
data = pd.read_parquet('run_data.parquet', columns=['var_00001', 'var_00002'])

# Or use polars (more memory efficient)
import polars as pl
data = pl.read_parquet('run_data.parquet')
```

### Joining issues

```python
# Make sure sample_key is used for joins
data.merge(metadata, on='sample_key')

# Check for missing keys
missing = set(data.index) - set(metadata.index)
print(f"Missing keys: {missing}")
```

## See Also

- [PARQUET_DESIGN.md](PARQUET_DESIGN.md) - Detailed design documentation
- [examples/parse_nmr_example.py](examples/parse_nmr_example.py) - Example script
- Original R code: [../fusion/R/parseNMR.R](../fusion/R/parseNMR.R)
