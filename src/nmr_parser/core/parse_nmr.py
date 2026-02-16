"""
Parse NMR data and export to parquet files.

This module migrates the parseNMR.R functionality to Python, preserving all
research decisions while replacing the dataElement structure with parquet files.
"""

from pathlib import Path
from typing import Union, Optional, Dict, Any, List, Tuple
import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
import hashlib
import logging
from rich.console import Console
from rich.prompt import Prompt

try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

from .experiment import read_experiment
from .folders import scan_folder
from .parameters import read_param
from ..processing.utils import clean_names
from ..version import __version__
from .logger import get_logger, LogLevel

console = Console()
logger = logging.getLogger(__name__)


def parse_nmr(
    folder: Union[str, Path, List[str], Dict[str, Any]],
    opts: Optional[Dict[str, Any]] = None
) -> Dict[str, pd.DataFrame]:
    """
    Parse NMR data from Bruker folders and export to parquet files.

    Migrated from parseNMR.R, preserving all research decisions while using
    parquet format instead of dataElement objects.

    Parameters
    ----------
    folder : str, Path, list, or dict
        Input data source:
        - str/Path: Local folder path to scan
        - list: List of experiment paths (direct mode)
        - dict: Rolodex request (future implementation)

    opts : dict, optional
        Processing options:

        - what : str or list of str
            Data types to read: 'spec', 'spcglyc', 'brxlipo', 'brxpacs', 'brxsm'
            Default: ['spec']

        - projectName : str
            Project identifier (default: '')

        - cohortName : str
            Cohort identifier (default: '')

        - runName : str
            Run identifier (default: '')

        - method : str
            Method name (default: auto-detected)

        - sampleMatrixType : str
            Sample matrix type (default: '')

        - specOpts : dict
            Spectrum reading options:
            - procno : int (default: 1)
            - uncalibrate : bool (default: False)
            - fromTo : tuple (default: (-0.1, 10))
            - length_out : int (default: 44079)
            - im : bool (default: False) - read imaginary part

        - outputDir : str or Path
            Output directory for parquet files (default: '.')

        - noWrite : bool
            If True, return DataFrames without writing files (default: False)

        - verbosity : str
            Logging verbosity: 'prod', 'info', or 'debug' (default: 'info')

    Returns
    -------
    dict
        Dictionary with keys: 'data', 'metadata', 'params', 'variables'
        Each value is a pandas DataFrame

    Notes
    -----
    Output files:
    - {run_id}_data.parquet : Main data matrix
    - {run_id}_metadata.parquet : Sample and run metadata
    - {run_id}_params.parquet : Acquisition/processing parameters
    - {run_id}_variables.parquet : Variable definitions

    For spcglyc, additional files:
    - {run_id}_tsp.parquet : TSP reference region
    - {run_id}_spc_region.parquet : Full SPC region
    - {run_id}_glyc_region.parquet : Full Glyc region

    Examples
    --------
    >>> # Parse spectra from local folder
    >>> result = parse_nmr(
    ...     "data/experiments/",
    ...     opts={
    ...         'what': ['spec'],
    ...         'projectName': 'HB',
    ...         'cohortName': 'COVID',
    ...         'runName': 'EXTr01',
    ...         'sampleMatrixType': 'plasma'
    ...     }
    ... )

    >>> # Parse spcglyc biomarkers
    >>> result = parse_nmr(
    ...     "data/experiments/",
    ...     opts={'what': ['spcglyc']}
    ... )

    >>> # Parse from direct paths
    >>> paths = ['exp1/10', 'exp2/10', 'exp3/10']
    >>> result = parse_nmr(
    ...     {"dataPath": paths},
    ...     opts={'noWrite': True}
    ... )
    """
    # ========================================================================
    # CONFIGURATION
    # ========================================================================

    # Define default options
    default_opts = {
        'what': ['spec'],
        'projectName': '',
        'cohortName': '',
        'runName': '',
        'method': '',
        'sampleMatrixType': '',
        'specOpts': {
            'procno': 1,
            'uncalibrate': False,
            'fromTo': (-0.1, 10),
            'length_out': 44079,
            'im': False
        },
        'EXP': '',
        'outputDir': '.',
        'noWrite': False,
        'verbosity': 'info'
    }

    # Merge provided options with defaults
    if opts is None:
        opts = default_opts
    else:
        # Handle nested specOpts
        if 'specOpts' in opts and opts['specOpts'] is not None:
            opts['specOpts'] = {**default_opts['specOpts'], **opts['specOpts']}
        opts = {**default_opts, **opts}

    # Create logger with specified verbosity
    log = get_logger(opts['verbosity'])

    # Handle spcglyc special case (lines 50-57 in R)
    if 'spcglyc' in opts['what']:
        opts['what'] = ['spec']  # Read spec first
        spcglyc = True
        opts['specOpts']['uncalibrate'] = True
    else:
        spcglyc = False

    no_write = opts['noWrite']

    # ========================================================================
    # INPUT PROCESSING
    # ========================================================================

    # Handle different input types
    if isinstance(folder, dict) and 'content' in folder:
        # CASE 1: Rolodex request (lines 60-110)
        loe = _process_rolodex_input(folder, opts, log)
        no_write = False

    elif isinstance(folder, dict) and 'dataPath' in folder:
        # CASE 2: Direct paths (lines 112-121)
        loe = _process_direct_paths(folder, log)
        no_write = True

    else:
        # CASE 3: Local folder (lines 123-227)
        loe = _process_local_folder(folder, opts, log)

    # Classify sample types (lines 98-108)
    loe = _classify_sample_types(loe, log)

    log.info(f"Processing {len(loe)} samples")

    # ========================================================================
    # READING DATA
    # ========================================================================

    data_matrix = None
    var_names = None
    data_type = None

    # Read spectra (lines 234-278)
    if 'spec' in opts['what']:
        log.step("Reading spectra")
        data_matrix, var_names, data_type = _read_spectra(loe, opts, log)

    # Handle other data types
    elif 'brxlipo' in opts['what']:
        log.step("Reading lipoprotein data")
        data_matrix, var_names, data_type = _read_brxlipo(loe, opts, log)

    elif 'brxpacs' in opts['what']:
        log.step("Reading PACS data")
        data_matrix, var_names, data_type = _read_brxpacs(loe, opts, log)

    elif 'brxsm' in opts['what']:
        log.step("Reading small molecule data")
        data_matrix, var_names, data_type = _read_brxsm(loe, opts, log)

    if data_matrix is None:
        raise ValueError("No data was read. Check input parameters.")

    # Apply spcglyc calculations (lines 280-359)
    if spcglyc:
        log.step("Calculating spcglyc biomarkers")
        ppm = np.linspace(
            opts['specOpts']['fromTo'][0],
            opts['specOpts']['fromTo'][1],
            opts['specOpts']['length_out']
        )
        data_matrix, var_names, extra_data = _calculate_spcglyc(
            data_matrix, ppm, loe, log
        )
        data_type = 'QUANT'
        opts['method'] = f"spcglyc_{loe['experiment'].iloc[0]}"

    # ========================================================================
    # READING PARAMETERS AND QUALITY CHECKS
    # ========================================================================

    log.step("Reading acquisition parameters", LogLevel.INFO)
    acqus_data = _read_acqus_params(loe['dataPath'].tolist(), log)

    log.step("Checking for IVDr QC data", LogLevel.INFO)
    qc_data, is_ivdr = _read_qc_data(loe['dataPath'].tolist(), log)

    # ========================================================================
    # MERGING AND ALIGNMENT
    # ========================================================================

    log.step("Merging data sources", LogLevel.INFO)
    data_matrix, loe, acqus_data, qc_data = _merge_data_sources(
        data_matrix, loe, acqus_data, qc_data, log
    )

    # ========================================================================
    # CREATE OUTPUT DATAFRAMES
    # ========================================================================

    # Generate sample keys for joining
    sample_keys = _generate_sample_keys(loe)
    loe['sample_key'] = sample_keys

    # 1. Data matrix
    data_df = pd.DataFrame(data_matrix, columns=var_names)
    data_df.insert(0, 'sample_key', sample_keys)
    data_df = data_df.set_index('sample_key')

    # 2. Metadata
    metadata_df = _create_metadata_df(loe, opts, data_type, is_ivdr)

    # 3. Parameters (long format)
    params_df = _create_params_df(sample_keys, acqus_data, qc_data)

    # 4. Variables
    variables_df = _create_variables_df(var_names, data_type, opts, spcglyc)

    # ========================================================================
    # WRITE PARQUET FILES
    # ========================================================================

    result = {
        'data': data_df,
        'metadata': metadata_df,
        'params': params_df,
        'variables': variables_df
    }

    if spcglyc and 'extra_data' in locals():
        result.update(extra_data)

    # Build sample type breakdown for summary
    type_counts = result['metadata']['sample_type'].value_counts()
    type_breakdown = " | ".join([f"{stype}: {count}" for stype, count in type_counts.items()])

    # Prepare summary data
    summary_data = {
        "Samples": f"{len(result['data'])} ({type_breakdown})",
        "Variables": len(result['variables']),
        "Data type": result['metadata']['data_type'].iloc[0],
        "Method": result['metadata']['method'].iloc[0]
    }

    if not no_write:
        output_dir = Path(opts['outputDir'])
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate file name
        file_name = _generate_file_name(opts)

        # Write parquet files
        _write_parquet_files(result, file_name, output_dir, log)

        # Add output info to summary
        summary_data["Output dir"] = str(output_dir)
        summary_data["Base name"] = file_name

    # Show summary (at PROD level)
    log.summary("Parse Complete", summary_data, LogLevel.PROD)

    return result


