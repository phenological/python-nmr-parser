# ParseNMR Python Migration - Parquet Design

## Overview
This document describes the migration strategy for parseNMR.R to Python, replacing the complex dataElement structure with simple parquet files designed for joining with nmrCatalog.

## Output Structure

Each parseNMR run produces **three parquet files**:

### 1. **{run_id}_data.parquet** - The main data matrix
```python
# Columns:
- sample_key: str          # Unique identifier for joining (sampleID + dataPath hash)
- var_001, var_002, ...    # Data values (PPM bins or metabolite names)

# Index: sample_key
# Shape: (n_samples, n_variables)
```

### 2. **{run_id}_metadata.parquet** - Sample and run metadata
```python
# Columns:
- sample_key: str          # Same key as in data file
- data_path: str           # Original bruker path
- sample_id: str           # Human-readable sample ID
- sample_type: str         # 'sample', 'qc', 'ltr', 'sltr', 'pqc'
- experiment: str          # Experiment name from EXP parameter
- nmr_folder_id: str       # Optional, from Rolodex
- project_name: str        # Project identifier
- cohort_name: str         # Cohort identifier
- run_name: str            # Run identifier
- sample_matrix_type: str  # Sample matrix (e.g., 'plasma', 'serum')
- method: str              # Method name (e.g., 'noesygppr1d@PROF_PLASMA_NOESY')
- data_type: str           # 'NMR' or 'QUANT'
- is_ivdr: bool            # Whether data has IVDr QC
- tube_type: str           # '3mm' or '5mm' (detected from path)
- created_at: timestamp    # Processing timestamp
- parser_version: str      # nmr-parser version

# Index: sample_key
# Shape: (n_samples, metadata_cols)
```

### 3. **{run_id}_params.parquet** - Acquisition and processing parameters
```python
# Columns:
- sample_key: str          # Same key as in data file
- param_name: str          # Parameter name (e.g., 'NS', 'O1', 'PULPROG')
- param_value: str/float   # Parameter value
- param_source: str        # 'acqus', 'procs', 'qc_test', 'qc_info'

# Index: (sample_key, param_name)
# Shape: (n_samples * n_params, 4)
# This is a "long" format for easy filtering and joining
```

### 4. **{run_id}_variables.parquet** - Variable definitions
```python
# Columns:
- var_id: str              # Variable identifier (matches column names in data)
- var_name: float/str      # Original name (PPM value or metabolite name)
- var_type: str            # 'ppm', 'metabolite', 'biomarker'
- var_unit: str            # 'ppm', 'mM', 'ratio', etc.
- ppm_center: float        # For integrated regions
- ppm_min: float           # For integrated regions
- ppm_max: float           # For integrated regions
- description: str         # Variable description

# Index: var_id
# Shape: (n_variables, 7)
```

## Key Advantages

1. **Simple joining with nmrCatalog**:
   ```python
   # Join data with catalog
   catalog = pd.read_sql("SELECT * FROM nmrCatalog", conn)
   merged = data.merge(metadata, on='sample_key')
   merged = merged.merge(catalog, on='sample_id')
   ```

2. **Efficient storage**: Parquet compression, column-oriented
3. **Type safety**: Explicit types, no mixed types
4. **Scalability**: Can handle large runs
5. **Standard format**: Works with Polars, DuckDB, Arrow, etc.

## Special Handling: spcglyc

For spcglyc analysis, the data file contains calculated biomarkers:

```python
# {run_id}_data.parquet columns for spcglyc:
- sample_key
- SPC_All, SPC3, SPC2, SPC1      # SPC biomarkers
- Glyc_All, GlycA, GlycB          # Glycoprotein biomarkers
- Alb1, Alb2                       # Albumin proxies
- SPC3_2                           # SPC3/SPC2 ratio
- SPC_Glyc                         # SPC/Glyc ratio

# Additionally saved:
# {run_id}_tsp.parquet - TSP reference region (0-0.5 ppm)
# {run_id}_spc_region.parquet - Full SPC region (3.18-3.32 ppm)
# {run_id}_glyc_region.parquet - Full Glyc region (2.050-2.118 ppm)
```

## Preserved Research Decisions

### Sample Type Classification
```python
# Lines 98-108 in R code
if 'sltr' in sample_id.lower():
    sample_type = 'sltr'
elif sample_id.lower().startswith('ltr'):
    sample_type = 'ltr'
elif sample_id.lower().startswith('pqc'):
    sample_type = 'pqc'
elif sample_id.lower().startswith('qc'):
    sample_type = 'qc'
else:
    sample_type = 'sample'
```

