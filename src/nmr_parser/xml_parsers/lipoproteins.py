"""Functions for reading lipoprotein data from Bruker XML files."""

from pathlib import Path
from typing import Union, Optional, Dict, Any
import pandas as pd
from lxml import etree
from rich.console import Console

console = Console()


def _text_attr(elem, name):
    """Attribute as text, or None when the element or attribute is absent."""
    return None if elem is None else elem.get(name)


def _float_attr(elem, name):
    """Attribute as a float, or NaN when absent or not a number.

    Bruker writes "-" for a value it did not report, which float() rejects.
    """
    raw = _text_attr(elem, name)
    if raw is None:
        return float("nan")
    try:
        return float(raw)
    except ValueError:
        return float("nan")



def read_lipo(file: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Extract lipoprotein quantification information from a Bruker XML file.

    Reads lipo_results.xml or plasma_lipo_report.xml files containing
    lipoprotein profile data.

    Parameters
    ----------
    file : str or Path
        Path to the lipoprotein XML file

    Returns
    -------
    dict or None
        Dictionary with keys:

        - data : pd.DataFrame
            DataFrame with columns: fraction, name, abbr, id, type, value,
            unit, refMax, refMin, refUnit
        - version : str
            Report version string

        Returns None if file doesn't exist.

    Notes
    -----
    Duplicate IDs are removed, keeping only the first occurrence.

    Examples
    --------
    >>> lipo = read_lipo("experiment/pdata/1/lipo_results.xml")
    >>> lipo['version']
    'PL-5009-01/001'
    >>> lipo['data']['id'].tolist()
    ['TPTG', 'TPCH', 'HDCH', ...]
    """
    file = Path(file)

    if not file.exists():
        console.print(f"[yellow]readLipo >> {file} not found[/yellow]")
        return None

    try:
        tree = etree.parse(str(file), parser=etree.XMLParser(remove_blank_text=True))
        root = tree.getroot()

        # Get version
        version_elem = root.find(".//QUANTIFICATION")
        if version_elem is not None:
            version = version_elem.get("version", "")
            # Extract just the version identifier
            version = version.split()[0] if version else ""
        else:
            version = ""

        # Extract parameter data
        parameters = root.findall(".//PARAMETER")

        fractions = []
        names = []
        abbrs = []
        ids = []
        types = []
        values = []
        units = []
        ref_maxs = []
        ref_mins = []
        ref_units = []

        for param in parameters:
            comment = param.get("comment", "")
            param_id = param.get("name", "")
            param_type = param.get("type", "")

            # Parse comment: "fraction, name, abbreviation"
            comment_parts = comment.split(",")
            fraction = comment_parts[0].strip() if len(comment_parts) > 0 else ""
            name = comment_parts[1].strip() if len(comment_parts) > 1 else ""
            abbr = comment_parts[2].strip() if len(comment_parts) > 2 else ""

            # An absent element, an absent attribute or one Bruker wrote as
            # "-" all read as missing. Substituting 0.0 made "not reported"
            # indistinguishable from a measured zero, and a missing reference
            # became a range of 0 to 0, so every value looked out of range.
            value_elem = param.find("./VALUE")
            value = _float_attr(value_elem, "value")
            unit = _text_attr(value_elem, "unit")

            ref_elem = param.find("./REFERENCE")
            ref_max = _float_attr(ref_elem, "vmax")
            ref_min = _float_attr(ref_elem, "vmin")
            ref_unit = _text_attr(ref_elem, "unit")

            fractions.append(fraction)
            names.append(name)
            abbrs.append(abbr)
            ids.append(param_id)
            types.append(param_type)
            values.append(value)
            units.append(unit)
            ref_maxs.append(ref_max)
            ref_mins.append(ref_min)
            ref_units.append(ref_unit)

        # Create DataFrame
        df = pd.DataFrame({
            'fraction': fractions,
            'name': names,
            'abbr': abbrs,
            'id': ids,
            'type': types,
            'value': values,
            'unit': units,
            'refMax': ref_maxs,
            'refMin': ref_mins,
            'refUnit': ref_units
        })

        # Remove duplicates based on 'id', keeping first occurrence
        df = df[~df['id'].duplicated()].reset_index(drop=True)

        result = {
            'data': df,
            'version': version
        }

        return result

    except Exception as e:
        console.print(f"[red]readLipo >> Error parsing {file}: {e}[/red]")
        return None
