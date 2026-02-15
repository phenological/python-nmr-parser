"""Functions for reading Bruker parameter files (acqus/procs)."""

import re
from pathlib import Path
from typing import Union, List, Optional
import pandas as pd
from rich.console import Console

from ..processing.utils import clean_names

console = Console()


def read_param(path: Union[str, Path], param_name: Union[str, List[str]]) -> Optional[Union[str, float, List]]:
    """
    Extract a parameter from a Bruker file (procs or acqus).

    Parameters
    ----------
    path : str or Path
        Path to the parameter file
    param_name : str or list of str
        Name(s) of the parameter(s) to read

    Returns
    -------
    str, float, list, or None
        The parameter value(s). Returns numeric if possible, string otherwise.
        Returns None if file or parameter not found.

    Examples
    --------
    >>> read_param("experiment/acqus", "PULPROG")
    'noesygppr1d'
    >>> read_param("experiment/acqus", ["BF1", "NS"])
    [600.27, 32]
    """
    path = Path(path)

    if not path.exists():
        console.print(f"[yellow]readParam file does not exist: {path}[/yellow]")
        return None

    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            txt = f.readlines()
    except Exception as e:
        console.print(f"[yellow]readParam error reading file: {path}[/yellow]")
        return None

    # Handle single parameter
    if isinstance(param_name, str):
        param_name = [param_name]

    # Search for each parameter
    parameters = []

    for pname in param_name:
        # Look for lines like ##$PARAMNAME= or ##PARAMNAME=
        pattern = f"{pname}="
        matching_lines = [i for i, line in enumerate(txt) if pattern in line]

        if not matching_lines:
            console.print(f"[yellow]readParam param {pname} not found in {path}[/yellow]")
            parameters.append(None)
            continue

        idx = matching_lines[0]
        line = txt[idx]

        # Extract value after '='
        if '=' in line:
            value = line.split('=', 1)[1].strip()

            # Handle angle brackets (string values)
            if '<' in value and '>' in value:
                # Remove angle brackets and spaces
                value = value.replace('<', '').replace('>', '').replace(' ', '')
                parameters.append(value)
            else:
                # Try to convert to numeric
                try:
                    if '.' in value or 'e' in value.lower():
                        parameters.append(float(value))
                    else:
                        parameters.append(int(value))
                except ValueError:
                    parameters.append(value)
        else:
            parameters.append(None)

    # Return single value if single parameter requested
    if len(parameters) == 1:
        return parameters[0]

    return parameters


def read_params(file: Union[str, Path]) -> Optional[pd.DataFrame]:
    """
    Extract all parameters from a Bruker parameter file (acqus/procs).

    Parses both xwin-nmr and TopSpin format parameter files, extracting
    parameter names, values, and metadata (date, time, instrument).

    Parameters
    ----------
    file : str or Path
        Path to the parameter file

    Returns
    -------
    pd.DataFrame or None
        DataFrame with columns: 'path', 'name', 'value'
        Returns None if file doesn't exist, is empty, or is AMIX format

    Notes
    -----
    Handles two timestamp formats:
    - XwinNMR: "YYYY-MM-DD HH:MM:SS TZ instrument"
    - TopSpin: "Mon Day DD HH:MM:SS YYYY TZ instrument"

    Supports vector parameters like "##$PARAM= (0..31)" followed by values.

    Examples
    --------
    >>> params = read_params("experiment/acqus")
    >>> params[params['name'] == 'PULPROG']['value'].values[0]
    'noesygppr1d'
    """
    file = Path(file)

    if not file.exists():
        console.print(f"[yellow]readParams >> {file} file not found[/yellow]")
        return None

    try:
        with open(file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        console.print(f"[yellow]readParams >> {file} error reading file[/yellow]")
        return None

    # Test if file is empty
    if not lines:
        console.print(f"[yellow]readParams >> {file} file is empty[/yellow]")
        return None

    # Test for AMIX files
    if lines[0].strip() == "A000":
        console.print(f"[yellow]readParams >> {file} file is AMIX[/yellow]")
        return None

    content = []
    counter = 0
    filename = file.name

    while counter < len(lines):
        line = lines[counter]

        if line.startswith("##END="):
            break

        # Get titles (##TITLE=)
        if re.match(r'^##[A-Z]', line):
            parts = line.split('= ', 1)
            if len(parts) == 2:
                param_name = parts[0].replace('##', '')
                value = parts[1].strip()

                # Clean value
                clean_value = value.replace('\t', ' ')
                clean_value = re.sub(r'\$\$', '', clean_value)
                clean_value = re.sub(r'\s+', ' ', clean_value)

                content.append({
                    'path': filename,
                    'name': param_name,
                    'value': clean_value
                })

        # Get audit info ($$)
        elif line.startswith('$$ '):
            param = line.replace('$$ ', '').strip()
            param = re.sub(r'\s+', ' ', param)

            date = time = timezone = instrument = dpath = None

            # XwinNMR format: YYYY-MM-DD HH:MM:SS TZ instrument
            if re.match(r'^\d{4}-\d{2}-\d{2}', param):
                parts = param.split(' ')
                if len(parts) >= 4:
                    date = parts[0]
                    time = parts[1]
                    timezone = parts[2]
                    instrument = clean_names(parts[3]) if len(parts) > 3 else None

            # TopSpin format: Mon Day DD HH:MM:SS YYYY TZ instrument
            elif re.match(r'^[A-Z][a-z]{2}\s+[A-Z][a-z]{2}\s+\d', param):
                param = re.sub(r'\s+', ' ', param)
                parts = param.split(' ')
                if len(parts) >= 8:
                    date = ' '.join(parts[0:3] + [parts[4]])  # Month Day DD YYYY
                    time = parts[3]
                    timezone = ' '.join(parts[5:7])
                    instrument = clean_names(parts[7]) if len(parts) > 7 else None

            # Data path
            elif re.match(r'^[A-Z]:', param) or param.startswith('/u'):
                dpath = param

            # Add metadata to content
            if all([date, time, timezone, instrument]):
                content.extend([
                    {'path': filename, 'name': 'instrumentDate', 'value': date},
                    {'path': filename, 'name': 'instrumentTime', 'value': time},
                    {'path': filename, 'name': 'instrumentTimeZone', 'value': timezone},
                    {'path': filename, 'name': 'instrument', 'value': instrument}
                ])

            if dpath:
                content.append({'path': filename, 'name': 'dpath', 'value': dpath})

        # Get parameters (##$)
        elif line.startswith('##$'):
            parts = line.split('= ', 1)
            if len(parts) == 2:
                param_name = parts[0].replace('##$', '')
                value = parts[1].strip()

                # Check for vectors like (0..31)
                if re.match(r'\(\d+\.\.\d+\)', value):
                    counter += 1
                    if counter < len(lines):
                        vector_line = lines[counter]
                        values = vector_line.split()
                        for i, v in enumerate(values):
                            content.append({
                                'path': filename,
                                'name': f'{param_name}_{i}',
                                'value': v
                            })
                else:
                    # Clean value
                    clean_value = value.replace('<', '').replace('>', '')
                    content.append({
                        'path': filename,
                        'name': param_name,
                        'value': clean_value
                    })

        counter += 1

    if not content:
        return None

    df = pd.DataFrame(content)

    # Replace empty values with None
    df['value'] = df['value'].replace('', None)

    return df