# ============================================================================
# INPUT PROCESSING FUNCTIONS
# ============================================================================

def _process_rolodex_input(folder: Dict, opts: Dict, log) -> pd.DataFrame:
    """Process input from Rolodex API request (lines 60-110)."""
    # This will be implemented when Rolodex integration is needed
    log.error("Rolodex input processing not yet implemented")
    raise NotImplementedError("Rolodex input processing not yet implemented")


def _process_direct_paths(folder: Dict, log) -> pd.DataFrame:
    """Process direct path input (lines 112-121)."""
    if isinstance(folder['dataPath'], list):
        paths = folder['dataPath']
    else:
        paths = [folder['dataPath']]

    log.debug(f"Processing {len(paths)} direct paths")

    loe = pd.DataFrame({
        'dataPath': paths,
        'sampleID': [f'sampleID_{i}' for i in range(len(paths))],
        'sampleType': ['sample'] * len(paths),
        'experiment': ['experiment_'] * len(paths)
    })

    return loe


def _process_local_folder(folder: Union[str, Path], opts: Dict, log) -> pd.DataFrame:
    """Process local folder input (lines 123-227)."""
    folder = Path(folder)

    log.step("Scanning folder for experiments", LogLevel.INFO)

    # Scan folder for experiments
    lof = scan_folder(folder, options=opts, verbosity=opts.get('verbosity', 'info'))

    if len(lof) == 0:
        raise ValueError(f"No experiments found in {folder}")

    # Get experiment name
    exp = clean_names(lof['EXP'].iloc[0])

    # Check for ANPC sampleID in USERA2 (lines 192-217)
    if not lof['USERA2'].isna().all() and lof['USERA2'].iloc[0] != '':
        log.info("ANPC sampleID (USERA2) found")
        sample_ids = lof['USERA2'].tolist()
        # Normalize QC labels (lines 196-200)
        sample_ids = [s.replace('SLTR', 'sltr') for s in sample_ids]
        sample_ids = [s.replace('LTR', 'ltr') for s in sample_ids]
        sample_ids = [s.replace('PQC', 'pqc') for s in sample_ids]
        sample_ids = [s.replace('QC', 'qc') for s in sample_ids]
    else:
        # Use interactive selection or timestamps
        log.warning("No USERA2 found. Using folder structure for sample IDs")
        # For now, use simple timestamps
        sample_ids = _make_unique([f"sample_{i:04d}" for i in range(len(lof))])

    # Making sampleID unique (lines 220)
    sample_ids = _make_unique(sample_ids)

    loe = pd.DataFrame({
        'dataPath': lof['file'].tolist(),
        'sampleID': sample_ids,
        'sampleType': ['sample'] * len(lof),
        'experiment': [exp] * len(lof)
    })

    return loe


