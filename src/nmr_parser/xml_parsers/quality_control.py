"""Functions for reading quality control data from Bruker XML files."""

from pathlib import Path
from typing import Union, Optional, Dict, Any
import pandas as pd
from lxml import etree
from rich.console import Console

from ..processing.utils import clean_names

console = Console()


def read_qc(file: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Read QC information for importation into database.

    Extracts quality control information from plasma_qc_report.xml or
    urine_qc_report.xml files.

    Parameters
    ----------
    file : str or Path
        Path to the QC report XML file

    Returns
    -------
    dict or None
        Dictionary with keys:
        - data: dict with 'infos', 'infoNames', 'tests', 'testNames'
        - version: QC report version string

        Returns None if file doesn't exist.

    Notes
    -----
    The QC file contains INFO elements describing sample conditions and
    PARAMETER elements with test results and reference ranges.

    Examples
    --------
    >>> qc = read_qc("experiment/pdata/1/plasma_qc_report.xml")
    >>> qc['version']
    'BioBankQC PS 1.0.0'
    >>> qc['data']['testNames']
    ['ph', 'lipaemia', ...]
    """
    file = Path(file)

    if not file.exists():
        console.print(f"[yellow]readQc >> {file} not found[/yellow]")
        return None

    try:
        tree = etree.parse(str(file), parser=etree.XMLParser(remove_blank_text=True))
        root = tree.getroot()

        # Get version from root element
        version = root.get("version", "")

        # Extract INFO elements
        info_elements = root.findall(".//INFO")
        info_names = []
        info_values = []
        info_refs = []
        info_comments = []

        for info in info_elements:
            name_raw = info.get("name", "")
            comment = info.get("value", "")

            # Extract applied value from name like "pH (Specified: 6.4 - 8, Applied: 7.6)"
            value = None
            ref = None

            if "Applied:" in name_raw.lower():
                parts = name_raw.lower().split("applied:")
                if len(parts) > 1:
                    value = parts[1].strip().rstrip(")")

            if "Specified:" in name_raw.lower():
                parts = name_raw.lower().split("specified:")
                if len(parts) > 1:
                    ref_part = parts[1].split(",")[0].strip()
                    ref = ref_part

            # Clean name (remove parentheses content)
            name = name_raw.split("(")[0].strip()
            clean_name = clean_names(name)

            info_names.append(name)
            info_values.append(value)
            info_refs.append(ref)
            info_comments.append(comment)

        infos = {
            'name': info_names,
            'comment': info_comments,
            'value': info_values,
            'ref': info_refs
        }

        # Extract PARAMETER elements (tests)
        test_elements = root.findall(".//PARAMETER")
        test_names = []
        test_comments = []
        test_types = []
        test_values = []
        test_units = []
        test_ref_maxs = []
        test_ref_mins = []

        for param in test_elements:
            name = param.get("name", "")
            comment = param.get("comment", "")
            param_type = param.get("type", "")

            # Clean test name
            clean_test_name = clean_names(name.split("(")[0].strip().lower())

            # Get VALUE element
            value_elem = param.find(".//VALUE")
            value = value_elem.get("value", "") if value_elem is not None else ""
            unit = value_elem.get("unit", "") if value_elem is not None else ""

            # Get REFERENCE element
            ref_elem = param.find(".//REFERENCE")
            ref_max = ref_elem.get("vmax", "") if ref_elem is not None else ""
            ref_min = ref_elem.get("vmin", "") if ref_elem is not None else ""

            # Clean value (handle \textless)
            value = value.replace("\\textless", "< ")

            test_names.append(name)
            test_comments.append(comment)
            test_types.append(param_type)
            test_values.append(value)
            test_units.append(unit)
            test_ref_maxs.append(ref_max)
            test_ref_mins.append(ref_min)

        tests = {
            'comment': test_comments,
            'name': test_names,
            'type': test_types,
            'value': test_values,
            'unit': test_units,
            'refMax': test_ref_maxs,
            'refMin': test_ref_mins
        }

        # Get cleaned test names
        test_names_clean = [clean_names(name.split("(")[0].strip().lower())
                           for name in test_names]

        # Get cleaned info names
        info_names_clean = [clean_names(name) for name in info_names]

        result = {
            'data': {
                'infos': infos,
                'infoNames': info_names_clean,
                'tests': tests,
                'testNames': test_names_clean
            },
            'version': version
        }

        return result

    except Exception as e:
        console.print(f"[red]readQc >> Error parsing {file}: {e}[/red]")
        return None
