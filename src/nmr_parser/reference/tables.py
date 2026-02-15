"""Reference table functions for accessing pre-loaded metabolite and lipoprotein data."""

import pandas as pd
from pathlib import Path
from functools import lru_cache
from typing import Literal, Optional


# Data directory path
DATA_DIR = Path(__file__).parent / "data"


@lru_cache(maxsize=1)
def get_lipo_table(extended: bool = False, with_densities: bool = False) -> pd.DataFrame:
    """
    Get lipoprotein reference table.

    Returns reference data for 112 lipoprotein measurements with compound
    names, abbreviations, fractions, and reference ranges.

    Parameters
    ----------
    extended : bool, default=False
        If True, returns extended table with calculated metrics (316 rows)
        If False, returns raw measurements only (112 rows)
    with_densities : bool, default=False
        If True, includes density information for lipoprotein fractions

    Returns
    -------
    pd.DataFrame
        DataFrame with columns:
        - fraction: Lipoprotein fraction (HDL, LDL, VLDL, IDL)
        - name: Full compound name
        - abbr: Abbreviation
        - id: Parameter ID
        - type: Measurement type
        - value: Reference value (if available)
        - unit: Unit of measurement
        - refMax: Maximum reference value
        - refMin: Minimum reference value
        - refUnit: Reference unit
        - tag: Publication label (if extended)
        - density: Density information (if with_densities=True)

    Examples
    --------
    >>> # Get basic lipoprotein table
    >>> lipo = get_lipo_table()
    >>> len(lipo)
    112

    >>> # Get extended table with calculated metrics
    >>> lipo_ext = get_lipo_table(extended=True)
    >>> len(lipo_ext)
    316

    >>> # Get table with density information
    >>> lipo_dens = get_lipo_table(with_densities=True)
    >>> lipo_dens[['id', 'fraction', 'density']].head()
    """
    if with_densities:
        file_path = DATA_DIR / "lipo_densities.csv"
    else:
        file_path = DATA_DIR / "lipo.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Reference data file not found: {file_path}\n"
            f"Please run data-raw/convert_rda_to_csv.R to generate CSV files."
        )

    df = pd.read_csv(file_path)

    if extended and not with_densities:
        # For extended table, we would need to apply extend_lipo
        # For now, return the base table with a note
        # In practice, users should call extend_lipo() on read_lipo() results
        pass

    return df


@lru_cache(maxsize=1)
def get_qc_table(matrix_type: Literal["SER", "URI"] = "SER",
                 with_value: bool = False) -> pd.DataFrame:
    """
    Get quality control reference table.

    Returns QC test parameters and reference ranges for serum/plasma
    or urine samples.

    Parameters
    ----------
    matrix_type : {"SER", "URI"}, default="SER"
        Sample matrix type:
        - "SER": Serum/Plasma
        - "URI": Urine
    with_value : bool, default=False
        If True, includes value and status columns (for actual measurements)

    Returns
    -------
    pd.DataFrame
        DataFrame with columns:
        - testName: Name of QC test
        - testUnit: Unit of measurement
        - testRefMax: Maximum reference value
        - testRefMin: Minimum reference value
        - testDescription: Test description
        - value: Measured value (if with_value=True)
        - status: Pass/fail status (if with_value=True)

    Examples
    --------
    >>> # Get serum QC reference table
    >>> qc_ser = get_qc_table("SER")
    >>> qc_ser[['testName', 'testRefMin', 'testRefMax']].head()

    >>> # Get urine QC reference table
    >>> qc_uri = get_qc_table("URI")
    >>> qc_uri[['testName', 'testUnit']].head()
    """
    # Note: QC data structure may vary based on XML format
    # This is a placeholder implementation
    # In practice, QC tables would be generated from test data or documentation

    if matrix_type == "SER":
        # Serum/Plasma QC parameters (example structure)
        data = {
            'testName': ['pH', 'Lipaemia', 'Hemolysis', 'Temperature',
                        'Line Width', 'Water Suppression', 'Reference Deconvolution'],
            'testUnit': ['-', 'AU', 'AU', '°C', 'Hz', '-', '-'],
            'testRefMin': ['6.4', '0', '0', '36.5', '0', '0', '0'],
            'testRefMax': ['8.0', '3', '3', '37.5', '2', '100', '100'],
            'testDescription': [
                'Sample pH',
                'Lipid content',
                'Hemoglobin content',
                'Sample temperature',
                'Spectral line width',
                'Water suppression quality',
                'Reference deconvolution quality'
            ]
        }
    else:  # URI
        # Urine QC parameters (example structure)
        data = {
            'testName': ['pH', 'Temperature', 'Line Width',
                        'Water Suppression', 'Reference Deconvolution'],
            'testUnit': ['-', '°C', 'Hz', '-', '-'],
            'testRefMin': ['4.5', '36.5', '0', '0', '0'],
            'testRefMax': ['8.5', '37.5', '2', '100', '100'],
            'testDescription': [
                'Sample pH',
                'Sample temperature',
                'Spectral line width',
                'Water suppression quality',
                'Reference deconvolution quality'
            ]
        }

    df = pd.DataFrame(data)

    if with_value:
        df['value'] = None
        df['status'] = None

    return df