def _classify_sample_types(loe: pd.DataFrame, log) -> pd.DataFrame:
    """
    Classify sample types based on sampleID patterns.

    Lines 98-108 in R code. CRITICAL research decision.
    """
    loe = loe.copy()

    type_counts = {'sltr': 0, 'ltr': 0, 'pqc': 0, 'qc': 0, 'sample': 0}

    for idx, row in loe.iterrows():
        sample_id = row['sampleID'].lower()

        # Priority order matters!
        if 'sltr' in sample_id:
            loe.at[idx, 'sampleType'] = 'sltr'
            type_counts['sltr'] += 1
        elif sample_id.startswith('ltr'):
            loe.at[idx, 'sampleType'] = 'ltr'
            type_counts['ltr'] += 1
        elif sample_id.startswith('pqc'):
            loe.at[idx, 'sampleType'] = 'pqc'
            type_counts['pqc'] += 1
        elif sample_id.startswith('qc'):
            loe.at[idx, 'sampleType'] = 'qc'
            type_counts['qc'] += 1
        else:
            type_counts['sample'] += 1

    # Log classification results at DEBUG level
    log.debug(f"Sample classification: {type_counts}")

    return loe


def _make_unique(names: List[str]) -> List[str]:
    """Make names unique by appending _1, _2, etc. to duplicates."""
    seen = {}
    result = []

    for name in names:
        if name not in seen:
            seen[name] = 0
            result.append(name)
        else:
            seen[name] += 1
            result.append(f"{name}_{seen[name]}")

    return result


