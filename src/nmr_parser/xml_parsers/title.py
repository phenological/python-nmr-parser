"""Functions for reading title files from Bruker experiments."""

from pathlib import Path
from typing import Union, Optional, Dict
from rich.console import Console

console = Console()


def read_title(file: Union[str, Path]) -> Optional[Dict[str, str]]:
    """
    Extract title from a Bruker title file.

    Reads a title file and concatenates all non-empty lines into a single
    title string, preserving line breaks.

    Parameters
    ----------
    file : str or Path
        Path to the title file

    Returns
    -------
    dict or None
        Dictionary with keys 'path', 'name', 'value' where value contains
        the concatenated title. Returns None if file doesn't exist.

    Examples
    --------
    >>> title = read_title("experiment/pdata/1/title")
    >>> print(title['value'])
    'PROF_PLASMA_NOESY Plasma {...}'
    """
    file = Path(file)

    if not file.exists():
        console.print(f"[yellow]readTitle >> {file} not found[/yellow]")
        return None

    try:
        with open(file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        console.print(f"[yellow]readTitle >> {file} error reading file[/yellow]")
        return None

    # Extract non-empty lines and strip trailing whitespace
    content = []
    for line in lines:
        if line.strip():  # If line is not empty
            # Remove trailing whitespace
            line = line.rstrip()
            content.append(line)

    # Concatenate all lines with newline separator
    title_value = '\n'.join(content)

    return {
        'path': 'title',
        'name': 'title',
        'value': title_value
    }