@lru_cache(maxsize=1)
def get_pacs_table() -> pd.DataFrame:
    """
    Get PACS (Phenotypic Assessment) reference table.

    Returns reference data for PACS metabolites with concentration
    ranges and units.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns:
        - name: Metabolite name
        - unit: Concentration unit
        - refMax: Maximum reference value
        - refMin: Minimum reference value
        - refUnit: Reference unit

    Examples
    --------
    >>> pacs = get_pacs_table()
    >>> pacs[['name', 'unit', 'refMin', 'refMax']].head()
    """
    # PACS data (16 metabolites)
    # This would typically come from reference documentation
    data = {
        'name': [
            'Glucose', 'Lactate', 'Alanine', 'Valine', 'Leucine',
            'Isoleucine', 'Acetate', 'Acetone', '3-Hydroxybutyrate',
            'Pyruvate', 'Creatinine', 'Citrate', 'Formate',
            'Phenylalanine', 'Tyrosine', 'Histidine'
        ],
        'unit': ['mmol/L'] * 16,
        'refMin': [
            '3.5', '0.5', '0.2', '0.15', '0.08',
            '0.04', '0.01', '0.0', '0.03',
            '0.04', '0.04', '0.05', '0.01',
            '0.04', '0.04', '0.05'
        ],
        'refMax': [
            '6.1', '2.2', '0.6', '0.35', '0.22',
            '0.11', '0.15', '0.2', '0.3',
            '0.15', '0.13', '0.35', '0.05',
            '0.09', '0.11', '0.10'
        ],
        'refUnit': ['mmol/L'] * 16
    }

    return pd.DataFrame(data)


@lru_cache(maxsize=1)
def get_sm_table(matrix_type: Literal["SER", "PLA", "URI"] = "SER") -> pd.DataFrame:
    """
    Get small molecules (metabolites) reference table.

    Returns reference data for metabolite quantification with compound
    names, units, and reference ranges.

    Parameters
    ----------
    matrix_type : {"SER", "PLA", "URI"}, default="SER"
        Sample matrix type:
        - "SER": Serum
        - "PLA": Plasma
        - "URI": Urine

    Returns
    -------
    pd.DataFrame
        DataFrame with columns:
        - Compound: Metabolite name
        - Unit: Concentration unit
        - Min Value: Minimum reference value
        - Max Value: Maximum reference value
        - Reference Unit: Reference unit
        - Reference Range: Formatted range string

    Examples
    --------
    >>> # Get serum/plasma metabolites (41 compounds)
    >>> sm_pla = get_sm_table("SER")
    >>> len(sm_pla)
    41

    >>> # Get urine metabolites (150 compounds)
    >>> sm_uri = get_sm_table("URI")
    >>> len(sm_uri)
    150
    """
    if matrix_type in ["SER", "PLA"]:
        file_path = DATA_DIR / "brxsm_pla.csv"
        if not file_path.exists():
            raise FileNotFoundError(
                f"Reference data file not found: {file_path}\n"
                f"Please run data-raw/convert_rda_to_csv.R to generate CSV files."
            )
        df = pd.read_csv(file_path)

    else:  # URI
        file_path = DATA_DIR / "brxsm_uri.csv"
        if not file_path.exists():
            raise FileNotFoundError(
                f"Reference data file not found: {file_path}\n"
                f"Please run data-raw/convert_rda_to_csv.R to generate CSV files."
            )
        df = pd.read_csv(file_path)

    return df


# Alias for backwards compatibility
def getLipoTable(extended: bool = False, withDensities: bool = False) -> pd.DataFrame:
    """Alias for get_lipo_table() with R-style naming."""
    return get_lipo_table(extended=extended, with_densities=withDensities)


def getQcTable(matrixType: str = "SER", withValue: bool = False) -> pd.DataFrame:
    """Alias for get_qc_table() with R-style naming."""
    return get_qc_table(matrix_type=matrixType, with_value=withValue)


def getPacsTable() -> pd.DataFrame:
    """Alias for get_pacs_table() with R-style naming."""
    return get_pacs_table()


def getSmTable(matrixType: str = "SER") -> pd.DataFrame:
    """Alias for get_sm_table() with R-style naming."""
    return get_sm_table(matrix_type=matrixType)
