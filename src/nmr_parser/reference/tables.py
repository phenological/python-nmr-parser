"""Reference table functions for accessing pre-loaded metabolite and lipoprotein data."""

import pandas as pd
from pathlib import Path
from functools import lru_cache
from typing import Literal


# Data directory path
DATA_DIR = Path(__file__).parent / "data"


@lru_cache(maxsize=1)
def get_lipo_table(extended: bool = False, with_densities: bool = False) -> pd.DataFrame:
    """
    Get lipoprotein reference table.

    Returns reference data for lipoprotein measurements from test reports.

    Parameters
    ----------
    extended : bool, default=False
        If True, applies extend_lipo to add calculated metrics
        If False, returns raw measurements only
    with_densities : bool, default=False
        Not currently supported (reserved for future use)

    Returns
    -------
    pd.DataFrame
        DataFrame with lipoprotein measurements and reference ranges

    Examples
    --------
    >>> # Get basic lipoprotein table
    >>> lipo = get_lipo_table()
    >>> lipo[['id', 'value', 'unit']].head()
    """
    from nmr_parser.xml_parsers.lipoproteins import read_lipo

    xml_path = DATA_DIR / "lipo_results.xml"

    if not xml_path.exists():
        raise FileNotFoundError(
            f"Lipoprotein reference data not found: {xml_path}"
        )

    lipo = read_lipo(xml_path)
    if lipo is None:
        raise ValueError(f"Failed to read lipoprotein data from {xml_path}")

    df = lipo['data'].copy()

    if extended:
        from nmr_parser.processing.lipoprotein_calc import extend_lipo
        result = extend_lipo(lipo)
        df = result['data']

    return df


@lru_cache(maxsize=1)
def get_qc_table(matrix_type: Literal["SER", "URI"] = "SER",
                 with_value: bool = False) -> pd.DataFrame:
    """
    Get quality control reference table.

    Returns QC test parameters and reference ranges for serum/plasma
    or urine samples. For plasma/serum, merges data from multiple
    reference XML files to capture all possible QC parameters.

    Parameters
    ----------
    matrix_type : {"SER", "URI"}, default="SER"
        Sample matrix type:
        - "SER": Serum/Plasma
        - "URI": Urine
    with_value : bool, default=False
        If True, includes value and comment columns (for actual measurements)

    Returns
    -------
    pd.DataFrame
        DataFrame with columns:
        - name: Name of QC test parameter
        - type: Test category/type
        - unit: Unit of measurement
        - refMax: Maximum reference value
        - refMin: Minimum reference value
        - value: Measured value (if with_value=True)
        - comment: Test comment/status (if with_value=True)

    Examples
    --------
    >>> # Get serum/plasma QC reference table
    >>> qc_ser = get_qc_table("SER")
    >>> qc_ser[['name', 'type', 'unit']].head()

    >>> # Get urine QC reference table
    >>> qc_uri = get_qc_table("URI")
    >>> qc_uri[['name', 'refMin', 'refMax']].head()
    """
    from nmr_parser.xml_parsers.quality_control import read_qc

    if matrix_type == "SER":
        xml_path = DATA_DIR / "plasma_qc_report_2.xml"

        if not xml_path.exists():
            raise FileNotFoundError(
                f"Plasma QC reference data not found: {xml_path}"
            )

        qc = read_qc(xml_path)
        if qc is None:
            raise ValueError(f"Failed to read QC data from {xml_path}")

        df = pd.DataFrame(qc['data']['tests'])

    else:  # URI
        xml_path = DATA_DIR / "urine_qc_report.xml"

        if not xml_path.exists():
            raise FileNotFoundError(
                f"Urine QC reference data not found: {xml_path}"
            )

        qc = read_qc(xml_path)
        if qc is None:
            raise ValueError(f"Failed to read QC data from {xml_path}")

        df = pd.DataFrame(qc['data']['tests'])

    # Select columns to return
    if with_value:
        df = df[['name', 'type', 'unit', 'refMax', 'refMin', 'value', 'comment']]
    else:
        df = df[['name', 'type', 'unit', 'refMax', 'refMin']]

    return df