# ============================================================================
# DATA READING FUNCTIONS
# ============================================================================

def _read_spectra(
    loe: pd.DataFrame,
    opts: Dict,
    log
) -> Tuple[np.ndarray, List[str], str]:
    """Read NMR spectra (lines 234-278)."""
    paths = loe['dataPath'].tolist()

    log.debug(f"Reading spectra from {len(paths)} paths")

    # Read all experiments
    experiments = read_experiment(
        paths,
        opts={'what': ['spec'], 'specOpts': opts['specOpts']}
    )

    if 'spec' not in experiments or experiments['spec'] is None:
        raise ValueError("No spectra found")

    spec_df = experiments['spec']

    # Extract spectra into matrix
    n_samples = len(spec_df)
    n_points = opts['specOpts']['length_out']

    # Check if reading imaginary part too
    if opts['specOpts'].get('im', False):
        # Complex data
        data_matrix = np.zeros((n_samples, n_points), dtype=np.complex128)
        for i, row in spec_df.iterrows():
            spec_result = row['spec'][0]  # spec is a list with one SpectrumResult
            spec_data = spec_result.spec  # Get the DataFrame from SpectrumResult
            data_matrix[i, :] = spec_data['y'].values + 1j * spec_data['yi'].values
    else:
        # Real data only
        data_matrix = np.zeros((n_samples, n_points))
        for i, row in spec_df.iterrows():
            spec_result = row['spec'][0]  # spec is a list with one SpectrumResult
            spec_data = spec_result.spec  # Get the DataFrame from SpectrumResult
            data_matrix[i, :] = spec_data['y'].values

    # Generate PPM axis
    ppm = np.linspace(
        opts['specOpts']['fromTo'][0],
        opts['specOpts']['fromTo'][1],
        opts['specOpts']['length_out']
    )

    var_names = [str(p) for p in ppm]
    data_type = 'NMR'

    # Log spectrum grid info once (not per spectrum!)
    log.debug(
        f"Spectra in common grid: {opts['specOpts']['fromTo'][0]} to "
        f"{opts['specOpts']['fromTo'][1]} ppm, {opts['specOpts']['length_out']} points"
    )

    # Set method name (line 245)
    if opts['method'] == '':
        # This would use interactive menu in R, for now use experiment name
        opts['method'] = f"noesygppr1d@{loe['experiment'].iloc[0]}"
    else:
        opts['method'] = f"{opts['method']}@{loe['experiment'].iloc[0]}"

    return data_matrix, var_names, data_type


def _read_brxlipo(loe: pd.DataFrame, opts: Dict, log) -> Tuple[np.ndarray, List[str], str]:
    """Read Bruker lipoprotein data (lines 361-374)."""
    paths = loe['dataPath'].tolist()
    log.debug(f"Reading brxlipo from {len(paths)} paths")

    experiments = read_experiment(paths, opts={'what': ['lipo']})

    if 'lipo' not in experiments or experiments['lipo'] is None:
        raise ValueError("No brxlipo data found")

    lipo_data = experiments['lipo']
    # Extract value columns
    value_cols = [c for c in lipo_data.columns if c.startswith('value.')]
    data_matrix = lipo_data[value_cols].values
    var_names = [c.replace('value.', '') for c in value_cols]

    log.debug(f"Extracted {len(var_names)} lipoprotein variables")
    opts['method'] = 'brxlipo'
    return data_matrix, var_names, 'QUANT'


def _read_brxpacs(loe: pd.DataFrame, opts: Dict, log) -> Tuple[np.ndarray, List[str], str]:
    """Read Bruker PACS data (lines 376-389)."""
    paths = loe['dataPath'].tolist()
    log.debug(f"Reading brxpacs from {len(paths)} paths")

    experiments = read_experiment(paths, opts={'what': ['pacs']})

    if 'pacs' not in experiments or experiments['pacs'] is None:
        raise ValueError("No brxpacs data found")

    pacs_data = experiments['pacs']
    value_cols = [c for c in pacs_data.columns if c.startswith('value.')]
    data_matrix = pacs_data[value_cols].values
    var_names = [c.replace('value.', '') for c in value_cols]

    log.debug(f"Extracted {len(var_names)} PACS variables")
    opts['method'] = 'brxpacs'
    return data_matrix, var_names, 'QUANT'


