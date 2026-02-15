# Reference Data Files

This directory contains reference data tables converted from R `.rda` format to CSV.

## Data Files

- **lipo.csv** - Lipoprotein reference data (112 measurements)
- **lipo_densities.csv** - Lipoprotein data with density information
- **brxsm_pla.csv** - Plasma/serum metabolites reference (41 compounds)
- **brxsm_uri.csv** - Urine metabolites reference (150 compounds)

## Generating CSV Files

To generate these CSV files from the original R package data:

```bash
# Navigate to data-raw directory
cd data-raw

# Run conversion script (requires R with nmr.parser package)
Rscript convert_rda_to_csv.R
```

### Requirements

- R (>= 4.0)
- R package: `nmr.parser` (>= 0.3.4)

### Manual Conversion

If you have the R package installed:

```r
# In R console
library(nmr.parser)

# Load and save each dataset
data(lipo)
write.csv(lipo$data, "lipo.csv", row.names = FALSE)

data(lipoWithDensities)
write.csv(lipoWithDensities$data, "lipo_densities.csv", row.names = FALSE)

data(brxsm_pla)
write.csv(brxsm_pla$data, "brxsm_pla.csv", row.names = FALSE)

data(brxsm_uri)
write.csv(brxsm_uri$data, "brxsm_uri.csv", row.names = FALSE)
```

## Usage in Python

Once converted, access the data with:

```python
from nmr_parser import get_lipo_table, get_sm_table

# Load lipoprotein reference table
lipo_ref = get_lipo_table()

# Load metabolite reference table (plasma)
metabolites = get_sm_table("PLA")
```

## Note

The reference table functions will work without these CSV files by providing
default/placeholder data based on documentation. However, for complete reference
data with exact values, the CSV files should be generated from the R package.
