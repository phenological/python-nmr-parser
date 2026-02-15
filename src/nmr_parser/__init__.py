"""
nmr-parser: Parse NMR IVDr data from Bruker instruments.

Python migration of the R nmr.parser package (v0.3.4).
"""

from .version import __version__, __r_version__

# Core functions
from .core import (
    read_experiment,
    read_spectrum,
    read_param,
    read_params,
    read_1r,
    scan_folder,
)

# XML parsers
from .xml_parsers import (
    read_qc,
    read_lipo,
    read_pacs,
    read_quant,
    read_eretic,
    read_eretic_f80,
    read_title,
)

# Processing utilities
from .processing import clean_names, extend_lipo, extend_lipo_value

# Reference tables
from .reference import (
    get_lipo_table,
    get_qc_table,
    get_pacs_table,
    get_sm_table,
)

__all__ = [
    # Version info
    '__version__',
    '__r_version__',

    # Main function
    'read_experiment',

    # Core I/O
    'read_spectrum',
    'read_param',
    'read_params',
    'read_1r',
    'scan_folder',

    # XML parsers
    'read_qc',
    'read_lipo',
    'read_pacs',
    'read_quant',
    'read_eretic',
    'read_eretic_f80',
    'read_title',

    # Processing
    'clean_names',
    'extend_lipo',
    'extend_lipo_value',

    # Reference tables
    'get_lipo_table',
    'get_qc_table',
    'get_pacs_table',
    'get_sm_table',
]
