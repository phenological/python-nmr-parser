"""Functions for reading quantification data from Bruker XML files."""

from pathlib import Path
from typing import Union, Optional, Dict, Any
import pandas as pd
from lxml import etree
from rich.console import Console

console = Console()


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
    """
    parameters = root.findall(".//PARAMETER")
    value_elems = root.findall(".//VALUE")
    value_relative_elems = root.findall(".//VALUERELATIVE")
    reldata_elems = root.findall(".//RELDATA")
    reference_elems = root.findall(".//REFERENCE")

    # Extract parameter names
    names = [p.get("name", "") for p in parameters]

    # Extract VALUE attributes
    conc_v = [v.get("conc", "") for v in value_elems]
    conc_unit_v = [v.get("concUnit", "") for v in value_elems]
    lod_v = [v.get("lod", "") for v in value_elems]
    lod_unit_v = [v.get("lodUnit", "") for v in value_elems]
    loq_v = [v.get("loq", "") for v in value_elems]
    loq_unit_v = [v.get("loqUnit", "") for v in value_elems]

    # Extract VALUERELATIVE attributes (prepend NA for first compound)
    conc_vr = [None] + [v.get("conc", "") for v in value_relative_elems]
    conc_unit_vr = [None] + [v.get("concUnit", "") for v in value_relative_elems]
    lod_vr = [None] + [v.get("lod", "") for v in value_relative_elems]
    lod_unit_vr = [None] + [v.get("lodUnit", "") for v in value_relative_elems]
    loq_vr = [None] + [v.get("loq", "") for v in value_relative_elems]
    loq_unit_vr = [None] + [v.get("loqUnit", "") for v in value_relative_elems]

    # Extract RELDATA attributes
    sig_corr_unit = [r.get("sigCorrUnit", "") for r in reldata_elems]
    sig_corr = [r.get("sigCorr", "") for r in reldata_elems]
    raw_conc_unit = [r.get("rawConcUnit", "") for r in reldata_elems]
    raw_conc = [r.get("rawConc", "") for r in reldata_elems]
    err_conc = [r.get("errConc", "") for r in reldata_elems]
    err_conc_unit = [r.get("errConcUnit", "") for r in reldata_elems]

    # Extract REFERENCE attributes
    ref_max = [r.get("vmax", "") for r in reference_elems]
    ref_min = [r.get("vmin", "") for r in reference_elems]
    ref_unit = [r.get("unit", "") for r in reference_elems]

    # Ensure all lists have the same length (pad if necessary)
    n = len(names)
    for lst in [conc_v, conc_unit_v, lod_v, lod_unit_v, loq_v, loq_unit_v,
                conc_vr, conc_unit_vr, lod_vr, lod_unit_vr, loq_vr, loq_unit_vr,
                sig_corr_unit, sig_corr, raw_conc_unit, raw_conc, err_conc, err_conc_unit,
                ref_max, ref_min, ref_unit]:
        while len(lst) < n:
            lst.append("")

    df = pd.DataFrame({
        'name': names,
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

    return df
