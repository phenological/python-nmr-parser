"""XML parsing functions for Bruker NMR data files."""

from .eretic import read_eretic, read_eretic_f80
from .quality_control import read_qc
from .lipoproteins import read_lipo
from .pacs import read_pacs
from .quantification import read_quant
from .title import read_title

__all__ = [
    'read_eretic',
    'read_eretic_f80',
    'read_qc',
    'read_lipo',
    'read_pacs',
    'read_quant',
    'read_title',
]
