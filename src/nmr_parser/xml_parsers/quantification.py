"""Functions for reading quantification data from Bruker XML files."""

from pathlib import Path
from typing import Union, Optional, Dict, Any
import pandas as pd
from lxml import etree
from rich.console import Console

console = Console()

#: Column order of the returned frame, shared by both document shapes so an
#: empty report still has the same columns as a populated one.
QUANT_COLUMNS = [
    'name',
    'conc_v', 'concUnit_v', 'lod_v', 'lodUnit_v', 'loq_v', 'loqUnit_v',
    'conc_vr', 'concUnit_vr', 'lod_vr', 'lodUnit_vr', 'loq_vr', 'loqUnit_vr',
    'sigCorrUnit', 'sigCorr', 'rawConcUnit', 'rawConc', 'errConc', 'errConcUnit',
    'refMax', 'refMin', 'refUnit',
]



def read_quant(file: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Extract small molecules quantification information from a Bruker XML file.

    Handles multiple XML schema versions with automatic detection:
    - "_ver_" format: Uses 'valueext' attributes
    - "Quant" format: Uses 'conc' attributes with separate VALUERELATIVE nodes

    Parameters
    ----------
    file : str or Path
        Path to the quantification XML file (plasma or urine)

    Returns
    -------
    dict or None
        Dictionary with keys:

        - data : pd.DataFrame
            DataFrame with 22 columns including: name, conc_v, concUnit_v,
            lod_v, lodUnit_v, loq_v, loqUnit_v, conc_vr, concUnit_vr,
            lod_vr, lodUnit_vr, loq_vr, loqUnit_vr, sigCorrUnit, sigCorr,
            rawConcUnit, rawConc, errConc, errConcUnit, refMax, refMin, refUnit
        - version : str
            Quantification version string

        Returns None if file doesn't exist or version not recognized.

    Notes
    -----
    Priority order for finding files (used by readExperiment):
    1. plasma_quant_report_2_1_0.xml
    2. plasma_quant_report.xml
    3. urine_quant_report_e_1_2_0.xml
    4. urine_quant_report_e_ver_1_0.xml
    5. urine_quant_report_e.xml
    6. urine_quant_report_b_ver_1_0.xml
    7. urine_quant_report_b.xml
    8. urine_quant_report_ne_ver_1_0.xml
    9. urine_quant_report_ne.xml

    Examples
    --------
    >>> quant = read_quant("experiment/pdata/1/plasma_quant_report.xml")
    >>> quant['version']
    'Quant-PS 2.0.0'
    >>> len(quant['data'])
    41
    >>> quant['data']['name'].iloc[0]
    'Ethanol'
    """
    file = Path(file)

    if not file.exists():
        console.print(f"[yellow]readQuant >> {file} not found[/yellow]")
        return None

    try:
        tree = etree.parse(str(file), parser=etree.XMLParser(remove_blank_text=True))
        root = tree.getroot()

        # Get version
        version_elem = root.find(".//QUANTIFICATION")
        version = version_elem.get("version", "") if version_elem is not None else ""

        # Determine format based on filename or version
        file_str = str(file)
        is_ver_format = "_ver_" in file_str

        if is_ver_format:
            # Version 1 format: Uses valueext attribute
            data = _parse_quant_ver_format(root)
        elif "Quant" in version:
            # Version 2 format: Uses conc attribute
            data = _parse_quant_standard_format(root)
        else:
            console.print(f"[red]readQuant >> {file} version not recognized[/red]")
            return None

        result = {
            'data': data,
            'version': version
        }

        return result

    except Exception as e:
        console.print(f"[red]readQuant >> Error parsing {file}: {e}[/red]")
        return None


def _parse_quant_ver_format(root) -> pd.DataFrame:
    """
    Parse quantification data in _ver_ format.

    Uses 'valueext' attribute and handles different VALUE element structures.
    """
    parameters = root.findall(".//PARAMETER")

    records = []

    for param in parameters:
        name = param.get("name", "")

        # Get VALUE elements
        value_elems = param.findall(".//VALUE")

        # First VALUE element
        if len(value_elems) > 0:
            val1 = value_elems[0]
            conc_v = val1.get("valueext", "")
            conc_unit_v = val1.get("unit", "")
            lod_v = val1.get("lod", "")
            lod_unit_v = val1.get("unit", "")
            loq_v = val1.get("loq", "")
            loq_unit_v = val1.get("unit", "")
            raw_conc_unit = val1.get("unit", "")
            raw_conc = val1.get("valueext", "")
        else:
            conc_v = conc_unit_v = lod_v = lod_unit_v = loq_v = loq_unit_v = ""
            raw_conc_unit = raw_conc = ""

        # Second VALUE element (relative values)
        if len(value_elems) > 1:
            val2 = value_elems[1]
            conc_vr = val2.get("valueext", "")
            conc_unit_vr = val2.get("unit", "")
            lod_vr = val2.get("lod", "")
            lod_unit_vr = val2.get("unit", "")
            loq_vr = val2.get("loq", "")
            loq_unit_vr = val2.get("unit", "")
        else:
            conc_vr = conc_unit_vr = lod_vr = lod_unit_vr = loq_vr = loq_unit_vr = ""

        # Signal correction and error (not available in this format)
        sig_corr_unit = None
        sig_corr = None
        err_conc = None
        err_conc_unit = None

        # Get REFERENCE element (skip for Creatinine)
        if name != "Creatinine":
            ref_elems = param.findall(".//REFERENCE")
            if ref_elems:
                ref_max = ref_elems[0].get("vmax", "")
                ref_min = ref_elems[0].get("vmin", "")
                ref_unit = ref_elems[0].get("unit", "")
            else:
                ref_max = ref_min = ref_unit = ""
        else:
            ref_max = ref_min = ref_unit = ""

        records.append({
            'name': name,
            'conc_v': conc_v,
            'concUnit_v': conc_unit_v,
            'lod_v': lod_v,
            'lodUnit_v': lod_unit_v,
            'loq_v': loq_v,
            'loqUnit_v': loq_unit_v,
            'conc_vr': conc_vr,
            'concUnit_vr': conc_unit_vr,
            'lod_vr': lod_vr,
            'lodUnit_vr': lod_unit_vr,
            'loq_vr': loq_vr,
            'loqUnit_vr': loq_unit_vr,
            'sigCorrUnit': sig_corr_unit,
            'sigCorr': sig_corr,
            'rawConcUnit': raw_conc_unit,
            'rawConc': raw_conc,
            'errConc': err_conc,
            'errConcUnit': err_conc_unit,
            'refMax': ref_max,
            'refMin': ref_min,
            'refUnit': ref_unit
        })

    return pd.DataFrame(records)


def _parse_quant_standard_format(root) -> pd.DataFrame:
    """
    Parse quantification data in standard Quant format.

    Uses 'conc' attribute with separate VALUERELATIVE elements.

    Each PARAMETER carries its own VALUE, VALUERELATIVE, RELDATA and
    REFERENCE, so they are read from inside it. Sweeping the whole document
    once per attribute and zipping the lists together lines them up by
    position, which silently shifts every later compound onto its
    neighbour's numbers as soon as one parameter has fewer children. It also
    needed a hard coded pad at the front of the six _vr columns, correct
    only while the one parameter without a VALUERELATIVE is the first one.
    """
    records = []

    for param in root.findall(".//PARAMETER"):
        value = param.find("./VALUE")
        relative = param.find("./VALUERELATIVE")
        rel_data = param.find("./RELDATA")
        reference = param.find("./REFERENCE")

        def attr(elem, name):
            """Absent element or absent attribute both read as missing."""
            return None if elem is None else elem.get(name)

        records.append({
            'name': param.get("name", ""),
            'conc_v': attr(value, "conc"),
            'concUnit_v': attr(value, "concUnit"),
            'lod_v': attr(value, "lod"),
            'lodUnit_v': attr(value, "lodUnit"),
            'loq_v': attr(value, "loq"),
            'loqUnit_v': attr(value, "loqUnit"),
            'conc_vr': attr(relative, "conc"),
            'concUnit_vr': attr(relative, "concUnit"),
            'lod_vr': attr(relative, "lod"),
            'lodUnit_vr': attr(relative, "lodUnit"),
            'loq_vr': attr(relative, "loq"),
            'loqUnit_vr': attr(relative, "loqUnit"),
            'sigCorrUnit': attr(rel_data, "sigCorrUnit"),
            'sigCorr': attr(rel_data, "sigCorr"),
            'rawConcUnit': attr(rel_data, "rawConcUnit"),
            'rawConc': attr(rel_data, "rawConc"),
            'errConc': attr(rel_data, "errConc"),
            'errConcUnit': attr(rel_data, "errConcUnit"),
            'refMax': attr(reference, "vmax"),
            'refMin': attr(reference, "vmin"),
            'refUnit': attr(reference, "unit"),
        })

    return pd.DataFrame(records, columns=QUANT_COLUMNS)
