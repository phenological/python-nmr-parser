"""Functions for reading PACS data from Bruker XML files."""

from pathlib import Path
from typing import Union, Optional, Dict, Any
import pandas as pd
from lxml import etree
from rich.console import Console

console = Console()


def read_pacs(file: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Extract PACS information from a Bruker XML file.

    Reads plasma_pacs_report.xml files containing phenotypic risk
    assessment data.

    Parameters
    ----------
    file : str or Path
        Path to the PACS XML file

    Returns
    -------
    dict or None
        Dictionary with keys:

        - data : pd.DataFrame
            DataFrame with columns: name, conc_v, concUnit_v, refMax,
            refMin, refUnit
        - version : str
            Report version string

        Returns None if file doesn't exist.

    Examples
    --------
    >>> pacs = read_pacs("experiment/pdata/1/plasma_pacs_report.xml")
    >>> pacs['version']
    'PhenoRisk PACS RuO 1.0.0'
    >>> len(pacs['data'])
    16
    """
    file = Path(file)

    if not file.exists():
        console.print(f"[yellow]readPacs >> {file} not found[/yellow]")
        return None

    try:
        tree = etree.parse(str(file), parser=etree.XMLParser(remove_blank_text=True))
        root = tree.getroot()

        # Get version
        version_elem = root.find(".//QUANTIFICATION")
        version = version_elem.get("version", "") if version_elem is not None else ""

        # Extract parameter data
        parameters = root.findall(".//PARAMETER")

        names = []
        conc_vs = []
        conc_unit_vs = []
        ref_maxs = []
        ref_mins = []
        ref_units = []

        for param in parameters:
            name = param.get("name", "")

            # Get VALUE element (using PARAMETER/VALUE path)
            value_elem = param.find(".//VALUE")
            if value_elem is not None:
                conc_v = value_elem.get("conc", "")
                conc_unit_v = value_elem.get("concUnit", "")
            else:
                conc_v = ""
                conc_unit_v = ""

            # Get REFERENCE element (using PARAMETER/REFERENCE path)
            ref_elem = param.find(".//REFERENCE")
            if ref_elem is not None:
                ref_max = ref_elem.get("vmax", "")
                ref_min = ref_elem.get("vmin", "")
                ref_unit = ref_elem.get("unit", "")
            else:
                ref_max = ""
                ref_min = ""
                ref_unit = ""

            names.append(name)
            conc_vs.append(conc_v)
            conc_unit_vs.append(conc_unit_v)
            ref_maxs.append(ref_max)
            ref_mins.append(ref_min)
            ref_units.append(ref_unit)

        # Create DataFrame
        df = pd.DataFrame({
            'name': names,
            'conc_v': conc_vs,
            'concUnit_v': conc_unit_vs,
            'refMax': ref_maxs,
            'refMin': ref_mins,
            'refUnit': ref_units
        })

        result = {
            'data': df,
            'version': version
        }

        return result

    except Exception as e:
        console.print(f"[red]readPacs >> Error parsing {file}: {e}[/red]")
        return None
