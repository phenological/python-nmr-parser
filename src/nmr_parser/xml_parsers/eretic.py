"""Functions for reading ERETIC calibration data from Bruker XML files."""

from pathlib import Path
from typing import Union, Optional
import pandas as pd
from lxml import etree
from rich.console import Console

console = Console()


def read_eretic(path: Union[str, Path]) -> Optional[pd.DataFrame]:
    """
    Extract ERETIC quantification information from a Bruker XML file.

    Reads QuantFactorSample.xml files to extract ERETIC calibration
    parameters for 600 MHz field strength.

    Parameters
    ----------
    path : str or Path
        Path to the QuantFactorSample.xml file

    Returns
    -------
    pd.DataFrame or None
        DataFrame with columns:
        - field: Magnetic field strength (600 MHz)
        - calEreticPosition: Calibration ERETIC position
        - calEreticLineWidth: Calibration ERETIC line width
        - calEreticConcentration: Calibration ERETIC concentration
        - calTubeID: Calibration tube ID
        - calTmin: Minimum temperature
        - calTmax: Maximum temperature
        - calP1: Calibration P1 value
        - calEreticCalibration: Calibration ERETIC factor
        - ereticFactor: Applied ERETIC factor
        - temperature: Application temperature
        - P1: Application P1 value

        Returns None if file doesn't exist.

    Examples
    --------
    >>> eretic = read_eretic("experiment/QuantFactorSample.xml")
    >>> eretic['ereticFactor'].iloc[0]
    3808.27187511
    """
    path = Path(path)

    if not path.exists():
        console.print(f"[yellow]readEretic >> {path} not found[/yellow]")
        return None

    try:
        tree = etree.parse(str(path), parser=etree.XMLParser(remove_blank_text=True))
        root = tree.getroot()

        # Extract values using XPath
        cal_eretic_position = float(root.findtext(".//Artificial_Eretic_Position", "0"))
        cal_eretic_line_width = float(root.findtext(".//Artificial_Eretic_Line_Width", "0"))
        cal_eretic_concentration = float(root.findtext(".//Artificial_Eretic_Concentration", "0"))

        # Get tube ID attribute
        tube_elem = root.find(".//Eretic_Sample_Tube")
        cal_tube_id = tube_elem.get("ID") if tube_elem is not None else None

        cal_tmin = float(root.findtext(".//Temperature_min", "0"))
        cal_tmax = float(root.findtext(".//Temperature_max", "0"))
        cal_p1 = float(root.findtext(".//Eretic_Calibration//P1", "0"))
        cal_eretic_calibration = float(root.findtext(".//Eretic_Calibration//Eretic_Factor", "0"))
        eretic_factor = float(root.findtext(".//Application_Parameter//Eretic_Factor", "0"))
        p1 = float(root.findtext(".//Application_Parameter//P1", "0"))
        temperature = float(root.findtext(".//Application_Parameter//Temperature", "0"))

        df = pd.DataFrame([{
            'field': 600,
            'calEreticPosition': cal_eretic_position,
            'calEreticLineWidth': cal_eretic_line_width,
            'calEreticConcentration': cal_eretic_concentration,
            'calTubeID': cal_tube_id,
            'calTmin': cal_tmin,
            'calTmax': cal_tmax,
            'calP1': cal_p1,
            'calEreticCalibration': cal_eretic_calibration,
            'ereticFactor': eretic_factor,
            'temperature': temperature,
            'P1': p1
        }])

        return df

    except Exception as e:
        console.print(f"[red]readEretic >> Error parsing {path}: {e}[/red]")
        return None


def read_eretic_f80(file: Union[str, Path]) -> Optional[pd.DataFrame]:
    """
    Extract ERETIC information from F80 (80 MHz) XML file.

    Reads eretic_file.xml files for 80 MHz field strength instruments.

    Parameters
    ----------
    file : str or Path
        Path to the eretic_file.xml

    Returns
    -------
    pd.DataFrame or None
        DataFrame with columns:
        - samOneMolInt: Sample one molecule intensity (ERETIC factor)
        - refOneMolInt: Reference one molecule intensity
        - samPreScanAttn: Sample pre-scan attenuation
        - refPreScanAttn: Reference pre-scan attenuation
        - samRG: Sample receiver gain
        - refRG: Reference receiver gain
        - samTemp: Sample temperature
        - refTemp: Reference temperature

        Returns None if file doesn't exist.

    Examples
    --------
    >>> eretic = read_eretic_f80("experiment/pdata/1/eretic_file.xml")
    >>> eretic['samOneMolInt'].iloc[0]
    1234.567
    """
    file = Path(file)

    if not file.exists():
        console.print(f"[yellow]readEreticF80 >> {file} not found[/yellow]")
        return None

    try:
        tree = etree.parse(str(file), parser=etree.XMLParser(remove_blank_text=True))
        root = tree.getroot()

        # Extract Sample section
        sam_one_mol_int = float(root.findtext(".//Sample//OneMolInt", "0"))
        sam_pre_scan_attn = float(root.findtext(".//Sample//PreScanAttn", "0"))
        sam_rg = float(root.findtext(".//Sample//RG", "0"))
        sam_temp = float(root.findtext(".//Sample//Temp", "0"))

        # Extract Reference section
        ref_one_mol_int = float(root.findtext(".//Reference//OneMolInt", "0"))
        ref_pre_scan_attn = float(root.findtext(".//Reference//PreScanAttn", "0"))
        ref_rg = float(root.findtext(".//Reference//RG", "0"))
        ref_temp = float(root.findtext(".//Reference//Temp", "0"))

        df = pd.DataFrame([{
            'samOneMolInt': sam_one_mol_int,
            'refOneMolInt': ref_one_mol_int,
            'samPreScanAttn': sam_pre_scan_attn,
            'refPreScanAttn': ref_pre_scan_attn,
            'samRG': sam_rg,
            'refRG': ref_rg,
            'samTemp': sam_temp,
            'refTemp': ref_temp
        }])

        return df

    except Exception as e:
        console.print(f"[red]readEreticF80 >> Error parsing {file}: {e}[/red]")
        return None