def _read_brxsm(loe: pd.DataFrame, opts: Dict, log) -> Tuple[np.ndarray, List[str], str]:
    """Read Bruker small molecule quant data (lines 391-404)."""
    paths = loe['dataPath'].tolist()
    log.debug(f"Reading brxsm from {len(paths)} paths")

    experiments = read_experiment(paths, opts={'what': ['quant']})

    if 'quant' not in experiments or experiments['quant'] is None:
        raise ValueError("No brxsm data found")

    quant_data = experiments['quant']
    value_cols = [c for c in quant_data.columns if c.startswith('value.')]
    data_matrix = quant_data[value_cols].values
    var_names = [c.replace('value.', '') for c in value_cols]

    log.debug(f"Extracted {len(var_names)} small molecule variables")
    opts['method'] = 'brxsm'
    return data_matrix, var_names, 'QUANT'


def _calculate_spcglyc(
    spectra: np.ndarray,
    ppm: np.ndarray,
    loe: pd.DataFrame,
    log
) -> Tuple[np.ndarray, List[str], Dict]:
    """
    Calculate spcglyc biomarkers.

    Lines 280-359 in R code. CRITICAL research decisions preserved.

    This function implements the calculation of glycoprotein and
    supramolecular phospholipid composite biomarkers from NMR spectra.
    """
    # 1. Trim specific PPM regions (lines 282-289)
    log.debug("Trimming PPM regions: water (4.6-4.85), baseline (<0.2), high (>10.0)")
    exclude_idx = (
        ((ppm >= 4.6) & (ppm <= 4.85)) |  # Water region
        ((ppm >= ppm.min()) & (ppm <= 0.2)) |  # Baseline
        (ppm >= 10.0)  # High PPM
    )

    trimmed_spectra = spectra[:, ~exclude_idx]
    trimmed_ppm = ppm[~exclude_idx]
    dw = trimmed_ppm[1] - trimmed_ppm[0]  # Delta PPM

    # 2. Check for 180° flip (lines 293-299)
    # CRITICAL: If sum of 3.2-3.3 region is negative, flip spectrum
    region_3_2_3_3 = trimmed_spectra[:, (trimmed_ppm >= 3.2) & (trimmed_ppm <= 3.3)]
    flip_idx = np.where(region_3_2_3_3.sum(axis=1) < 0)[0]

    if len(flip_idx) > 0:
        log.debug(f"Flipping {len(flip_idx)} spectra (180° phase correction)")
        trimmed_spectra[flip_idx, :] = -trimmed_spectra[flip_idx, :]

    # 3. Extract specific regions for output (lines 301-316)
    # TSP region (0-0.5 ppm)
    tsp_region = spectra[:, (ppm >= ppm.min()) & (ppm <= 0.5)]
    tsp_ppm = ppm[(ppm >= ppm.min()) & (ppm <= 0.5)]

    # SPC region (3.18-3.32 ppm)
    spc_region = trimmed_spectra[:, (trimmed_ppm > 3.18) & (trimmed_ppm < 3.32)]
    spc_ppm = trimmed_ppm[(trimmed_ppm > 3.18) & (trimmed_ppm < 3.32)]

    # Glyc region (2.050-2.118 ppm)
    glyc_region = trimmed_spectra[:, (trimmed_ppm > 2.050) & (trimmed_ppm < 2.118)]
    glyc_ppm = trimmed_ppm[(trimmed_ppm > 2.050) & (trimmed_ppm < 2.118)]

    # 4. Calculate biomarkers by integration (lines 319-347)
    # CRITICAL: All integrations use sum * dw
    def integrate_region(ppm_min: float, ppm_max: float) -> np.ndarray:
        """Integrate spectrum in PPM range."""
        mask = (trimmed_ppm > ppm_min) & (trimmed_ppm < ppm_max)
        return trimmed_spectra[:, mask].sum(axis=1) * dw

    # SPC biomarkers
    spc_all = integrate_region(3.18, 3.32)
    spc3 = integrate_region(3.262, 3.3)
    spc2 = integrate_region(3.236, 3.262)
    spc1 = integrate_region(3.2, 3.236)

    # Glycoprotein biomarkers
    glyc_all = integrate_region(2.050, 2.118)
    glyc_a = integrate_region(2.050, 2.089)
    glyc_b = integrate_region(2.089, 2.118)

    # Albumin proxies
    alb1 = integrate_region(0.2, 0.7)
    alb2 = integrate_region(6.0, 10.0)

    # 5. Calculate ratios (lines 349-350)
    spc3_2 = spc3 / spc2
    spc_glyc = spc_all / glyc_all

    # 6. Apply 3mm tube correction (lines 356-357)
    # CRITICAL: Divide by 2 for 3mm tubes
    is_3mm = loe['dataPath'].str.contains('3mm', case=False).values
    if is_3mm.any():
        log.debug(f"Applying 3mm tube correction to {is_3mm.sum()} samples")
        for arr in [spc_all, spc3, spc2, spc1, glyc_all, glyc_a, glyc_b,
                    alb1, alb2, spc3_2, spc_glyc]:
            arr[is_3mm] = arr[is_3mm] / 2

    # Create output matrix
    data_matrix = np.column_stack([
        spc_all, spc3, spc2, spc1,
        glyc_all, glyc_a, glyc_b,
        alb1, alb2,
        spc3_2, spc_glyc
    ])

    var_names = [
        'SPC_All', 'SPC3', 'SPC2', 'SPC1',
        'Glyc_All', 'GlycA', 'GlycB',
        'Alb1', 'Alb2',
        'SPC3_2', 'SPC_Glyc'
    ]

    # Store extra data for output
    extra_data = {
        'tsp': pd.DataFrame(tsp_region, columns=[str(p) for p in tsp_ppm]),
        'spc_region': pd.DataFrame(spc_region, columns=[str(p) for p in spc_ppm]),
        'glyc_region': pd.DataFrame(glyc_region, columns=[str(p) for p in glyc_ppm])
    }

    return data_matrix, var_names, extra_data