@lru_cache(maxsize=1)
def get_pacs_table() -> pd.DataFrame:
    """
    Get PACS (Phenotypic Assessment and Clinical Screening) reference table.

    Returns reference data for PACS parameters with concentration
    ranges and units from test report XML files.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns:
        - name: Parameter name (e.g., 'Glucose', 'TG', 'Chol', 'Apo-A1', 'Apo-B100')
        - unit: Concentration unit
        - refMax: Maximum reference value
        - refMin: Minimum reference value
        - refUnit: Reference unit

    Notes
    -----
    PACS includes 16 parameters:
    - Glucose, Creatinine (clinical chemistry)
    - Lipoproteins: TG, Chol, LDL-Chol, HDL-Chol, LDL-Phos, HDL-Phos
    - Apolipoproteins: Apo-A1, Apo-B100, Apo-B100/Apo-A1
    - Glycoproteins: GlycA, GlycB, Glyc, SPC, Glyc/SPC

    Examples
    --------
    >>> pacs = get_pacs_table()
    >>> pacs[['name', 'unit', 'refMin', 'refMax']].head()
           name    unit refMin refMax
    0   Glucose  mmol/l   1.73   6.08
    1  Creatinine mmol/l   0.06   0.14
    2        TG   mg/dL     53    490
    3      Chol   mg/dL    140    341
    4  LDL-Chol   mg/dL     55    227

    >>> # Get only lipoproteins (exclude Glucose, Creatinine)
    >>> lipoproteins = pacs[~pacs['name'].isin(['Glucose', 'Creatinine'])]
    >>> len(lipoproteins)
    14
    """
    # Import read_pacs function
    from nmr_parser.xml_parsers.pacs import read_pacs

    # Path to reference XML file in package data directory
    xml_path = DATA_DIR / "plasma_pacs_report.xml"

    if not xml_path.exists():
        raise FileNotFoundError(
            f"PACS reference data file not found: {xml_path}\n"
            f"Please ensure plasma_pacs_report.xml is available in the package data directory."
        )

    # Read PACS data
    pacs = read_pacs(xml_path)

    if pacs is None:
        raise ValueError(f"Failed to read PACS data from {xml_path}")

    # Extract dataframe and rename columns to match R function output
    tbl = pacs['data'].copy()
    tbl.columns = ['name', 'conc', 'unit', 'refMax', 'refMin', 'refUnit']

    # Return only the reference columns (drop conc)
    tbl = tbl[['name', 'unit', 'refMax', 'refMin', 'refUnit']]

    return tbl


@lru_cache(maxsize=1)
def get_sm_table(matrix_type: Literal["SER", "PLA", "URI"] = "SER") -> pd.DataFrame:
    """
    Get small molecules (metabolites) reference table.

    Returns reference data for metabolite quantification from test reports.

    Parameters
    ----------
    matrix_type : {"SER", "PLA", "URI"}, default="SER"
        Sample matrix type:
        - "SER": Serum (uses plasma data)
        - "PLA": Plasma
        - "URI": Urine

    Returns
    -------
    pd.DataFrame
        DataFrame with metabolite data including reference ranges

    Examples
    --------
    >>> # Get plasma metabolites (41 compounds)
    >>> sm_pla = get_sm_table("PLA")
    >>> sm_pla[['name', 'conc_v', 'concUnit_v']].head()

    >>> # Get urine metabolites (150 compounds)
    >>> sm_uri = get_sm_table("URI")
    >>> len(sm_uri)
    150
    """
    from nmr_parser.xml_parsers.quantification import read_quant

    if matrix_type in ["SER", "PLA"]:
        xml_path = DATA_DIR / "plasma_quant_report.xml"
    else:  # URI
        xml_path = DATA_DIR / "urine_quant_report_e.xml"

    if not xml_path.exists():
        raise FileNotFoundError(
            f"Small molecule reference data not found: {xml_path}"
        )

    quant = read_quant(xml_path)
    if quant is None:
        raise ValueError(f"Failed to read quantification data from {xml_path}")

    return quant['data'].copy()


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