### spcglyc Calculation Logic (lines 280-359)
```python
# 1. Trim regions (excluding water, baseline, high PPM)
excluded_ppm = [
    (ppm >= 4.6) & (ppm <= 4.85),   # Water
    (ppm >= min_ppm) & (ppm <= 0.2), # Baseline
    (ppm >= 10.0)                     # High PPM
]

# 2. Check for 180° flip (lines 293-299)
region_3_2_3_3 = trimmed_spectra[:, (ppm >= 3.2) & (ppm <= 3.3)]
flip_idx = np.where(region_3_2_3_3.sum(axis=1) < 0)[0]
trimmed_spectra[flip_idx, :] = -trimmed_spectra[flip_idx, :]

# 3. Calculate biomarkers with integration (sum * dw)
dw = ppm[1] - ppm[0]  # Delta ppm

biomarkers = {
    'SPC_All': integrate_region(3.18, 3.32),
    'SPC3': integrate_region(3.262, 3.3),
    'SPC2': integrate_region(3.236, 3.262),
    'SPC1': integrate_region(3.2, 3.236),
    'Glyc_All': integrate_region(2.050, 2.118),
    'GlycA': integrate_region(2.050, 2.089),
    'GlycB': integrate_region(2.089, 2.118),
    'Alb1': integrate_region(0.2, 0.7),
    'Alb2': integrate_region(6.0, 10.0),
}

# 4. Calculate ratios
biomarkers['SPC3_2'] = biomarkers['SPC3'] / biomarkers['SPC2']
biomarkers['SPC_Glyc'] = biomarkers['SPC_All'] / biomarkers['Glyc_All']

# 5. Apply 3mm tube correction (lines 356-357)
is_3mm = ['3mm' in path.lower() for path in data_paths]
biomarkers.loc[is_3mm, :] = biomarkers.loc[is_3mm, :] / 2
```

### Data Merging Strategy (lines 425-545)
```python
# Find intersection of all data sources
paths_intersection = set(spec_paths) & set(acqus_paths) & set(loe_paths)

# Filter each dataframe to only include intersection
spec_data = spec_data[spec_data['path'].isin(paths_intersection)]
acqus_data = acqus_data[acqus_data['path'].isin(paths_intersection)]
loe_data = loe_data[loe_data['path'].isin(paths_intersection)]

# Log excluded paths
excluded = set(spec_paths) - paths_intersection
if excluded:
    logger.warning(f"Excluded paths: {excluded}")
```

### IVDr Detection (lines 415-422)
```python
# Check if any QC data exists
has_qc = any(qc_data is not None for qc_data in qc_results)
is_ivdr = has_qc
```

## File Naming Convention

```
{project}_{cohort}_{matrix}_{run}_{method}_{type}.parquet

Examples:
- HB_COVID_plasma_EXTr01_noesygppr1d@PROF_PLASMA_NOESY_data.parquet
- HB_COVID_plasma_EXTr01_noesygppr1d@PROF_PLASMA_NOESY_metadata.parquet
- HB_COVID_plasma_EXTr01_noesygppr1d@PROF_PLASMA_NOESY_params.parquet
- HB_COVID_plasma_EXTr01_noesygppr1d@PROF_PLASMA_NOESY_variables.parquet
- HB_COVID_plasma_EXTr01_spcglyc_data.parquet (for spcglyc runs)
```

## Integration with nmrCatalog

The nmrCatalog SQLite database likely contains:
- Sample metadata (sample_id, patient_id, collection_date, etc.)
- Clinical data
- Study design information

### Joining Strategy:

```python
import pandas as pd
import sqlite3
import pyarrow.parquet as pq

# Load parquet files
data = pq.read_table('run_data.parquet').to_pandas()
metadata = pq.read_table('run_metadata.parquet').to_pandas()
params = pq.read_table('run_params.parquet').to_pandas()

# Load catalog
conn = sqlite3.connect('/Users/jul/docker/plt-binder-docker/db/binder.sqlite')
catalog = pd.read_sql('SELECT * FROM nmrCatalog', conn)

# Join
full_dataset = (
    data
    .merge(metadata, on='sample_key', how='left')
    .merge(catalog, on='sample_id', how='left')
)

# Filter by specific parameters
specific_params = params[params['param_name'].isin(['NS', 'RG', 'PULPROG'])]
param_wide = specific_params.pivot(
    index='sample_key',
    columns='param_name',
    values='param_value'
)
full_dataset = full_dataset.merge(param_wide, on='sample_key', how='left')
```

## Implementation Priority

1. **Phase 1**: Core parseNMR with spec and basic metadata
2. **Phase 2**: spcglyc with all biomarker calculations
3. **Phase 3**: brxlipo, brxpacs, brxsm quantification data
4. **Phase 4**: IVDr QC tests and info values
5. **Phase 5**: Integration with Rolodex API (optional)

## Testing Strategy

Each critical research decision should have unit tests:
- `test_sample_type_classification()` - Verify sltr, ltr, qc, pqc detection
- `test_spcglyc_ppm_trimming()` - Verify correct PPM exclusion
- `test_spcglyc_flip_detection()` - Verify 180° flip correction
- `test_spcglyc_biomarkers()` - Verify all 11 biomarker calculations
- `test_3mm_tube_correction()` - Verify 3mm tube correction
- `test_data_merging()` - Verify intersection logic
- `test_ivdr_detection()` - Verify QC presence detection