def _read_acqus_params(paths: List[str], log) -> pd.DataFrame:
    """Read acquisition parameters (lines 409)."""
    log.debug(f"Reading acquisition parameters from {len(paths)} paths")
    experiments = read_experiment(paths, opts={'what': ['acqus']})

    if 'acqus' not in experiments:
        log.warning("No acquisition parameters found")
        return pd.DataFrame()

    return experiments['acqus']


def _read_qc_data(paths: List[str], log) -> Tuple[Optional[pd.DataFrame], bool]:
    """Read QC data and check for IVDr (lines 411-422)."""
    log.debug(f"Checking for QC data in {len(paths)} paths")
    experiments = read_experiment(paths, opts={'what': ['qc']})

    if 'qc' not in experiments or experiments['qc'] is None:
        log.info("Non-IVDr data (no QC found)")
        return None, False

    log.info("IVDr QC data found")
    return experiments['qc'], True


# ============================================================================
# DATA MERGING FUNCTIONS
# ============================================================================

def _merge_data_sources(
    data_matrix: np.ndarray,
    loe: pd.DataFrame,
    acqus_data: pd.DataFrame,
    qc_data: Optional[pd.DataFrame],
    log
) -> Tuple[np.ndarray, pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Merge data sources by finding path intersection.

    Lines 425-545 in R code. CRITICAL for data integrity.
    """
    # Get all paths
    loe_paths = set(loe['dataPath'].tolist())

    if len(acqus_data) > 0:
        acqus_paths = set(acqus_data['path'].tolist())
    else:
        acqus_paths = loe_paths

    if qc_data is not None and len(qc_data) > 0:
        qc_paths = set(qc_data['path'].tolist())
    else:
        qc_paths = loe_paths

    # Find intersection
    intersection = loe_paths & acqus_paths & qc_paths

    # Log excluded paths
    excluded = loe_paths - intersection
    if excluded:
        log.warning(f"Excluded {len(excluded)} paths (not present in all data sources)")
        for path in list(excluded)[:5]:  # Show first 5 at DEBUG level
            log.detail(path)

    # Filter all data sources
    loe_idx = loe['dataPath'].isin(intersection)
    data_matrix = data_matrix[loe_idx, :]
    loe = loe[loe_idx].reset_index(drop=True)

    if len(acqus_data) > 0:
        acqus_data = acqus_data[acqus_data['path'].isin(intersection)].reset_index(drop=True)

    if qc_data is not None and len(qc_data) > 0:
        qc_data = qc_data[qc_data['path'].isin(intersection)].reset_index(drop=True)

    return data_matrix, loe, acqus_data, qc_data


# ============================================================================
# OUTPUT CREATION FUNCTIONS
# ============================================================================

def _generate_sample_keys(loe: pd.DataFrame) -> List[str]:
    """Generate unique sample keys for joining."""
    keys = []
    for idx, row in loe.iterrows():
        # Use sampleID + hash of path for uniqueness
        path_hash = hashlib.md5(row['dataPath'].encode()).hexdigest()[:8]
        key = f"{row['sampleID']}_{path_hash}"
        keys.append(key)
    return keys


def _create_metadata_df(
    loe: pd.DataFrame,
    opts: Dict,
    data_type: str,
    is_ivdr: bool
) -> pd.DataFrame:
    """Create metadata DataFrame."""
    # Detect tube type from path
    tube_types = []
    for path in loe['dataPath']:
        if '3mm' in path.lower():
            tube_types.append('3mm')
        else:
            tube_types.append('5mm')

    metadata = pd.DataFrame({
        'sample_key': loe['sample_key'],
        'data_path': loe['dataPath'],
        'sample_id': loe['sampleID'],
        'sample_type': loe['sampleType'],
        'experiment': loe['experiment'],
        'nmr_folder_id': loe.get('nmrFolderId', [None] * len(loe)),
        'project_name': opts['projectName'],
        'cohort_name': opts['cohortName'],
        'run_name': opts['runName'],
        'sample_matrix_type': opts['sampleMatrixType'],
        'method': opts['method'],
        'data_type': data_type,
        'is_ivdr': is_ivdr,
        'tube_type': tube_types,
        'created_at': datetime.now(),
        'parser_version': __version__
    })

    return metadata.set_index('sample_key')


def _create_params_df(
    sample_keys: List[str],
    acqus_data: pd.DataFrame,
    qc_data: Optional[pd.DataFrame]
) -> pd.DataFrame:
    """Create parameters DataFrame in long format."""
    params_list = []

    # Add acqus parameters
    if len(acqus_data) > 0:
        for idx, key in enumerate(sample_keys):
            row = acqus_data.iloc[idx]
            for col in acqus_data.columns:
                if col != 'path':
                    params_list.append({
                        'sample_key': key,
                        'param_name': col,
                        'param_value': row[col],
                        'param_source': 'acqus'
                    })

    # Add QC parameters
    if qc_data is not None and len(qc_data) > 0:
        for idx, key in enumerate(sample_keys):
            row = qc_data.iloc[idx]
            for col in qc_data.columns:
                if col != 'path':
                    params_list.append({
                        'sample_key': key,
                        'param_name': col,
                        'param_value': row[col],
                        'param_source': 'qc'
                    })

    if not params_list:
        return pd.DataFrame(columns=['sample_key', 'param_name', 'param_value', 'param_source'])

    params_df = pd.DataFrame(params_list)
    return params_df.set_index(['sample_key', 'param_name'])


def _create_variables_df(
    var_names: List[str],
    data_type: str,
    opts: Dict,
    spcglyc: bool
) -> pd.DataFrame:
    """Create variables DataFrame."""
    n_vars = len(var_names)

    # Generate var_ids
    var_ids = [f"var_{i:05d}" for i in range(n_vars)]

    if spcglyc:
        # Special case for spcglyc biomarkers
        var_type = ['biomarker'] * n_vars
        var_unit = ['ratio'] * n_vars
        descriptions = [
            'Total SPC (3.18-3.32 ppm)',
            'SPC subregion 3 (3.262-3.3 ppm)',
            'SPC subregion 2 (3.236-3.262 ppm)',
            'SPC subregion 1 (3.2-3.236 ppm)',
            'Total Glycoprotein (2.050-2.118 ppm)',
            'GlycA (2.050-2.089 ppm)',
            'GlycB (2.089-2.118 ppm)',
            'Albumin proxy 1 (0.2-0.7 ppm)',
            'Albumin proxy 2 (6.0-10.0 ppm)',
            'SPC3/SPC2 ratio',
            'SPC/Glyc ratio'
        ]
        ppm_centers = [
            3.25, 3.281, 3.249, 3.218,
            2.084, 2.0695, 2.1035,
            0.45, 8.0,
            np.nan, np.nan
        ]
        ppm_mins = [3.18, 3.262, 3.236, 3.2, 2.050, 2.050, 2.089, 0.2, 6.0, np.nan, np.nan]
        ppm_maxs = [3.32, 3.3, 3.262, 3.236, 2.118, 2.089, 2.118, 0.7, 10.0, np.nan, np.nan]

    elif data_type == 'NMR':
        # Spectral data
        var_type = ['ppm'] * n_vars
        var_unit = ['ppm'] * n_vars
        descriptions = [f'NMR intensity at {v} ppm' for v in var_names]
        ppm_centers = [float(v) for v in var_names]
        ppm_mins = [np.nan] * n_vars
        ppm_maxs = [np.nan] * n_vars

    else:
        # Quantification data
        var_type = ['metabolite'] * n_vars
        var_unit = ['mM'] * n_vars
        descriptions = [f'Concentration of {v}' for v in var_names]
        ppm_centers = [np.nan] * n_vars
        ppm_mins = [np.nan] * n_vars
        ppm_maxs = [np.nan] * n_vars

    variables_df = pd.DataFrame({
        'var_id': var_ids,
        'var_name': var_names,
        'var_type': var_type,
        'var_unit': var_unit,
        'ppm_center': ppm_centers,
        'ppm_min': ppm_mins,
        'ppm_max': ppm_maxs,
        'description': descriptions
    })

    return variables_df.set_index('var_id')


def _generate_file_name(opts: Dict) -> str:
    """Generate base file name for parquet files."""
    parts = [
        opts['projectName'],
        opts['cohortName'],
        opts['sampleMatrixType'],
        opts['runName'],
        opts['method']
    ]
    # Filter out empty parts
    parts = [p for p in parts if p]

    if not parts:
        # Fallback to timestamp
        parts = [f"nmr_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"]

    return '_'.join(parts)


def _write_parquet_files(
    result: Dict[str, pd.DataFrame],
    base_name: str,
    output_dir: Path,
    log
):
    """Write all result DataFrames to parquet files."""
    written_files = []

    log.step("Writing parquet files", LogLevel.INFO)

    # Main files
    for key in ['data', 'metadata', 'params', 'variables']:
        if key in result:
            file_path = output_dir / f"{base_name}_{key}.parquet"
            result[key].to_parquet(file_path, compression='snappy', index=True)
            log.detail(f"Wrote: {file_path.name}")
            written_files.append((key, file_path))

    # Extra files (spcglyc regions)
    for key in ['tsp', 'spc_region', 'glyc_region']:
        if key in result:
            file_path = output_dir / f"{base_name}_{key}.parquet"
            result[key].to_parquet(file_path, compression='snappy', index=False)
            log.detail(f"Wrote: {file_path.name}")
            written_files.append((key, file_path))

    log.success(f"Wrote {len(written_files)} parquet files", LogLevel.PROD)

    # Create DuckDB database pointing to parquet files
    _create_duckdb_database(base_name, output_dir, written_files, log)


def _create_duckdb_database(
    base_name: str,
    output_dir: Path,
    written_files: List[Tuple[str, Path]],
    log
):
    """
    Create a DuckDB database with views to all parquet files.

    This allows easy SQL querying of the data:
    >>> import duckdb
    >>> con = duckdb.connect('run.duckdb')
    >>> con.sql('SELECT * FROM data LIMIT 10').df()
    """
    if not DUCKDB_AVAILABLE:
        log.warning("DuckDB not available. Skipping database creation.", LogLevel.INFO)
        log.detail("Install with: pip install duckdb")
        return

    db_path = output_dir / f"{base_name}.duckdb"

    try:
        log.step("Creating DuckDB database", LogLevel.INFO)

        # Create or connect to database
        con = duckdb.connect(str(db_path))

        # Create views for each parquet file
        for table_name, file_path in written_files:
            # Make table name SQL-friendly (replace hyphens with underscores)
            sql_table_name = table_name.replace('-', '_')

            # Create view pointing to parquet file
            con.execute(f"""
                CREATE OR REPLACE VIEW {sql_table_name} AS
                SELECT * FROM read_parquet('{file_path}')
            """)
            log.detail(f"Created view: {sql_table_name}")

        # Create a convenience view that joins data with metadata
        if any(name == 'data' for name, _ in written_files) and \
           any(name == 'metadata' for name, _ in written_files):
            con.execute("""
                CREATE OR REPLACE VIEW data_with_metadata AS
                SELECT d.*, m.*
                FROM data d
                LEFT JOIN metadata m USING (sample_key)
            """)
            log.detail("Created view: data_with_metadata")

        con.close()

        log.success(f"Created DuckDB database: {db_path.name}", LogLevel.PROD)
        log.info(f"Query with: duckdb.connect('{db_path.name}')")
        log.debug(f"Available views: {[name for name, _ in written_files] + ['data_with_metadata']}")

    except Exception as e:
        log.warning(f"Could not create DuckDB database: {e}")
